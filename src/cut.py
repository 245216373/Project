# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa

import re
import time

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
from crlib.env import env

LOGGER = logging.getLogger(__name__)


class CutterAsyncInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def submit_task(
            self,
            task_id,  # type: str
            file_id,  # type: str
            file_type,  # type: str
            filename,  # type: str
            vod_path,  # type: str
            cut_args,  # type: Dict[str, Any]
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> ThreadingFuture
        pass


class CutterAsyncImplement(
        ThreadingActor,  # type: ignore
        CutterAsyncInterface):
    use_daemon_thread = True

    def __init__(self):
        # type: () -> None
        super(CutterAsyncImplement, self).__init__()

    def submit_task(
            self,
            task_id,  # type: str
            file_id,  # type: str
            file_type,  # type: str
            filename,  # type: str
            vod_path,  # type: str
            cut_args,  # type: Dict[str, Any]
            callback_ok,  # type: Callable
            callback_error,  # type: Callable
    ):
        # type: (...) -> None
        def cut():
            # type: () -> None
            LOGGER.debug('cut %s' % (task_id, ))
            # 将需要剪辑文件从 文件存储中心 取出到本地 vod 文件夹
            storage.get_vod_dir(file_id,
                                vod_path + '/' + file_id).get(timeout=600)

            # 对文件调用 ffmpeg 拼接
            tt = CutTemplateFactory.make(
                str(cut_args.get('template_type', '1')))
            ffmpeg_cmd_args = []  # type: List[str]
            src_path = vod_path + '/' + file_id + '/index.m3u8'
            dst_path = vod_path + '/' + cut_args['file_id']
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)

            ffmpeg_cmd_args += tt.parse_from_json_to_cmd_args(
                src_path, dst_path, cut_args)
            ffmpeg_runner = FFmpegRunnerFactory.make()
            try:
                ffmpeg_runner.run_cmd(ffmpeg_cmd_args)
            except IOError:
                LOGGER.error(traceback.format_exc())
                callback_error()
                return

            fix_cut_m3u8_file(dst_path)   # 针对裁剪只能出现最后4个ts解决方案
            media_info = RecordMediaInfoFactory.make(dst_path)
            LOGGER.debug(media_info)
            media_info.refresh_media_info()
            media_info.refresh_media_snapshot(0)

            LOGGER.debug(
                '%s ffmpeg_cmd_args is: %s' % (task_id, ffmpeg_cmd_args))
            storage.copy_vod_dir(dst_path).get(timeout=600)

            LOGGER.debug('%s cut finished, callback' % (task_id, ))
            callback_ok()

        t = Thread(target=cut)
        t.setDaemon(True)
        t.start()


class CutterAsyncFactory(object):
    __proxy = None

    @classmethod
    def make(cls):
        # type: () -> CutterAsyncInterface
        if cls.__proxy is None:
            cls.__proxy = CutterAsyncImplement.start().proxy()
        assert isinstance(cls.__proxy, ActorProxy)
        return cls.__proxy  # type: ignore


cutter = CutterAsyncFactory.make()


class CutTemplateInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse_from_json_to_cmd_args(self, src_path, dst_path, body):
        # type: (str, str, Dict[str, Any]) -> List[str]
        pass


class CutTemplateImplement(CutTemplateInterface):
    def __init__(self, template_type):
        # type: (str) -> None
        super(CutTemplateImplement, self).__init__()
        self.template_type = template_type

    def parse_from_json_to_cmd_args(self, src_path, dst_path, body):
        # type: (str, str, Dict[str, Any]) -> List[str]
        result = []  # type: List[str]
        parse_func = getattr(
            self, 'parse_from_json_to_cmd_args_%s' % (self.template_type, ))
        result += ['-i', src_path]
        result += parse_func(body)
        result += ['-c', 'copy']

        if body['file_type'] == 'm3u8':
            result += ['%s/index.m3u8' % (dst_path, )]

        return result

    def parse_from_json_to_cmd_args_1(self, body):
        # type: (Dict[str, Any]) -> List[str]
        result = []  # type: List[str]
        result += ['-ss', '%s' % (body['ss'], )]
        result += ['-t', '%s' % (body['t'], )]
        return result


class CutTemplateFactory(object):
    @classmethod
    def make(cls, template_type):
        # type: (str) -> CutTemplateInterface
        __obj = CutTemplateImplement(
            template_type)  # type: CutTemplateInterface
        assert isinstance(__obj, CutTemplateInterface)
        return __obj

# ffmpeg裁剪后m3u8文件只会保留最后五个ts,需要对其重新进行写入
def fix_cut_m3u8_file(file_path):
    with open(file_path + '/index.m3u8', 'r') as f:    # 获取总ts片数以及单个ts时间
        result = f.read()
        last_time_info = result.split('\n')

        ts_num_pattern = '#EXT-X-MEDIA-SEQUENCE:(.+)'
        ts_time_pattern = '#EXTINF:(.+),'

        ts_num = re.findall(ts_num_pattern, result)
        ts_time = re.findall(ts_time_pattern, result)

        num = int(ts_num[0])
        ts_time = ts_time[0]

        last_3_lines_info = last_time_info[-4] + '\n' + \
                            last_time_info[-3] + '\n' + last_time_info[-2] + '\n'
        with open(file_path + '/index.m3u8', 'w') as fd:
            for i in last_time_info:
                if i[0: 22] == '#EXT-X-MEDIA-SEQUENCE:':
                    fd.write('#EXT-X-MEDIA-SEQUENCE:%s\n' % 0)
                    break
                fd.write(i + '\n')
            for i in range(num + 4):
                fd.write('#EXTINF:%s,\n' % ts_time)
                fd.write('index%s.ts\n' % i)
            fd.write(last_3_lines_info)

# 清除因未上传完成超时的分片
def clear_timeout_sharding():

    # LOGGER.debug('clear timeout sharding')
    def file_path(file):    # 文件路径
        return sharding_upload_path + '/' + file

    sharding_upload_path = env.get("APP_UPLOAD_ROOT_PATH")
    clear_timeout = env.get('CLEAR_SHARDING')
    files = os.popen("ls -l %s | awk '{print $9}'" % (sharding_upload_path, ))
    for file in files:
        sharding_file_path = file_path(file.strip())
        # LOGGER.debug('file %s' % (sharding_file_path, ))
        if file == '\n' or '.' in file:
            continue
        t = os.path.getctime(sharding_file_path)
        if t + int(clear_timeout) < time.time():
            try:
                os.remove(sharding_file_path)
                LOGGER.debug('remove file %s' % (sharding_file_path, ))
            except Exception as e:
                raise e
