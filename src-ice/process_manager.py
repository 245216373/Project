# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from pykka import ThreadingActor

import os
import traceback
import logging
from subprocess import Popen
from threading import Thread
import time

from crlib.env import env
from crlib.actor_mixin import ActorScheduleMixin

LOGGER = logging.getLogger(__name__)


class ProcessAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_running(self):
        # type: () -> False
        pass

    @abstractmethod
    def run(self):
        # type: () -> None
        pass

    @abstractmethod
    def exit(self):
        # type: () -> None
        pass


class ProcessTemplateAsyncInterface(
        ThreadingActor,  # type: ignore
        ActorScheduleMixin,
        ProcessAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(ProcessTemplateAsyncInterface, self).__init__()
        self.pm = ProcessManagerFactory.make(self.name, self.run_path,
                                             self.run_args)
        self.hand = None  # type: Optional[Thread]
        self._schedule_process_run_again = None  # type: Optional[Thread]

    @property
    @abstractmethod
    def name(self):
        # type: () -> str
        pass

    @property
    @abstractmethod
    def run_path(self):
        # type: () -> str
        pass

    @property
    @abstractmethod
    def run_args(self):
        # type: () -> str
        pass

    @property
    def path(self):
        # type: () -> str
        return os.path.dirname(self.run_path)

    @property
    def run_again_time(self):
        # type: () -> int
        return 30

    def on_run_exit(self):
        # type: () -> None
        LOGGER.debug(
            'process %s recv thread exit notify, schedule run again after %ss'
            % (self.name, self.run_again_time))
        self.hand = None
        self._schedule_process_run_again = self._actor_schedule_once(
            "process_run_again", delay=self.run_again_time)

    def process_run_again(self):
        # type: () -> None
        if not self._actor_schedule_is_valid(self._schedule_process_run_again):
            return
        self.run()

    def is_running(self):
        # type: () -> False
        return self.hand is not None

    def run(self):
        # type: () -> None
        LOGGER.debug('start new thread run %s' % (self.name, ))
        self.hand = Thread(
            target=self.pm.run, args=(self.actor_ref.proxy().on_run_exit, ))
        self.hand.setDaemon(True)
        self.hand.start()

    def exit(self):
        # type: () -> None
        self.pm.exit()


class ProcessManagerInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, on_exit):
        # type: (Callable) -> None
        pass

    @abstractmethod
    def exit(self):
        # type: () -> None
        pass


class ProcessManagerImplement(ProcessManagerInterface):
    def __init__(self, server_name, path, args):
        # type: (str, str, str) -> None
        super(ProcessManagerImplement, self).__init__()
        self._pid = None  # type: Optional[int]
        self.server_name = server_name
        self.path = path
        self.args = args

    @property
    def pid(self):
        # type: () -> Optional[int]
        return self._pid

    @pid.setter
    def pid(self, pid):
        # type: (int) -> None
        self._pid = pid

    @property
    def cmd(self):
        # type: () -> List[str]
        cmd = self.path + ' ' + self.args
        return cmd.split(' ')

    def run(self, on_exit):
        # type: (Callable) -> None
        try:
            LOGGER.debug('run process %s' % (self.server_name, ))
            if self.pid is not None:
                LOGGER.error(
                    'process %s have been running' % (self.server_name, ))
                return
            LOGGER.info(
                'run process %s cmd is: %s' % (self.server_name, self.cmd))
            sub_env = env.to_dict()
            sub_env['LD_LIBRARY_PATH'] = os.path.dirname(self.path) + '/lib'
            LOGGER.debug("start process env is: %s" % sub_env)

            p = Popen(self.cmd, env=sub_env)
            self._pid = p.pid

            out, err = p.communicate()
            exit_code = p.poll()
            LOGGER.warn('process %s exit out:%s err:%s exit_code:%s' %
                        (self.server_name, out, err, exit_code))
        except Exception:
            LOGGER.debug("process %s exit %s env is: %s" % (self.server_name,
                                                            self.cmd, sub_env))
            LOGGER.error(traceback.format_exc())
        finally:
            self._pid = None
            on_exit()

    def exit(self):
        # type: () -> None
        if self._pid is not None:
            try:
                os.system("kill -TERM %s" % self._pid)
                time.sleep(0.1)
            except Exception:
                pass


class ProcessManagerFactory(object):
    @classmethod
    def make(cls, server_name, path, args):
        # type: (str, str, str) -> ProcessManagerInterface
        o = ProcessManagerImplement(server_name, path,
                                    args)  # type: ProcessManagerInterface
        assert isinstance(o, ProcessManagerInterface)
        return o
