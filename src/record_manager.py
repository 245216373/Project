# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from typing import Dict, List, cast, Any
import logging
import traceback
import uuid
import os
import shutil
import tempfile
import subprocess
import json
import time
import copy

from storage import storage

from crlib.env import env

LOGGER = logging.getLogger(__name__)


class RecorderInterface(object):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def file_id(self):
        # type: () -> str
        pass

    @abstractmethod
    def create_record_dir(self):
        # type: () -> None
        pass

    @abstractmethod
    def transfer(self):
        # type: () -> None
        pass


class VodManagerInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_vod_file_exists(self):
        # type: () -> bool
        pass

    @abstractmethod
    def delete_vod_file(self):
        # type: () -> None
        pass

    @property
    @abstractmethod
    def vod_info(self):
        # type: () -> Dict[str, Any]
        pass


class RecordFileInterface(RecorderInterface, VodManagerInterface):
    pass


class RecordFileImplement(RecordFileInterface):
    def __init__(self, channel_id, meeting_id, file_id):
        # type: (str, str, str) -> None
        super(RecordFileImplement, self).__init__()
        self.channel_id = channel_id
        self.meeting_id = meeting_id
        self._file_id = file_id
        self.fixer = RecordFixerFactory.make(self.vod_dir)

    @property
    def APP_RECORD_ROOT_PATH(self):
        # type: () -> str
        return cast(str, env.get('APP_RECORD_ROOT_PATH'))

    @property
    def APP_VOD_ROOT_PATH(self):
        # type: () -> str
        return cast(str, env.get('APP_VOD_ROOT_PATH'))

    @property
    def APP_UPLOAD_ROOT_PATH(self):
        # type: () -> str
        return cast(str, env.get("APP_UPLOAD_ROOT_PATH"))

    @property
    def APP_VOD_PALY_URL(self):
        # type: () -> str
        return cast(str, env.get('APP_VOD_PALY_URL'))

    @property
    def APP_RECORD_IS_RECODE_FLV(self):
        # type: () -> str
        return cast(str, env.get('APP_RECORD_IS_RECODE_FLV'))

    @property
    def file_id(self):
        # type: () -> str
        return self._file_id

    @property
    def vod_info(self):
        # type: () -> Dict[str, Any]
        info = copy.copy(RecordMediaInfoFactory.make(self.vod_dir).info)
        info['file_id'] = self.file_id
        info['relative_file_name'] = self.vod_relative_file_name
        info['play_url'] = '%s/%s' % (self.APP_VOD_PALY_URL,
                                      info['relative_file_name'])
        if 'snapshot_name' in info:
            info['relative_snapshot_file_name'] = \
                self.vod_relative_path + '/' + info['snapshot_name']
            info['snapshot_url'] = '%s/%s' % (
                self.APP_VOD_PALY_URL, info['relative_snapshot_file_name'])
        return info

    @property
    def record_dir(self):
        # type: () -> str
        return '%s/%s' % (self.APP_RECORD_ROOT_PATH, self.channel_id)

    @property
    def record_flv_path(self):
        # type: () -> str
        return '%s/%s.flv' % (self.APP_RECORD_ROOT_PATH, self.channel_id)

    @property
    def vod_flv_file_name(self):
        # type: () -> str
        return '%s.flv' % (self.file_id, )

    @property
    def local_vod_flv_path(self):    # 新增vod删除vod文件夹下的flv文件
        # type: () -> str
        return '%s/%s.flv' % (self.APP_VOD_ROOT_PATH, self.file_id)

    @property
    def vod_relative_path(self):
        # type: () -> str
        # return '%s/%s' % (self.meeting_id, self.file_id)
        return self.file_id

    @property
    def vod_relative_file_name(self):
        # type: () -> str
        return '%s/index.m3u8' % (self.vod_relative_path)

    @property
    def vod_dir(self):
        # type: () -> str
        return '%s/%s' % (self.APP_VOD_ROOT_PATH, self.vod_relative_path)

    @property
    def upload_dir(self):
        # type: () -> str
        return '%s/%s' % (self.APP_UPLOAD_ROOT_PATH, self.vod_relative_path)

    @property
    def vod_dir_name(self):
        # type: () -> str
        return self.file_id

    @property
    def vod_flv_path(self):
        # type: () -> str
        return '%s.flv' % (self.file_id, )

    @property
    def vod_flv_path(self):
        # type: () -> str
        return '%s/%s.flv' % (self.APP_VOD_ROOT_PATH, self.file_id)

    @property
    def vod_upload_name(self):
        # type: () -> str
        return self.file_id

    def is_vod_file_exists(self):
        # type: () -> bool
        return storage.is_vod_dir_exists(self.vod_dir) or \
            os.path.exists(self.vod_dir)

    def create_record_dir(self):
        # type: () -> None
        LOGGER.debug(
            '[%s] mkdir record dir %s' % (self.channel_id, self.record_dir))
        if not os.path.exists(self.record_dir):
            os.makedirs(self.record_dir)

    def delete_vod_file(self):
        # type: () -> None
        if storage.is_vod_dir_exists(self.vod_dir_name):
            storage.delete_vod_dir(self.vod_dir_name)
            storage.delete_upload_file(self.vod_dir_name)
        if self.is_vod_file_exists():
            shutil.rmtree(self.vod_dir)
            os.popen("rm -rf %s.*" % self.upload_dir)  # 增加删除上传的文件
        #
        # if self.APP_RECORD_IS_RECODE_FLV:
        #     if storage.is_vod_file_exists(self.record_flv_path):
        #         storage.delete_vod_file(self.vod_flv_file_name)
        #     if os.path.exists(self.record_flv_path):
        #         shutil.rmtree(self.record_flv_path)

        if self.APP_RECORD_IS_RECODE_FLV:    # 修改删除flv文件代码,注释部分为原代码
            if storage.is_vod_file_exists(self.vod_flv_file_name):
                storage.delete_vod_file(self.vod_flv_file_name)
            if os.path.exists(self.local_vod_flv_path):
                LOGGER.debug('rm %s' % (self.local_vod_flv_path, ))
                os.popen('rm -rf %s' % (self.local_vod_flv_path, ))


    def transfer(self):
        # type: () -> None
        LOGGER.info('[%s] transfer dir from %s to %s' %
                    (self.channel_id, self.record_dir, self.vod_dir))
        if os.path.exists(self.vod_dir):
            shutil.rmtree(self.vod_dir)
        shutil.move(self.record_dir, self.vod_dir)
        try:
            self.fixer.fix()
        except IOError as e:
            LOGGER.debug('clean error vod dir')
            shutil.rmtree(self.vod_dir)
            if self.APP_RECORD_IS_RECODE_FLV:
                if os.path.exists(self.vod_flv_path):
                    os.remove(self.vod_flv_path)
            raise (e)
        else:
            storage.copy_vod_dir(self.vod_dir)
            if self.APP_RECORD_IS_RECODE_FLV:
                if os.path.exists(self.record_flv_path):
                    shutil.move(self.record_flv_path, self.vod_flv_path)
                    storage.copy_vod_file(self.vod_flv_path)

    @staticmethod
    def generate_id():
        # type: () -> str
        return str(uuid.uuid4()).replace('-', '')


class RecordFileFactory(object):
    @classmethod
    def make(cls, channel_id, meeting_id, file_id=None):
        # type: (str, str, Optional[str]) -> RecordFileInterface
        if file_id is None:
            file_id = RecordFileImplement.generate_id()
        o = RecordFileImplement(channel_id, meeting_id,
                                file_id)  # type: RecordFileInterface
        assert isinstance(o, RecordFileInterface)
        LOGGER.debug('[%s] create a new record manager, file_id is %s' %
                     (channel_id, file_id))
        return o


class RecorderFactory(object):
    @classmethod
    def make(cls, channel_id, meeting_id, file_id=None):
        # type: (str, str, Optional[str]) -> RecorderInterface
        o = RecordFileFactory.make(channel_id, meeting_id,
                                   file_id)  # type: RecorderInterface
        assert isinstance(o, RecorderInterface)
        LOGGER.debug('[%s] create a new recorder, file_id is %s' % (channel_id,
                                                                    file_id))
        return o


class VodManagerFactory(object):
    @classmethod
    def make(cls, meeting_id, file_id):
        # type: (str, str) -> VodManagerInterface
        o = RecordFileFactory.make(meeting_id, meeting_id,
                                   file_id)  # type: VodManagerInterface
        assert isinstance(o, VodManagerInterface)
        LOGGER.debug('[%s] create a new vod manager, file_id is %s' %
                     (meeting_id, file_id))
        return o


class RecordFixerInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def fix(self):
        # type: () -> None
        pass


class RecordFixerImplement(RecordFixerInterface):
    def __init__(self, file_path):
        # type: (str) -> None
        super(RecordFixerImplement, self).__init__()
        self.file_path = file_path
        self._last_time_3_files_by_cache = None  # type: Optional[List[str]]

    @property
    def FFMPEG_CMD_PATH(self):
        # type: () -> str
        return cast(str, env.get('FFMPEG_CMD_PATH'))

    @property
    def m3u8_index_file_path(self):
        # type: () -> str
        return self.file_path + '/' + 'index.m3u8'

    def is_full_m3u8_file(self):
        # type: () -> bool
        with open(self.m3u8_index_file_path, mode='rb') as f:
            sa = b'#EXT-X-ENDLIST\n'
            f.seek(-1 * len(sa), 2)
            sb = f.read()
            return sa == sb

    @property
    def last_time_3_files_by_cache(self):
        # type: () -> List[str]
        if self._last_time_3_files_by_cache is not None:
            return cast(List[str], self._last_time_3_files_by_cache)
        cmd = '''ls -t %s''' % self.file_path  # WARN: hide file
        p = subprocess.Popen(
            cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=30)
        exit_code = p.poll()
        if exit_code != 0:
            raise RuntimeError(
                'ls dir file error code %s err %s' % (exit_code, err))
        self._last_time_3_files_by_cache = out.decode().split('\n')[:-1][:3]
        return cast(List[str], self._last_time_3_files_by_cache)

    def fix_index_m3u8_in_tmp(self, ts_file_name, tmp_dir):
        # type: (str, str) -> bool
        tmp_ts_file = tmp_dir + '/tmp.ts'
        LOGGER.debug(
            'cp %s to %s' % (self.file_path + '/' + ts_file_name, tmp_ts_file))
        shutil.copy(self.file_path + '/' + ts_file_name, tmp_ts_file)

        ffmpeg_cmd = '%s -y -v quiet -i %s -codec copy ' % \
            (self.FFMPEG_CMD_PATH, tmp_ts_file)
        ffmpeg_cmd += '-hls_time 2 -start_number 0 -hls_flags '
        ffmpeg_cmd += 'append_list -hls_playlist_type vod -hls_list_size 0 '
        ffmpeg_cmd += '-f hls %s/index.m3u8' % (tmp_dir, )
        LOGGER.debug('ffmpeg cmd is: %s' % (ffmpeg_cmd, ))
        exit_code = subprocess.call(ffmpeg_cmd.split(), timeout=30)
        if exit_code != 0:
            LOGGER.error(
                'ffmpeg conv file %s error code %s' % (tmp_ts_file, exit_code))
        return exit_code == 0

    def fix_1_file(self):
        # type: () -> None
        assert len(self.last_time_3_files_by_cache) == 1
        tmp_dir = tempfile.mkdtemp()
        ts_file_name = self.last_time_3_files_by_cache[0]
        if self.fix_index_m3u8_in_tmp(ts_file_name, tmp_dir):
            os.remove(self.m3u8_index_file_path)
            shutil.copy(tmp_dir + '/index.m3u8', self.m3u8_index_file_path)
        else:
            with open(self.m3u8_index_file_path, mode='ab') as f:
                f.write(b'\n#EXT-X-ENDLIST')
        shutil.rmtree(tmp_dir)

    def fix_more_1_file(self):
        # type: () -> None
        if self.is_full_m3u8_file():
            LOGGER.debug(
                'there is full m3u8 file %s' % (self.m3u8_index_file_path, ))
            return

        tmp_dir = tempfile.mkdtemp()
        ts_file_name = self.last_time_3_files_by_cache[0]

        if self.fix_index_m3u8_in_tmp(ts_file_name, tmp_dir):
            with open(tmp_dir + '/' + 'index.m3u8', mode='rb') as f:
                lines = f.readlines()
                value = lines[-3] + ts_file_name.encode() + b'\n' + lines[-1]

            with open(self.m3u8_index_file_path, mode='ab') as f:
                f.write(value)
        else:
            with open(self.m3u8_index_file_path, mode='ab') as f:
                f.write(b'#EXT-X-ENDLIST\n')

        shutil.rmtree(tmp_dir)

    def fix(self):
        # type: () -> None
        files = self.last_time_3_files_by_cache
        if len(files) == 0:
            LOGGER.debug('file count is zero, ignore')
            raise IOError('file count is zero')

        if len(files) == 1:
            LOGGER.debug('file count is 1')
            self.fix_1_file()
        else:
            LOGGER.debug('file count more 1')
            self.fix_more_1_file()

        media_info = RecordMediaInfoFactory.make(self.file_path)
        media_info.refresh_media_info()
        media_info.refresh_media_snapshot(0)


class RecordFixerFactory(object):
    @classmethod
    def make(cls, file_path):
        # type: (str) -> RecordFixerInterface
        o = RecordFixerImplement(file_path)  # type: RecordFixerInterface
        assert isinstance(o, RecordFixerInterface)
        return o


class RecordMediaInfoInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def refresh_media_info(self):
        # type: () -> None
        pass

    @abstractmethod
    def refresh_media_snapshot(self, time_pos):
        # type: (int) -> None
        pass

    @property
    @abstractmethod
    def info(self):
        # type: () -> Dict[str, Any]
        pass


class RecordMediaInfoImplement(RecordMediaInfoInterface):
    def __init__(self, path):
        # type: (str) -> None
        super(RecordMediaInfoImplement, self).__init__()
        self.path = path
        self._info = {}  # type: Dict[str, Any]
        self.init_path()
        self.load()

    @property
    def FFMPEG_CMD_PATH(self):
        # type: () -> str
        return cast(str, env.get('FFMPEG_CMD_PATH'))

    @property
    def FFPROBE_CMD_PATH(self):
        # type: () -> str
        root_path = os.path.dirname(self.FFMPEG_CMD_PATH)
        if not root_path:
            return 'ffprobe'
        else:
            return root_path + '/ffprobe'

    @property
    def info(self):
        # type: () -> Dict[str, Any]
        return self._info

    @info.setter
    def info(self, info):
        # type: (Dict[str, Any]) -> None
        self._info = info

    @property
    def file_path(self):
        # type: () -> str
        return self.path + '/.media_info'

    def re_init_file(self):
        # type: () -> None
        self.info = {'create_time': int(time.time())}
        self.dump()

    def init_path(self):
        # type: () -> None
        if not os.path.exists(self.file_path):
            self.re_init_file()

    def dump(self):
        # type: () -> None
        with open(self.file_path, 'w') as f:
            json.dump(self.info, f)

    def load(self):
        # type: () -> None
        def _load():
            # type: () -> None
            with open(self.file_path, 'r') as f:
                self.info = cast(Dict[str, Any], json.load(f))

        try:
            _load()
        except Exception:
            LOGGER.error('file %s error, re init file. traceback is %s' %
                         (self.file_path, traceback.format_exc()))
            self.re_init_file()
            _load()
            LOGGER.warn('file re init by exception')

    def view_media_info(self):
        # type: () -> Dict[str, Any]
        ffprobe_cmd = '%s -v quiet -hide_banner ' % (self.FFPROBE_CMD_PATH, )
        ffprobe_cmd += '-print_format json -show_streams -show_format '
        ffprobe_cmd += '-i %s ' % (self.path + '/index.m3u8', )
        LOGGER.debug('ffprobe cmd is: %s' % (ffprobe_cmd, ))
        p = subprocess.Popen(
            ffprobe_cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=30)
        exit_code = p.poll()
        if exit_code != 0:
            raise RuntimeError(
                'ffprobe error code %s err %s' % (exit_code, err))
        try:
            info = json.loads(out.decode())  # type: Dict[str, Any]
        except Exception as e:
            LOGGER.error('view %s media info error %s' % (self.path, e))
            LOGGER.error(traceback.format_exc())
            info = {}

        return info

    def refresh_media_snapshot(self, time_pos):
        # type: (int) -> None
        LOGGER.debug('Enter refresh_media_snapshot')
        if 'snapshot_name' not in self.info:
            LOGGER.debug('do not update media snapshot path, media info error')
            return
        if time_pos < 0 or time_pos > self.info['record_time_lenght']:
            LOGGER.debug('do not update media snapshot path, time pos error')
            return

        if time_pos > 30:
            LOGGER.debug('do not update media snapshot path, time pos limit')
            return
        ffmpeg_cmd = '%s -y -v quiet -i %s -ss %d -vframes 1 %s' % \
            (self.FFMPEG_CMD_PATH, self.path + '/index.m3u8',
             time_pos, self.path + '/' + self.info['snapshot_name'])
        LOGGER.debug('ffmpeg cmd is: %s' % (ffmpeg_cmd, ))
        exit_code = subprocess.call(ffmpeg_cmd.split(), timeout=30)
        if exit_code != 0:
            raise RuntimeError(
                'ffmpeg snapshot file error code %s' % (exit_code, ))

    def refresh_media_info(self):
        # type: () -> None
        media_info = self.view_media_info()
        if not media_info:
            LOGGER.debug('do not update media info, because media info error')
            return
        LOGGER.debug('Enter refresh_media_info')
        new_info = copy.copy(self.info)
        try:
            new_info['file_path'] = '%s/index.m3u8' % self.path
            new_info['snapshot_name'] = '.snapshot.jpg'
            new_info['file_size'] = self.count_file_size()
            new_info['record_begin_time'] = new_info['create_time']
            new_info['record_end_time'] = \
                new_info['create_time'] + \
                int(float(media_info['format']['duration']))
            new_info['record_time_lenght'] = \
                new_info['record_end_time'] - new_info['record_begin_time']
            new_info['audio_channel'] = media_info['streams'][1]['channels']
            new_info['resolution'] = str(media_info['streams'][0]['height'])
        except Exception as e:
            LOGGER.error('refresh %s media info error %s' % (self.path, e))
            LOGGER.error(traceback.format_exc())
            return
        self.info = new_info
        self.dump()

    def count_file_size(self):
        # type: () -> str
        out = subprocess.check_output(['du', '-s', self.path])
        size = out.split()[0].decode('utf-8')  # type: str
        return size


class RecordMediaInfoFactory(object):
    @classmethod
    def make(cls, path):
        # type: (str) -> RecordMediaInfoInterface
        o = RecordMediaInfoImplement(path)  # type: RecordMediaInfoInterface
        assert isinstance(o, RecordMediaInfoInterface)
        return o
