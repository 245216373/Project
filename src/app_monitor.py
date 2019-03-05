# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import logging
from threading import Thread  # noqa

from pykka import ThreadingActor, ActorProxy

from crlib.actor_mixin import ActorScheduleMixin

from app import AppAsyncInterface  # noqa
from cut import clear_timeout_sharding

LOGGER = logging.getLogger(__name__)


class AppMonitorAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self):
        # type: () -> None
        pass


class AppMonitorAsyncImplement(
        ThreadingActor,  # type: ignore
        ActorScheduleMixin,
        AppMonitorAsyncInterface):
    use_daemon_thread = True

    def __init__(self, app):
        # type: (AppAsyncInterface) -> None
        super(AppMonitorAsyncImplement, self).__init__()
        self._schedule_check = None  # type: Optional[Thread]
        self.app = app

    def check(self):
        # type: () -> None
        if self._schedule_check is None:
            LOGGER.debug('schedul canceled, check function exit')
            return
        info = self.app.monitor_info.get()  # type: ignore
        LOGGER.info('monitor info: %s' % (info, ))
        clear_timeout_sharding()

    def run(self):
        # type: () -> None
        if self._schedule_check is None:
            self._schedule_check = self._actor_schedule_forever(
                "check", delay=120, min_delay=None)


class AppMonitorAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls, app):
        # type: (AppAsyncInterface) -> AppMonitorAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = AppMonitorAsyncImplement(app).start(app).proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore
