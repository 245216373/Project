# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from typing import cast
import logging
from threading import Thread
import traceback

from pykka import ThreadingActor, ActorProxy
from gevent.pywsgi import WSGIServer

from crlib.env import env

from flask_app_public import app_public
from flask_app_nginx_rtmp import app_nginx_rtmp

LOGGER = logging.getLogger(__name__)


class WSGIServerRunnerInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_running(self):
        # type: () -> bool
        pass

    @abstractmethod
    def run(self):
        # type: () -> None
        pass


class WSGIServerRunnerImplement(WSGIServerRunnerInterface):
    def __init__(self, server, server_name):
        # type: (WSGIServer, str) -> None
        super(WSGIServerRunnerImplement, self).__init__()
        self._hand = None  # type: Optional[Thread]
        self.server = server
        self.server_name = server_name

    @property
    def hand(self):
        # type: () -> Optional[Thread]
        return self._hand

    @hand.setter
    def hand(self, hand):
        # type: (Thread) -> None
        self._hand = hand

    def is_running(self):
        # type: () -> bool
        return self.hand is not None

    def server_forever(self):
        # type: () -> None
        try:
            self.server.serve_forever()
        except Exception:
            self.hand = None
            LOGGER.error(traceback.format_exc())

    def run(self):
        # type: () -> None
        if self.hand is None:
            LOGGER.info('run web server %s' % (self.server_name, ))
            self.hand = Thread(target=self.server_forever)
            self.hand.setDaemon(True)
            self.hand.start()
        else:
            LOGGER.error(
                'web server %s have been running' % (self.server_name, ))


class WSGIServerRunnerFactory(object):
    @classmethod
    def make(cls, server, server_name):
        # type: (WSGIServer, str) -> WSGIServerRunnerInterface
        o = WSGIServerRunnerImplement(
            server, server_name)  # type: WSGIServerRunnerInterface
        assert isinstance(o, WSGIServerRunnerInterface)
        return o


class WebServerAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self):
        # type: () -> None
        pass

    @property
    @abstractmethod
    def monitor_info(self):
        # type: () -> Dict[str, Any]
        pass


class WebServerAsyncImplement(
        ThreadingActor,  # type: ignore
        WebServerAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(WebServerAsyncImplement, self).__init__()
        self.app_nginx_rtmp_server_runner = WSGIServerRunnerFactory.make(
            WSGIServer(('', self.APP_WEB_SERVER_NGINX_RTMP_PORT),
                       app_nginx_rtmp), 'nginx_rtmp')
        self.app_public_server_runner = WSGIServerRunnerFactory.make(
            WSGIServer(('', self.APP_WEB_SERVER_PUBLIC_PORT), app_public),
            'public')

    @property
    def monitor_info(self):
        # type: () -> Dict[str, Any]
        r = {
            'nginx_rtmp_server': {
                'is_running': self.app_nginx_rtmp_server_runner.is_running(),
            },
            'public_server': {
                'is_running': self.app_public_server_runner.is_running(),
            },
        }
        return r

    @property
    def APP_WEB_SERVER_NGINX_RTMP_IP(self):
        # type: () -> str
        return cast(str, env.get('APP_WEB_SERVER_NGINX_RTMP_IP'))

    @property
    def APP_WEB_SERVER_NGINX_RTMP_PORT(self):
        # type: () -> int
        return cast(int, env.get('APP_WEB_SERVER_NGINX_RTMP_PORT', type_=int))

    @property
    def APP_WEB_SERVER_PUBLIC_IP(self):
        # type: () -> str
        return cast(str, env.get('APP_WEB_SERVER_PUBLIC_IP'))

    @property
    def APP_WEB_SERVER_PUBLIC_PORT(self):
        # type: () -> int
        return cast(int, env.get('APP_WEB_SERVER_PUBLIC_PORT', type_=int))

    def run(self):
        # type: () -> None
        if not self.app_nginx_rtmp_server_runner.is_running():
            self.app_nginx_rtmp_server_runner.run()
        if not self.app_public_server_runner.is_running():
            self.app_public_server_runner.run()


class WebServerAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> WebServerAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = WebServerAsyncImplement().start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore
