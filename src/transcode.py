# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import logging
import traceback
import os

from threading import Thread

from pykka import ThreadingActor, ActorProxy, ThreadingFuture  # noqa

from storage import storage
from record_manager import RecordMediaInfoFactory
from ffmpeg_run import FFmpegRunnerFactory
# import ffmpeg_run

LOGGER = logging.getLogger(__name__)


class TranscoderAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def submit_task(
            self,
            task_id,  # type: str
            file_id,  # type: str
            file_type,  # type: str
            filename,  # type: str
            upload_path,  # type: str
            vod_path,  # type: str
            transcode_args,  # type: Dict[str, Any]
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> ThreadingFuture
        pass


class TranscoderAsyncImplement(
        ThreadingActor,  # type: ignore
        TranscoderAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(TranscoderAsyncImplement, self).__init__()

    def submit_task(
            self,
            task_id,  # type: str
            file_id,  # type: str
            file_type,  # type: str
            filename,  # type: str
            upload_path,  # type: str
            vod_path,  # type: str
            transcode_args,  # type: Dict[str, Any]
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> None
        def transcode():
            # type: () -> None
            LOGGER.debug('transcode %s' % (task_id, ))
            # 将上传文件从 文件存储中心 取出到本地 upload 文件夹
            storage.get_upload_file(filename, upload_path).get(timeout=600)

            # 对文件调用 ffmpeg 转码
            tt = TranscodeTemplateFactory.make(
                str(transcode_args['template_type']))
            ffmpeg_cmd_args = []  # type: List[str]
            src_path = upload_path + '/' + filename
            dst_path = vod_path + '/' + transcode_args['file_id']
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)

            ffmpeg_cmd_args += tt.parse_from_json_to_cmd_args(
                src_path, dst_path, transcode_args)
            ffmpeg_runner = FFmpegRunnerFactory.make()

            try:
                ffmpeg_runner.run_cmd(ffmpeg_cmd_args)
            except IOError:
                LOGGER.error(traceback.format_exc())
                callback_error()
                return

            media_info = RecordMediaInfoFactory.make(dst_path)
            media_info.refresh_media_info()
            media_info.refresh_media_snapshot(0)

            LOGGER.debug(
                '%s ffmpeg_cmd_args is: %s' % (task_id, ffmpeg_cmd_args))
            storage.copy_vod_dir(dst_path).get(timeout=600)

            LOGGER.debug('%s transcode finished, callback' % (task_id, ))
            callback_ok()

        t = Thread(target=transcode)
        t.setDaemon(True)
        t.start()


class TranscoderAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> TranscoderAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = TranscoderAsyncImplement.start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


transcoder = TranscoderAsyncFactory.make()


class TranscodeTemplateInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse_from_json_to_cmd_args(self, src_path, dst_path, body):
        # type: (str, str, Dict[str, Any]) -> List[str]
        pass


class TranscodeTemplateImplement(TranscodeTemplateInterface):
    def __init__(self, template_type):
        # type: (str) -> None
        super(TranscodeTemplateImplement, self).__init__()
        self.template_type = template_type

    def parse_from_json_to_cmd_args(self, src_path, dst_path, body):
        # type: (str, str, Dict[str, Any]) -> List[str]
        result = []  # type: List[str]
        parse_func = getattr(
            self, 'parse_from_json_to_cmd_args_%s' % (self.template_type, ))
        # result += ['-preset', 'veryfast']
        result += ['-i', src_path]
        result += parse_func(body)
        result += ['-vcodec', 'libx264', '-c:a', 'aac']
        result += ['-bf', '0', '-b_strategy', '0']
        result += ['-keyint_min', '60', '-g', '60']
        result += ['-sc_threshold', '0', '-strict', 'experimental']
        result += ['-flags', 'global_header', '-y']

        if body['file_type'] == 'm3u8':
            result += ['-hls_time', '2']
            result += ['-start_number', '0']
            result += ['-hls_flags', 'append_list']
            result += ['-hls_playlist_type', 'vod']
            result += ['-hls_list_size', '0']
            result += ['-f', 'hls']
            result += ['%s/index.m3u8' % (dst_path, )]

        return result

    def parse_from_json_to_cmd_args_1(self, body):
        # type: (Dict[str, Any]) -> List[str]
        result = []  # type: List[str]
        thread_count = {
            '1920x1080': 2,
            '1280x720': 3,
            '848x480': 6,
        }[body['s']]
        result += ['-threads', '%s' % (thread_count, )]
        result += ['-s', '%s' % (body['s'], )]
        result += ['-r', '%s' % (body['r'], )]
        result += ['-crf', '%s' % (body['crf'], )]
        return result


class TranscodeTemplateFactory(object):
    @classmethod
    def make(cls, template_type):
        # type: (str) -> TranscodeTemplateInterface
        __obj = TranscodeTemplateImplement(
            template_type)  # type: TranscodeTemplateInterface
        assert isinstance(__obj, TranscodeTemplateInterface)
        return __obj
