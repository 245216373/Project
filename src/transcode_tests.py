# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa
from mock import Mock, MagicMock, PropertyMock  # noqa
from pytest_mock import MockFixture  # noqa
from pykka import ThreadingActor, ActorProxy, ThreadingFuture  # noqa

from transcode import (TranscoderAsyncInterface, TranscoderAsyncImplement,
                       TranscoderAsyncFactory, TranscodeTemplateInterface,
                       TranscodeTemplateImplement, TranscodeTemplateFactory)


class TestTranscoderAsyncFactory(object):
    def test_make(self):
        # type: () -> None
        obj = TranscoderAsyncFactory.make()
        assert isinstance(obj, ActorProxy)
        assert obj.actor_ref.is_alive()
        assert obj.actor_ref.actor_class == TranscoderAsyncImplement
        obj.actor_ref.stop()


class TestTranscoderAsyncImplement(object):
    def test_is_implement_of_interface(self):
        # type: () -> None
        assert issubclass(TranscoderAsyncImplement, TranscoderAsyncInterface)

    def create_submit_task_args_transcode_args(self):
        # type: () -> Dict[str, Any]
        transcode_args = {
            'template_type': 1,
            'file_id': 'transcode_args_file_id_xx',
            'file_type': 'm3u8',
            's': '1920x1080',
            'r': 24,
            'crf': 34,
        }  # type: Dict[str, Any]
        return transcode_args

    def create_submit_task_args(
            self,
            mocker,  # type: MockFixture
            transcode_args  # type: Dict[str, Any]
    ):
        # type: (...) -> Tuple[str, str, str, str, str, str, Dict[str, Any], MagicMock, MagicMock]  # noqa
        mock_stub_callback_ok = mocker.stub(name='callback_ok')
        mock_stub_callback_error = mocker.stub(name='callback_error')
        return ('task_id_xx', 'file_id_xx', 'm3u8', 'filename_xx',
                '/tmp/upload_path', '/tmp/vod/path', transcode_args,
                mock_stub_callback_ok, mock_stub_callback_error)

    def get_submit_task__transcode_func(self, mocker, obj, submit_task_args):
        # type: (MockFixture, TranscoderAsyncImplement, Tuple) -> Callable
        mock_Thread = mocker.patch(
            'transcode.Thread',
            return_value=mocker.MagicMock())  # type: MagicMock
        obj.submit_task(*submit_task_args)
        return mock_Thread.call_args[1]['target']

    def test_submit_task(self, mocker):
        # type: (MockFixture) -> None
        obj = TranscoderAsyncImplement()
        mock_thread = mocker.MagicMock()  # type: MagicMock
        mock_Thread = mocker.patch(
            'transcode.Thread', return_value=mock_thread)  # type: MagicMock
        obj.submit_task(*self.create_submit_task_args(
            mocker, self.create_submit_task_args_transcode_args()))
        mock_Thread.assert_called_once()
        mock_thread.setDaemon.assert_called_once_with(True)
        mock_thread.start.assert_called_once()

    def create_submit_task__transcode_mocks(self, mocker):
        # type: (MockFixture) -> Dict[str, MagicMock]
        mocks = {}  # type: Dict[str, MagicMock]

        mocks['storage'] = mocker.patch('transcode.storage')
        mocks['tt'] = mocker.MagicMock()
        mocks['TranscodeTemplateFactory_make'] = mocker.patch(
            'transcode.TranscodeTemplateFactory.make',
            return_value=mocks['tt'])
        mocks['os_path_exists'] = mocker.patch(
            'os.path.exists', return_value=False)
        mocks['os_mkdir'] = mocker.patch('os.mkdir')
        mocks['ffmpeg_runner'] = mocker.MagicMock()
        mocks['FFmpegRunnerFactory_make'] = mocker.patch(
            'transcode.FFmpegRunnerFactory.make',
            return_value=mocks['ffmpeg_runner'])
        mocks['media_info'] = mocker.MagicMock()
        mocks['RecordMediaInfoFactory_make'] = mocker.patch(
            'transcode.RecordMediaInfoFactory.make',
            return_value=mocks['media_info'])

        return mocks

    def test_submit_task__transcode_callback_error_with_run_ffmpeg_cmd_raise_IOError(  # noqa
            self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_submit_task__transcode_mocks(mocker)
        mocks['ffmpeg_runner'].run_cmd.side_effect = IOError

        submit_task_args = self.create_submit_task_args(
            mocker, self.create_submit_task_args_transcode_args())
        mock_stub_callback_error = submit_task_args[-1]
        self.get_submit_task__transcode_func(
            mocker, TranscoderAsyncImplement(), submit_task_args)()

        # 执行失败回调
        mock_stub_callback_error.assert_called_once()

    def test_submit_task__transcode_callback_ok(self, mocker):
        # type: (MockFixture) -> None
        mocks = self.create_submit_task__transcode_mocks(mocker)

        task_id, file_id, file_type, filename, upload_path, vod_path, \
            transcode_args, mock_stub_callback_ok, mock_stub_callback_error = \
            submit_task_args = \
            self.create_submit_task_args(
                mocker, self.create_submit_task_args_transcode_args())
        transcode_func = self.get_submit_task__transcode_func(
            mocker, TranscoderAsyncImplement(), submit_task_args)
        transcode_func()

        src_path = '%s/%s' % (upload_path, filename)
        dst_path = '%s/%s' % (vod_path, transcode_args['file_id'])

        # 从文件存储中心取出到本地，超时 600 秒
        mocks['storage'].get_upload_file.assert_called_once_with(
            filename, upload_path)
        mocks['storage'].get_upload_file().get.assert_called_once_with(
            timeout=600)
        # 正确使用了模板生成了转码参数
        mocks['TranscodeTemplateFactory_make'].assert_called_once_with(
            str(transcode_args['template_type']))
        mocks['tt'].parse_from_json_to_cmd_args.assert_called_once_with(
            src_path, dst_path, transcode_args)
        # 如果目标目录不存在时则创建
        mocks['os_path_exists'].assert_called_once_with(dst_path)
        mocks['os_mkdir'].assert_called_once_with(dst_path)
        # 调用了 FFmpegRunnerInterface 执行
        mocks['FFmpegRunnerFactory_make'].assert_called_once()
        mocks['ffmpeg_runner'].run_cmd.assert_called_once()
        # 调用了 RecordMediaInfoInterface 刷新媒体信息
        mocks['RecordMediaInfoFactory_make'].assert_called_once_with(dst_path)
        mocks['media_info'].refresh_media_info.assert_called_once()
        mocks['media_info'].refresh_media_snapshot.assert_called_once_with(0)
        # 存入到文件存储中心，超时 600 秒
        mocks['storage'].copy_vod_dir.assert_called_once_with(dst_path)
        mocks['storage'].copy_vod_dir().get.assert_called_once_with(
            timeout=600)
        # 执行成功回调
        mock_stub_callback_ok.assert_called_once()


class TestTranscodeTemplateImplement(object):
    def test_is_implement_of_interface(self):
        # type: () -> None
        assert issubclass(TranscodeTemplateImplement,
                          TranscodeTemplateInterface)

    def test_parse_from_json_to_cmd_args_with_body_s_eq_1920x1080(self):
        # type: () -> None
        obj = TranscodeTemplateImplement('1')
        src_path, dst_path = '/tmp/src_path', '/tmp/dst_path'
        body = {
            'file_type': 'm3u8',
            's': '1920x1080',
            'r': 24,
            'crf': 34,
        }
        result = obj.parse_from_json_to_cmd_args(src_path, dst_path, body)
        result_string = ' '.join(result)
        assert '-i %s' % src_path in result_string
        assert '-f hls %s' % dst_path in result_string
        assert '-threads 2' in result_string
        assert '-s 1920x1080' in result_string
        assert '-r 24' in result_string
        assert '-crf 34' in result_string


class TestTranscodeTemplateFactor(object):
    def test_make_with_template_type_1(self):
        # type: () -> None
        obj = TranscodeTemplateFactory.make('1')
        assert isinstance(obj, TranscodeTemplateImplement)
