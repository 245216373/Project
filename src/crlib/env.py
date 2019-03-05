# -*- coding: utf-8 -*
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import os

from threading import Lock

from six import string_types, integer_types


class EnvInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_inited(self):
        # type: () -> bool
        pass

    @abstractmethod
    def get(self, name, default=None, type_=None):
        # type: (str, Optional[Any], Optional[Type]) -> Any
        pass

    @abstractmethod
    def set(self, name, value):
        # type: (str, Any) -> None
        pass

    @abstractmethod
    def init(self, env_file=None):
        # type: (Optional[str]) -> None
        pass

    @abstractmethod
    def to_dict(self):
        # type: () -> Dict[str, str]
        pass


class EnvFactory(object):
    @classmethod
    def make(cls):
        # type: () -> EnvInterface
        o = EnvImplement()  # type: EnvInterface
        assert isinstance(o, EnvInterface)
        return o


class EnvImplement(EnvInterface):
    def __init__(self):  # type: () -> None
        super(EnvImplement, self).__init__()
        self.lock = Lock()
        self.envs = {}  # type: Dict[str, Any]
        self._is_inited = False

    def is_inited(self):
        # type: () -> bool
        return self._is_inited

    def get(self, name, default=None, type_=None):
        # type: (str, Optional[Any], Optional[Type]) -> Any
        self.lock.acquire()
        try:
            value = self.envs.get(name, default)
            if value is None or type_ is None:
                return value
            if type_ is bool:
                if isinstance(value, string_types):
                    value = value.upper() in ('TRUE', b'TRUE')
                else:
                    value = bool(value)
            elif type_ in integer_types:
                value = int(value)
            else:
                value = type_(value)
            return value
        finally:
            self.lock.release()

    def set(self, name, value):
        # type: (str, Any) -> None
        self.lock.acquire()
        try:
            self.envs[name] = value
        finally:
            self.lock.release()

    def init(self, env_file=None):
        # type: (Optional[str]) -> None
        self.lock.acquire()
        try:
            self._is_inited = True
            for k, v in os.environ.items():
                self.envs[k] = v

            if env_file:
                with open(env_file) as f:
                    lines = f.readlines()

                for line in lines:
                    if not line:
                        continue
                    if line[0] == '#':
                        continue
                    line_list = line.split('=')
                    if len(line_list) < 2:
                        continue
                    name, value = line_list[0], '='.join(line_list[1:])[:-1]
                    self.envs[name.strip()] = value
        finally:
            self.lock.release()

    def to_dict(self):
        # type: () -> Dict[str, str]
        result = {}
        for k, v in self.envs.items():
            result[k] = str(v)
        return result


env = EnvFactory.make()
