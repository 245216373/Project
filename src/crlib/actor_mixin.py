# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from typing import cast

import time
from threading import Thread, Event, RLock
import logging
import traceback

LOGGER = logging.getLogger(__name__)


class ActorScheduleMixin(object):
    def __new__(cls, *args, **kwargs):  # type: ignore
        o = super(ActorScheduleMixin, cls).__new__(cls)
        o._ActorScheduleMixin__tasks_lock = RLock()
        o._ActorScheduleMixin__tasks = {}  # t: {"schedule_stopped": Event()}
        return o

    def __actor_schedule_mixin_get_func(self, func_name):  # type: ignore
        try:
            func = getattr(self.actor_ref.proxy(), func_name)
        except AttributeError:
            raise AttributeError("self.%s is not exists" % (func_name, ))
        return func

    def __actor_schedule_is_valid(self, t):
        # type: (Thread) -> bool
        if self.actor_stopped.is_set():  # type: ignore
            return False
        with self.__tasks_lock:  # type: ignore
            if t not in self.__tasks:  # type: ignore
                return False
            task = self.__tasks[t]  # type: ignore
            if task["schedule_stopped"].is_set():
                return False
        return True

    def __actor_schedule_sleep_success(  # type: ignore
            self, t, delay, min_delay):  # type: ignore
        if min_delay is None:
            min_delay = delay

        if delay > min_delay:
            i = 0
            while i < delay:
                i += min_delay
                time.sleep(min_delay)
                if not self.__actor_schedule_is_valid(t):
                    return False
        else:
            time.sleep(delay)
        return self.__actor_schedule_is_valid(t)

    def __actor_schedule_add_thread(self, target, name):  # type: ignore
        t = Thread(target=target, name=name)
        t.setDaemon(True)
        with self.__tasks_lock:
            self.__tasks[t] = {"schedule_stopped": Event()}
        return t

    def _actor_schedule_once(
            self,
            func_name,  # type: str
            func_args=(),  # type: Any
            func_kwargs=None,  # type: Any
            delay=0,  # type: float
            min_delay=0.005,  # type: Union[None, float]
    ):
        # type: (...) -> Thread
        if func_kwargs is None:
            func_kwargs = {}
        func = self.__actor_schedule_mixin_get_func(func_name)  # type: ignore

        def _run():
            # type: () -> None
            try:
                if self.__actor_schedule_sleep_success(  # type: ignore
                        t, delay, min_delay):  # type: ignore
                    func(*func_args, **func_kwargs)
            except Exception:
                LOGGER.error(traceback.format_exc())
            finally:
                self._actor_schedule_cancel(t)

        t = self.__actor_schedule_add_thread(  # type: ignore
            _run, "actor_schedule_mixin_schedule_once")
        t.start()
        return cast(Thread, t)

    def _actor_schedule_forever(
            self,
            func_name,  # type: str
            func_args=(),  # type: Any
            func_kwargs=None,  # type: Any
            delay=1,  # type: float
            min_delay=0.005,  # type: Union[None, float]
            is_at_once=False,  # type: bool
    ):
        # type: (...) -> Thread
        if func_kwargs is None:
            func_kwargs = {}
        func = self.__actor_schedule_mixin_get_func(func_name)  # type: ignore

        def _run():  # type: ignore
            try:
                if is_at_once and self.__actor_schedule_is_valid(t):
                    func(*func_args, **func_kwargs)
                while self.__actor_schedule_is_valid(t):
                    if self.__actor_schedule_sleep_success(
                            t, delay, min_delay):
                        func(*func_args, **func_kwargs)
            finally:
                self._actor_schedule_cancel(t)

        t = self.__actor_schedule_add_thread(
            _run, "actor_schedule_mixin_schedule_forever")
        t.start()
        return t

    def _actor_schedule_cancel(self, t):
        # type: (Thread) -> None
        with self.__tasks_lock:  # type: ignore
            if t in self.__tasks:  # type: ignore
                task = self.__tasks.pop(t)  # type: ignore
                task["schedule_stopped"].set()

    def _actor_schedule_is_valid(self, t):
        # type: (Optional[Thread]) -> bool
        if t is None:
            return False

        return self.__actor_schedule_is_valid(t)
