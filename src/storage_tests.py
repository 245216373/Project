# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa
from mock import Mock, MagicMock, PropertyMock  # noqa
from pytest_mock import MockFixture  # noqa
from pykka import ThreadingActor, ActorProxy, ThreadingFuture  # noqa

import pytest
from mock import call

from storage import StorageAsyncInterface, StorageAsyncFactory
from storage import StorageNASAsyncImplement, StorageLocalAsyncImplement


class TestStorageNASAsyncImplement(object):
    def test_is_implement_of_interface(self):
        # type: () -> None
        assert issubclass(StorageNASAsyncImplement, StorageAsyncInterface)

    @pytest.fixture(autouse=True)
    def mock_ENVs(self, mocker):
        # type: (MockFixture) -> None
        def side_effect_env_get(name, default=None, type_=None):
            # type: (str, Optional[Any], Optional[Type]) -> Any
            if name == 'APP_STORAGE_NAS_ROOT_PATH':
                return '/tmp/nas'

        mocker.patch('storage.env.get', side_effect=side_effect_env_get)

    def create_mocks(self, mocker):
        # type: (MockFixture) -> Dict[str, MagicMock]
        mocks = {}  # type: Dict[str, MagicMock]

        mocks['os.path.exists'] = mocker.patch(
            'storage.os.path.exists', return_value=True)
        mocks['os.mkdir'] = mocker.patch('storage.os.mkdir')
        mocks['os.remove'] = mocker.patch('storage.os.remove')
        mocks['shutil.move'] = mocker.patch('storage.shutil.move')
        mocks['shutil.copy'] = mocker.patch('storage.shutil.copy')
        mocks['shutil.rmtree'] = mocker.patch('storage.shutil.rmtree')
        mocks['shutil.copytree'] = mocker.patch('storage.shutil.copytree')

        return mocks

    def test_move_upload_file(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/nas/upload/filename']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        src_file, filename = '/tmp/src_file', 'filename'
        dst_file = '/tmp/nas/upload/filename'
        obj.move_upload_file(src_file, filename)

        mocks['os.mkdir'].assert_called_once_with(obj.UPLOAD_PATH)
        mocks['os.path.exists'].call_args_list == [
            call(obj.UPLOAD_PATH), call(dst_file)
        ]
        mocks['shutil.move'].assert_called_once_with(src_file, dst_file)

    def test_get_upload_file(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in [
                '/tmp/nas', '/tmp/nas/upload/filename', '/tmp/upload/filename'
            ]

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        dst_path, filename = '/tmp/upload', 'filename'
        src_file, dst_file = '/tmp/nas/upload/filename', dst_path + '/filename'
        obj.get_upload_file(filename, dst_path)

        mocks['os.path.exists'].assert_called_with(dst_file)
        mocks['os.remove'].assert_called_with(dst_file)
        mocks['shutil.copy'].assert_called_once_with(src_file, dst_path)

    def test_delete_upload_file(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/nas/upload/filename']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        filename, src_file = 'filename', '/tmp/nas/upload/filename'
        obj.delete_upload_file(filename)

        mocks['os.path.exists'].assert_called_with(src_file)
        mocks['os.remove'].assert_called_with(src_file)

    def test_copy_vod_file(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/nas/vod/filename']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        src_file, dst_file = '/tmp/vod/filename', '/tmp/nas/vod/filename'
        obj.copy_vod_file(src_file)

        mocks['os.path.exists'].call_args_list == [
            call(obj.VOD_PATH), call(dst_file)
        ]
        mocks['os.remove'].assert_called_once_with(dst_file)
        mocks['shutil.copy'].assert_called_once_with(src_file, dst_file)

    def test_copy_vod_dir(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/nas/vod/dirname']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        src_dir, dst_dir = '/tmp/vod/dirname', '/tmp/nas/vod/dirname'
        obj.copy_vod_dir(src_dir)

        mocks['os.path.exists'].call_args_list == [
            call(obj.VOD_PATH), call(dst_dir)
        ]
        mocks['shutil.rmtree'].assert_called_once_with(dst_dir)
        mocks['shutil.copytree'].assert_called_once_with(src_dir, dst_dir)

    def test_get_vod_dir(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.get_vod_dir('dirname', '/tmp/vod/dirname')

        mocks['os.path.exists'].assert_called_with('/tmp/vod/dirname')
        mocks['shutil.copytree'].assert_called_once_with(
            '/tmp/nas/vod/dirname', '/tmp/vod/dirname')

    def test_get_vod_dir_return_with_dst_path_exists(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/vod/dirname']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.get_vod_dir('dirname', '/tmp/vod/dirname')

        mocks['os.path.exists'].assert_called_with('/tmp/vod/dirname')
        mocks['shutil.copytree'].assert_not_called()

    def test_delete_vod_dir(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/nas/vod/dirname']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.delete_vod_dir('dirname')

        mocks['os.path.exists'].assert_called_with('/tmp/nas/vod/dirname')
        mocks['shutil.rmtree'].assert_called_once_with('/tmp/nas/vod/dirname')

    def test_get_vod_file(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.get_vod_file('filename', '/tmp/vod/filename')

        mocks['os.path.exists'].assert_called_with('/tmp/vod/filename')
        mocks['shutil.copy'].assert_called_once_with('/tmp/nas/vod/filename',
                                                     '/tmp/vod/filename')

    def test_get_vod_file_return_with_dst_path_exists(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/vod/filename']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.get_vod_file('filename', '/tmp/vod/filename')

        mocks['os.path.exists'].assert_called_with('/tmp/vod/filename')
        mocks['shutil.copy'].assert_not_called()

    def test_delete_vod_file(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas', '/tmp/nas/vod/filename']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.delete_vod_file('filename')

        mocks['os.path.exists'].assert_called_with('/tmp/nas/vod/filename')
        mocks['os.remove'].assert_called_once_with('/tmp/nas/vod/filename')

    def test_is_vod_dir_exists(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.is_vod_dir_exists('dirname')

        mocks['os.path.exists'].assert_called_with('/tmp/nas/vod/dirname')

    def test_is_vod_file_exists(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_mocks(mocker)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            return path in ['/tmp/nas']

        mocks['os.path.exists'] = mocker.patch(
            'os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageNASAsyncImplement()
        obj.is_vod_dir_exists('filename')

        mocks['os.path.exists'].assert_called_with('/tmp/nas/vod/filename')


class TestStorageLocalAsyncImplement(object):
    def test_is_implement_of_interface(self):
        # type: () -> None
        assert issubclass(StorageLocalAsyncImplement, StorageAsyncInterface)


class TestStorageNASAsyncFactory(object):
    def test_make_NAS(self, mocker):
        # type: (MockFixture) -> None
        mocker.patch(
            'storage.StorageAsyncFactory.APP_STORAGE_TYPE',
            new_callable=PropertyMock,
            return_value='NAS')
        mocker.patch(
            'storage.StorageAsyncFactory._StorageAsyncFactory__proxy',
            new_callable=PropertyMock,
            return_value=None)

        def side_effect_env_get(name, default=None, type_=None):
            # type: (str, Optional[Any], Optional[Type]) -> Any
            if name == 'APP_STORAGE_NAS_ROOT_PATH':
                return '/tmp/nas'

        mocker.patch('storage.env.get', side_effect=side_effect_env_get)

        def side_effect_os_path_exists(path):
            # type: (str) -> bool
            if path == '/tmp/nas':
                return True
            else:
                return False

        mocker.patch('os.path.exists', side_effect=side_effect_os_path_exists)

        obj = StorageAsyncFactory.make()
        assert isinstance(obj, ActorProxy)
        assert obj.actor_ref.is_alive()
        assert obj.actor_ref.actor_class == StorageNASAsyncImplement
        obj.actor_ref.stop()

    def test_make_Local(self, mocker):
        # type: (MockFixture) -> None
        mocker.patch(
            'storage.StorageAsyncFactory.APP_STORAGE_TYPE',
            new_callable=PropertyMock,
            return_value='LOCAL')
        mocker.patch(
            'storage.StorageAsyncFactory._StorageAsyncFactory__proxy',
            new_callable=PropertyMock,
            return_value=None)

        obj = StorageAsyncFactory.make()
        assert isinstance(obj, ActorProxy)
        assert obj.actor_ref.is_alive()
        assert obj.actor_ref.actor_class == StorageLocalAsyncImplement
        obj.actor_ref.stop()
