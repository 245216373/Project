# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from typing import Optional  # noqa
from pykka import ActorProxy

import logging
import os

from process_manager import (  # noqa
    ProcessAsyncInterface, ProcessTemplateAsyncInterface)

LOGGER = logging.getLogger(__name__)


class NginxProcessManagerAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> ProcessAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = NginxProcessManagerAsyncImplement().start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


class NginxProcessManagerAsyncImplement(ProcessTemplateAsyncInterface):
    def __init__(self):
        # type: () -> None
        super(NginxProcessManagerAsyncImplement, self).__init__()
        self.fix_run_args()

    @property
    def name(self):
        # type: () -> str
        return 'nginx'

    @property
    def run_path(self):
        # type: () -> str
        a = os.getcwd() + '/../nginx/nginx'
        b = os.path.abspath(a)
        return b

    @property
    def path(self):
        # type: () -> str
        return os.path.dirname(self.run_path)

    @property
    def run_args(self):
        # type: () -> str
        return '-c %s/nginx.conf -p %s' % (self.path, self.path)

    def fix_run_args(self):
        # type: () -> None
        a1 = self.path + '/logs'
        if not os.path.exists(a1):
            os.mkdir(a1)
