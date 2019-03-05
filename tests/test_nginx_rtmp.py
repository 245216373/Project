# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa
from toolz.compatibility import *  # noqa

from fn import _ as X
from functoolsex import lmap

import unittest

import os
import shutil
import time
import threading
import requests

from .resources import (
    APP_STORAGE_TYPE,
    INFO_RECORD_FILE_URL,
    ResourcesNAS,
    SRC_MP4_PATH,
    SRC_LONG_MP4_PATH,
    MP4_FILE_RECORD_HLS_DIR_PATH,
    MP4_FILE_RECORD_FLV_FILE_PATH,
    MP4_FILE_VOD_HLS_DIR_PATH,
    MP4_FILE_VOD_FLV_FILE_PATH,
    MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH,
    MP4_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH,
    MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH,
    RTMP_LIVE_PUBLISH_URL,
    RTMP_MEETING_ID,
    RTMP_ROOT_URL,
    UPLOAD_MP4_FILE_ID,
)
from .utils import ffmpeg_run_cmd


def publish_to_nginx_rtmp(src, urls, timeout=5):
    # type: (str, List[str], int) -> None
    cmd_args = ['-re', '-fflags', '+genpts', '-stream_loop', '-1', '-i', src]
    for url in urls:
        cmd_args += ['-c', 'copy', '-f', 'flv', url]
    ffmpeg_run_cmd(cmd_args, timeout=timeout)


class TestNginxRtmpPublish(ResourcesNAS, unittest.TestCase):
    def test_publish_live(self):
        # type: () -> None
        publish_to_nginx_rtmp(SRC_MP4_PATH, [RTMP_LIVE_PUBLISH_URL], timeout=5)

        time.sleep(1)
        self.assertTrue(os.path.exists(MP4_FILE_VOD_HLS_DIR_PATH))
        self.assertTrue(os.path.exists(MP4_FILE_VOD_FLV_FILE_PATH))
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(
                os.path.exists(MP4_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH))
            self.assertTrue(
                os.path.exists(MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH))


@unittest.skip('only manual')
class TestNginxRtmpPublishPerformance(ResourcesNAS, unittest.TestCase):
    def setUp(self):
        # type: () -> None
        super(TestNginxRtmpPublishPerformance, self).setUp()
        self.__clean_init_files()

    def tearDown(self):
        # type: () -> None
        super(TestNginxRtmpPublishPerformance, self).tearDown()
        self.__clean_init_files()

    def __clean_init_files(self):
        # type: () -> None
        for i in range(10000):
            path = self.replace_string_file_id(MP4_FILE_RECORD_HLS_DIR_PATH, i)
            if os.path.exists(path):
                shutil.rmtree(path)
            path = self.replace_string_file_id(MP4_FILE_RECORD_FLV_FILE_PATH,
                                               i)
            if os.path.exists(path):
                os.remove(path)
            path = self.replace_string_file_id(MP4_FILE_VOD_HLS_DIR_PATH, i)
            if os.path.exists(path):
                shutil.rmtree(path)
            path = self.replace_string_file_id(MP4_FILE_VOD_FLV_FILE_PATH, i)
            if os.path.exists(path):
                os.remove(path)
            if APP_STORAGE_TYPE == 'NAS':
                path = self.replace_string_file_id(
                    MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH, i)
                if os.path.exists(path):
                    shutil.rmtree(path)
                path = self.replace_string_file_id(
                    MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH, i)
                if os.path.exists(path):
                    os.remove(path)

    def make_rtmp_url(self, index):
        # type: (int) -> str
        url_params = '?meeting_id=%s&file_id=%s' % \
                (RTMP_MEETING_ID, UPLOAD_MP4_FILE_ID + str(index))  # type: str
        url = '%s/live/%s%s' % \
            (RTMP_ROOT_URL, index, url_params)  # type: str
        return url

    def replace_string_file_id(self, string, index):
        # type: (str, int) -> str
        result = string.replace(UPLOAD_MP4_FILE_ID,
                                UPLOAD_MP4_FILE_ID + str(index))
        return result

    def test_publish_live_more_and_long_time_1(self):
        # type: () -> None
        """10ffmpeg每10推，不规则，检查录制文件是否存在"""
        count = 10
        per_count = 10
        thread_list = []
        for i in range(count):
            urls = []
            for j in range(per_count):
                urls.append(self.make_rtmp_url(i * 100 + j))
            t = threading.Thread(
                target=publish_to_nginx_rtmp,
                args=(SRC_LONG_MP4_PATH, urls),
                kwargs={'timeout': 10 + i * per_count})
            t.setDaemon(True)
            t.start()
            thread_list.append(t)
            time.sleep(2)

        lmap(X.call('join'), thread_list)
        time.sleep(count * per_count)

        error_count = 0
        for i in range(count):
            for j in range(per_count):
                path_list = [
                    self.replace_string_file_id(MP4_FILE_VOD_HLS_DIR_PATH,
                                                i * 100 + j),
                    self.replace_string_file_id(MP4_FILE_VOD_FLV_FILE_PATH,
                                                i * 100 + j),
                ]
                if APP_STORAGE_TYPE == 'NAS':
                    path_list += [
                        self.replace_string_file_id(
                            MP4_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH,
                            i * 100 + j),
                        self.replace_string_file_id(
                            MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH,
                            i * 100 + j),
                    ]
                for path in path_list:
                    if not os.path.exists(path):
                        error_count += 1
                        print("error path is: %s" % (path, ))

        if error_count > 0:
            self.assertTrue(False, "can not find path count %d" % error_count)

    def test_publish_live_more_and_long_time_2(self):
        # type: () -> None
        """ 针对长时间推流场景进行测试
        10ffmpeg每2推，规则600秒，还要检查是否中断过
        每2秒起1ffmpeg，结束后检查录制文件时长（从WEB接口）
        """
        count = 10
        per_count = 2
        time_lenght = 600
        thread_list = []
        for i in range(count):
            urls = []
            for j in range(per_count):
                urls.append(self.make_rtmp_url(i * 100 + j))
            t = threading.Thread(
                target=publish_to_nginx_rtmp,
                args=(SRC_LONG_MP4_PATH, urls),
                kwargs={'timeout': time_lenght})
            t.setDaemon(True)
            t.start()
            thread_list.append(t)
            time.sleep(2)

        lmap(X.call('join'), thread_list)
        time.sleep(count * per_count * time_lenght / 30)

        error_count = 0
        for i in range(count):
            for j in range(per_count):
                path_list = [
                    self.replace_string_file_id(MP4_FILE_VOD_HLS_DIR_PATH,
                                                i * 100 + j),
                    self.replace_string_file_id(MP4_FILE_VOD_FLV_FILE_PATH,
                                                i * 100 + j),
                ]
                if APP_STORAGE_TYPE == 'NAS':
                    path_list += [
                        self.replace_string_file_id(
                            MP4_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH,
                            i * 100 + j),
                        self.replace_string_file_id(
                            MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH,
                            i * 100 + j),
                    ]
                for path in path_list:
                    if not os.path.exists(path):
                        error_count += 1
                        print("error path is: %s" % (path, ))

        if error_count > 0:
            self.assertTrue(False, "can not find path count %d" % error_count)

        error_count = 0
        for i in range(count):
            for j in range(per_count):
                file_id = self.replace_string_file_id(UPLOAD_MP4_FILE_ID,
                                                      i * 100 + j)
                params = {
                    'action_type': 'info_record_file',
                    'file_id': file_id,
                    'file_type': 'm3u8',
                }
                r = requests.get(INFO_RECORD_FILE_URL, json=params)
                if r.status_code == 200:
                    info = r.json()
                    if info['error_code'] == 0:
                        if info['record_time_lenght'] < time_lenght - 30:
                            error_count += 1
                            print("%s limit time is: %s and %s" %
                                  (file_id, info['record_time_lenght'],
                                   time_lenght))
                    else:
                        error_count += 1
                        print(
                            "%s error_code: %s, error_info: %s" %
                            (file_id, info['error_code'], info['error_info']))
                else:
                    error_count += 1
                    print(
                        "%s status_code error: %s" % (file_id, r.status_code))
        if error_count > 0:
            self.assertTrue(
                False, "can not pass limit time count %d" % (error_count, ))
