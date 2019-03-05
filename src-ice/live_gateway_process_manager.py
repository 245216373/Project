# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from pykka import ActorProxy

import logging
import os

from process_manager import (  # noqa
    ProcessAsyncInterface, ProcessTemplateAsyncInterface)

LOGGER = logging.getLogger(__name__)


class LiveGatewayProcessManagerAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> ProcessAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = LiveGatewayProcessManagerAsyncImplement().start(
            ).proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


class LiveGatewayProcessManagerAsyncImplement(ProcessTemplateAsyncInterface):
    def __init__(self):
        # type: () -> None
        super(LiveGatewayProcessManagerAsyncImplement, self).__init__()

    @property
    def name(self):
        # type: () -> str
        return 'live-gateway'

    @property
    def run_path(self):
        # type: () -> str
        a = os.getcwd() + '/../live-gateway/live-gateway'
        b = os.path.abspath(a)
        return b

    @property
    def run_args(self):
        # type: () -> str
        return '--config=/opt/cloudroom/var/lib/crproj/LiveGateway/config.conf'
