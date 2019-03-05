# -*- coding: utf-8 -*-
"""提供对录像文件的数据中心存储位置支持"""
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import os
import shutil
import logging

from pykka import ThreadingActor, ActorProxy, ThreadingFuture  # noqa

from crlib.env import env

LOGGER = logging.getLogger(__name__)


# XXX: 要修改长时间执行任务为线程执行并回调的模式
class StorageAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def move_upload_file(self, src, filename):
        # type: (str, str) -> ThreadingFuture
        pass

    @abstractmethod
    def get_upload_file(self, filename, dst):
        # type: (str, str) -> ThreadingFuture
        pass

    @abstractmethod
    def delete_upload_file(self, filename):
        # type: (str) -> ThreadingFuture
        pass

    @abstractmethod
    def copy_vod_file(self, src):
        # type: (str) -> ThreadingFuture
        pass

    @abstractmethod
    def copy_vod_dir(self, src):
        # type: (str) -> ThreadingFuture
        pass

    @abstractmethod
    def get_vod_dir(self, dirname, dst_path):
        # type: (str, str) -> ThreadingFuture
        pass

    @abstractmethod
    def delete_vod_dir(self, dirname):
        # type: (str) -> ThreadingFuture
        pass

    @abstractmethod
    def get_vod_file(self, filename, dst_path):
        # type: (str, str) -> ThreadingFuture
        pass

    @abstractmethod
    def delete_vod_file(self, filename):
        # type: (str) -> ThreadingFuture
        pass

    @abstractmethod
    def is_vod_dir_exists(self, dirname):
        # type: (str) -> ThreadingFuture
        pass

    @abstractmethod
    def is_vod_file_exists(self, filename):
        # type: (str) -> ThreadingFuture
        pass


class StorageNASAsyncImplement(
        ThreadingActor,  # type: ignore
        StorageAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(StorageNASAsyncImplement, self).__init__()
        self.check_root_path()

    def check_root_path(self):
        # type: () -> None
        path = self.APP_STORAGE_NAS_ROOT_PATH
        if not path or not os.path.exists(path):
            raise ValueError('path invalid: %s' % (path, ))

    def move_upload_file(self, src, filename):
        # type: (str, str) -> None
        if not os.path.exists(self.UPLOAD_PATH):
            os.mkdir(self.UPLOAD_PATH)
            LOGGER.debug('create file %s' % self.UPLOAD_PATH)
        dst = self.UPLOAD_PATH + '/' + filename
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
        LOGGER.debug('%s to %s' % (src, dst))

    def get_upload_file(self, filename, dst):
        # type: (str, str) -> None
        dst_file = dst + '/' + filename
        if os.path.exists(dst_file):
            os.remove(dst_file)
        shutil.copy(self.UPLOAD_PATH + '/' + filename, dst)

    def delete_upload_file(self, filename):
        # type: (str) -> None
        dst = self.UPLOAD_PATH + '/' + filename
        local_path = self.upload_path + '/' + filename
        if os.path.exists(dst):
            os.remove(dst)
        if os.path.exists(local_path):  # 添加删除本地上传文件
            os.remove(local_path)

    def copy_vod_file(self, src):
        # type: (str) -> None
        if not os.path.exists(self.VOD_PATH):
            os.mkdir(self.VOD_PATH)
        dst = self.VOD_PATH + '/' + os.path.basename(src)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, dst)

    def copy_vod_dir(self, src):
        # type: (str) -> None
        if not os.path.exists(self.VOD_PATH):
            os.mkdir(self.VOD_PATH)
        dst = self.VOD_PATH + '/' + os.path.basename(src)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def get_vod_dir(self, dirname, dst_path):
        # type: (str, str) -> None
        if os.path.exists(dst_path):
            return
        src = self.VOD_PATH + '/' + dirname
        shutil.copytree(src, dst_path)

    def delete_vod_dir(self, dirname):
        # type: (str) -> None
        dir_path = self.VOD_PATH + '/' + dirname
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    def get_vod_file(self, filename, dst_path):
        # type: (str, str) -> None
        if os.path.exists(dst_path):
            return
        src = self.VOD_PATH + '/' + filename
        shutil.copy(src, dst_path)

    def delete_vod_file(self, filename):
        # type: (str) -> None
        file_path = self.VOD_PATH + '/' + filename
        if os.path.exists(file_path):
            os.remove(file_path)

    def is_vod_dir_exists(self, dirname):
        # type: (str) -> bool
        dir_path = self.VOD_PATH + '/' + dirname
        return os.path.exists(dir_path)

    def is_vod_file_exists(self, filename):
        # type: (str) -> bool
        file_path = self.VOD_PATH + '/' + filename
        return os.path.exists(file_path)

    @property
    def UPLOAD_PATH(self):
        # type: () -> str
        return self.APP_STORAGE_NAS_ROOT_PATH + '/upload'


    @property
    def upload_path(self):
        # type: () -> str
        return self.APP_UPLOAD_ROOT_PATH + '/upload'

    @property
    def VOD_PATH(self):
        # type: () -> str
        return self.APP_STORAGE_NAS_ROOT_PATH + '/vod'

    @property
    def APP_STORAGE_NAS_ROOT_PATH(self):
        # type: () -> str
        r = env.get('APP_STORAGE_NAS_ROOT_PATH')  # type: str
        return r

    @property
    def APP_UPLOAD_ROOT_PATH(self):
        # type: () -> str
        r = env.get('APP_UPLOAD_ROOT_PATH')  # type: str
        return r

class StorageLocalAsyncImplement(
        ThreadingActor,  # type: ignore
        StorageAsyncInterface):
    use_daemon_thread = True

    def check_root_path(self):
        # type: () -> None
        return

    def move_upload_file(self, src, filename):
        # type: (str, str) -> None
        return

    def get_upload_file(self, filename, dst):
        # type: (str, str) -> None
        return

    def delete_upload_file(self, filename):
        # type: (str) -> None
        return

    def copy_vod_file(self, src):
        # type: (str) -> None
        return

    def copy_vod_dir(self, src):
        # type: (str) -> None
        return

    def get_vod_dir(self, dirname, dst_path):
        # type: (str, str) -> None
        return

    def delete_vod_dir(self, dirname):
        # type: (str) -> None
        return

    def get_vod_file(self, filename, dst_path):
        # type: (str, str) -> None
        return

    def delete_vod_file(self, filename):
        # type: (str) -> None
        return

    def is_vod_dir_exists(self, dirname):
        # type: (str) -> bool
        return True

    def is_vod_file_exists(self, filename):
        # type: (str) -> bool
        return True


class StorageAsyncFactory(object):
    __proxy = None

    APP_STORAGE_TYPE = env.get('APP_STORAGE_TYPE',
                               'LOCAL').upper()  # type: str

    @classmethod
    def make(cls):
        # type: () -> StorageAsyncInterface
        if cls.__proxy is None:
            if cls.APP_STORAGE_TYPE == 'LOCAL':
                cls.__proxy = StorageLocalAsyncImplement.start().proxy()
            elif cls.APP_STORAGE_TYPE == 'NAS':
                cls.__proxy = StorageNASAsyncImplement.start().proxy()
            else:
                raise ValueError(
                    'unknow app storage type: %s' % (cls.APP_STORAGE_TYPE, ))
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


storage = StorageAsyncFactory.make()
