# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import logging
import os
from threading import Thread

from pykka import ThreadingActor, ActorProxy, ThreadingFuture  # noqa

from storage import storage

LOGGER = logging.getLogger(__name__)


class UploadFileCompleterAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def submit_task(
            self,
            task_id,  # type: str
            target_filename,  # type: str
            target_file_path,  # type: str
            upload_path,  # type: str
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> ThreadingFuture
        pass


class UploadFileCompleterAsyncImplement(
        ThreadingActor,  # type: ignore
        UploadFileCompleterAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(UploadFileCompleterAsyncImplement, self).__init__()

    def submit_task(
            self,
            task_id,  # type: str
            target_filename,  # type: str
            target_file_path,  # type: str
            upload_path,  # type: str
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> None
        def complete():
            # type: () -> None
            LOGGER.debug(
                'complete %s %s %s %s' % (task_id, target_filename,
                                          target_file_path, upload_path))
            chunk = 0
            with open(target_file_path, 'wb') as target_file:
                while True:
                    try:
                        filename = '%s/%s%d' % (upload_path, task_id, chunk)
                        LOGGER.debug('Merge file %s' % (filename))
                        source_file = open(filename, 'rb')
                        target_file.write(source_file.read())
                        source_file.close()
                    except IOError:
                        break
                    chunk += 1
                    os.remove(filename)

            storage.move_upload_file(target_file_path,
                                     target_filename).get(timeout=600)
            LOGGER.debug('%s to %s' % (target_file_path, target_filename))
            LOGGER.debug('%s complete finished, callback' % (task_id, ))
            callback_ok()

        t = Thread(target=complete)
        t.setDaemon(True)
        t.start()


class UploadFileCompleterAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> UploadFileCompleterAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = UploadFileCompleterAsyncImplement.start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


upload_file_completer = UploadFileCompleterAsyncFactory.make()
