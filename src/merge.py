# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import logging
import traceback
import os
import tempfile

from threading import Thread

from pykka import ThreadingActor, ActorProxy, ThreadingFuture  # noqa

from storage import storage
from record_manager import RecordMediaInfoFactory
from ffmpeg_run import FFmpegRunnerFactory

LOGGER = logging.getLogger(__name__)


class MergerAsyncInterface(object):
    __metaclass__ = ABCMeta

    # @abstractmethod
    # def submit_task(
    #         self,
    #         task_id,  # type: str
    #         file_id,  # type: str
    #         file_type,  # type: str
    #         filename,  # type: str
    #         vod_path,  # type: str
    #         merge_args,  # type: Dict[str, Any]
    #         callback_ok,  # type: Callable
    #         callback_error,  # type: Callable
    # ):
    #     # type: (...) -> ThreadingFuture
    #     pass

    @abstractmethod
    def submit_task(
            self,
            task_id,  # type: str
            vod_path,  # type: str
            merge_args,  # type: Dict[str, Any]
            merge_files,  # type: Dict[str, Any]
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> ThreadingFuture
        pass


class MergerAsyncImplement(
        ThreadingActor,  # type: ignore
        MergerAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(MergerAsyncImplement, self).__init__()

    # def submit_task(
    #         self,
    #         task_id,  # type: str
    #         file_id,  # type: str
    #         file_type,  # type: str
    #         filename,  # type: str
    #         vod_path,  # type: str
    #         merge_args,  # type: Dict[str, Any]
    #         callback_ok,  # type: Callable
    #         callback_error,  # type: Callable
    # ):

    def submit_task(
            self,
            task_id,  # type: str
            vod_path,  # type: str
            merge_args,  # type: Dict[str, Any]
            merge_files,  # type: Dict[str, Any]
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> None
        def merge():
            # type: () -> None
            def to_src_file_path(file_id):
                # type: (str) -> bytes
                path = vod_path + '/' + file_id + '/index.m3u8'
                path = "file '%s'\n" % (path, )
                return path.encode()

            LOGGER.debug('merge %s' % (task_id, ))
            # 将需要剪辑文件从 文件存储中心 取出到本地 vod 文件夹
            # storage.get_vod_dir(file_id,
            #                     vod_path + '/' + file_id).get(timeout=600)

            # 对文件调用 ffmpeg 拼接
            tt = MergeTemplateFactory.make(
                str(merge_args.get('template_type', '1')))
            ffmpeg_cmd_args = []  # type: List[str]
            tmp_dir = tempfile.mkdtemp()
            tmp_src_file_path = tmp_dir + '/src_file_list.txt'
            LOGGER.debug('tmp_src_file_path is %s' % (tmp_src_file_path, ))
            with open(tmp_src_file_path, 'wb') as f:
                f_list = []
                # f_list.append(to_src_file_path(file_id))
                # for merage_file_args in merge_args['merge_files']:  原代码
                for merage_file_args in merge_files:
                    if not merage_file_args['file_id'] or not merage_file_args['file_type']:
                        callback_error()
                        return
                    f_list.append(
                        to_src_file_path(merage_file_args['file_id']))
                    storage.get_vod_dir(
                        merage_file_args['file_id'],
                        vod_path + '/' + merage_file_args['file_id']).get(
                            timeout=600)
                f.writelines(f_list)
            dst_path = vod_path + '/' + merge_args['file_id']
            LOGGER.debug('dst_path is %s' % (dst_path))
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)

            LOGGER.debug('merge params is %s, %s, %s' % (tmp_src_file_path, dst_path, merge_args))
            ffmpeg_cmd_args += tt.parse_from_json_to_cmd_args(
                tmp_src_file_path, dst_path, merge_args)
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

            LOGGER.debug('%s merge finished, callback' % (task_id, ))
            callback_ok()

        t = Thread(target=merge)
        t.setDaemon(True)
        t.start()


class MergerAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> MergerAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = MergerAsyncImplement.start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


merger = MergerAsyncFactory.make()


class MergeTemplateInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse_from_json_to_cmd_args(self, src_path, dst_path, body):
        # type: (str, str, Dict[str, Any]) -> List[str]
        pass


class MergeTemplateImplement(MergeTemplateInterface):
    def __init__(self, template_type):
        # type: (str) -> None
        super(MergeTemplateImplement, self).__init__()
        self.template_type = template_type

    def parse_from_json_to_cmd_args(self, src_path, dst_path, body):
        # type: (str, str, Dict[str, Any]) -> List[str]
        result = []  # type: List[str]
        parse_func = getattr(
            self, 'parse_from_json_to_cmd_args_%s' % (self.template_type, ))
        result += ['-f', 'concat']
        result += ['-safe', '0']
        result += ['-i', src_path]
        result += parse_func(body)
        result += ['-c', 'copy']

        if body['file_type'] == 'm3u8':
            result += ['-hls_time', '5']
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
        return result


class MergeTemplateFactory(object):
    @classmethod
    def make(cls, template_type):
        # type: (str) -> MergeTemplateInterface
        __obj = MergeTemplateImplement(
            template_type)  # type: MergeTemplateInterface
        assert isinstance(__obj, MergeTemplateInterface)
        return __obj
