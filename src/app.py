# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import logging
import traceback
import sys
import signal
from functools import partial

import gevent
from pykka import ThreadingActor, ActorProxy

from web_server import WebServerAsyncFactory

LOGGER = logging.getLogger(__name__)


def _exit(sig_name, *args, **kwargs):
    # type: (str, Any, Any) -> None
    try:
        LOGGER.warning('recv sig %s' % (sig_name, ))
        if sig_name in ('SIGQUIT', 'SIGTERM'):
            try:
                gevent.kill(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                sys.exit()
        elif sig_name == 'SIGINT':
            sys.exit()
        elif sig_name == 'SIGHUP':
            sys.exit()  # TODO: 软重启
    except Exception:
        LOGGER.error(traceback.format_exc())


def _bind_signal():
    # type: () -> None
    LOGGER.debug('bind gevent signal')
    gevent.signal(signal.SIGHUP, partial(_exit, "SIGHUP"))
    gevent.signal(signal.SIGINT, partial(_exit, "SIGINT"))
    gevent.signal(signal.SIGTERM, partial(_exit, "SIGTERM"))
    gevent.signal(signal.SIGQUIT, partial(_exit, "SIGQUIT"))


class AppAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self):  # type: () -> None
        pass

    @property
    @abstractmethod
    def monitor_info(self):
        # type: () -> Dict[str, dict]
        pass


class AppAsyncImplement(
        ThreadingActor,  # type: ignore
        AppAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(AppAsyncImplement, self).__init__()
        self.web_server = WebServerAsyncFactory.make()

    @property
    def monitor_info(self):
        # type: () -> Dict[str, dict]
        return self.web_server.monitor_info.get()  # type: ignore

    def run(self):
        # type: () -> None
        LOGGER.info('app run')
        _bind_signal()
        self.web_server.run()


class AppAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> AppAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = AppAsyncImplement().start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore
