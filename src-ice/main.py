# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import _patch_all  # noqa

import logging
import traceback
import sys
import datetime
import time
import signal
import os

import Ice
import Ice_Process_ice  # noqa

import AppIce
from live_gateway_process_manager import LiveGatewayProcessManagerAsyncFactory
from nginx_process_manager import NginxProcessManagerAsyncFactory
from process_manager import ProcessAsyncInterface  # noqa

LOGGER = logging.getLogger(__name__)


class ProcessSrvI(AppIce.ProcessSrv):  # type: ignore
    pass


class OtherProcessManagerInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def clean(self):
        # type: () -> None
        pass

    @abstractmethod
    def init(self):
        # type: () -> None
        pass

    @abstractmethod
    def exit(self):
        # type: () -> None
        pass


class OtherProcessManagerImplement(OtherProcessManagerInterface):
    def __init__(self):
        # type: () -> None
        super(OtherProcessManagerImplement, self).__init__()
        self.proc_list = []  # type: List[ProcessAsyncInterface]
        self.init_proc_list()

    def init_proc_list(self):
        # type: () -> None
        self.proc_list.append(LiveGatewayProcessManagerAsyncFactory.make())
        self.proc_list.append(NginxProcessManagerAsyncFactory.make())

    def clean(self):
        # type: () -> None
        cmd1 = "kill -TERM $(ps -ef | grep '/distrib/LiveGateway/' | grep -v '/live-gateway-ice/live-gateway-ice' | grep -v grep | grep -v vim | awk '{print $2}')"  # noqa
        try:
            LOGGER.debug(cmd1)
            os.system(cmd1)
        except Exception:
            LOGGER.error(traceback.format_exc())
        time.sleep(1)

    def init(self):
        # type: () -> None
        LOGGER.debug('init other models')
        for proc in self.proc_list:
            proc.run()

    def exit(self):
        # type: () -> None
        for proc in self.proc_list:
            proc.exit()


class OtherProcessManagerFactory(object):
    @classmethod
    def make(cls):
        # type: () -> OtherProcessManagerInterface
        o = OtherProcessManagerImplement(
        )  # type: OtherProcessManagerInterface
        assert isinstance(o, OtherProcessManagerInterface)
        return o


class ProcessI(Ice.Process):  # type: ignore
    def __init__(  # type: ignore
            self, comm, adapter, other_process_manager):
        self._comm = comm
        self._adapter = adapter
        self.other_process_manager = \
            other_process_manager  # type: OtherProcessManagerInterface

    def shutdown(self, current=None):  # type: ignore
        LOGGER.debug('shutdown on process')
        self.other_process_manager.exit()

        if not self._comm.isShutdown():
            LOGGER.debug('shutdown communicator')
            self._comm.shutdown()

    def writeMessage(self, message, fd, current):  # type: ignore
        if fd == 1:
            sys.stdout.write(message)
        elif fd == 2:
            sys.stderr.write(message)


class Server(Ice.Application):  # type: ignore
    def __init__(self, *args, **kwargs):  # type: ignore
        super(Server, self).__init__(*args, **kwargs)
        self.other_process_manager = OtherProcessManagerFactory.make()

    def run(self, args):  # type: ignore
        def create_adpter():  # type: ignore
            comm = self.communicator()
            properties = comm.getProperties()
            adapter = comm.createObjectAdapter(
                properties.getProperty(b'AdapterIdentity'))
            adapter.add(
                ProcessSrvI(),
                comm.stringToIdentity(properties.getProperty(b'Identity')))
            return adapter

        adapter = create_adpter()  # type: ignore
        adapter.activate()

        try:
            self.other_process_manager.clean()
            self.other_process_manager.init()
        except Exception:
            LOGGER.error("[system]: %s" % (traceback.format_exc()))
            return 1

        self.callbackOnInterrupt()

        self.communicator().removeAdminFacet(b'Process')
        self._process = ProcessI(  # type: ignore
            self.communicator(), adapter, self.other_process_manager)
        self.communicator().addAdminFacet(self._process, b'Process')
        self.communicator().getAdmin()

        self.communicator().waitForShutdown()
        LOGGER.debug("ice_server shutdown...")

        if self.interrupted():
            LOGGER.info(self.appName() + ": terminating")
        return 0

    def shutdown(self, current=None):  # type: ignore
        LOGGER.debug("[system]: recv shutdown signal")
        current.adapter.getCommunicator().shutdown()

    def interruptCallback(self, sig):  # type: ignore
        LOGGER.debug("[system]: recv ice signal %s" % str(sig))
        if sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            os.system("kill -9 %d" % os.getpid())
            sys.exit(0)


def ice_server():
    # type: () -> int
    props = Ice.createProperties(sys.argv, None)

    props.setProperty(b"Ice.Trace.Network", b"0")
    props.setProperty(b"Ice.Trace.Protocol", b"0")
    props.setProperty(b"Ice.ACM.Client", b"0")
    props.setProperty(b'Ice.ThreadPool.Client.Serialize', b'1')
    props.setProperty(b'Ice.ThreadPool.Server.Serialize', b'1')
    props.setProperty(
        b'UpTime',
        datetime.datetime.strftime(datetime.datetime.now(),
                                   '%Y-%m-%d %H:%M:%S').encode())
    props.setProperty(b'Version', b'LiveGateway v0.0.0')
    props.setProperty(b'Ice.Default.EncodingVersion', b'1.0')

    initData = Ice.InitializationData()
    initData.properties = props
    initData.logger = logging.getLogger()

    app = Server(signalPolicy=Ice.Application.HandleSignals)  # type: ignore
    return app.main(sys.argv, None, initData)  # type: ignore


def main():
    # type: () -> None
    try:
        sys.exit(ice_server())
    except Exception:
        LOGGER.critical(traceback.format_exc())
        LOGGER.warning('will quit 90 s later')
        time.sleep(90)
        sys.exit(-1)


if __name__ == "__main__":
    main()
