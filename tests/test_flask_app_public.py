# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import os
import time
import shutil
import unittest
import json

import requests

from .resources import (
    APP_UPLOAD_ROOT_PATH,
    APP_STORAGE_TYPE,
    SRC_MP4_PATH,
    SRC_MP4_SIZE,
    UPLOAD_MP4_FILE_TYPE,
    UPLOAD_MP4_FILE_ID,
    MP4_FILE_UPLOAD_PATH,
    SRC_HLS_PATH,
    SRC_HLS_FILE_ID,
    SRC_HLS_FILE_TYPE,
    SRC_HLS_VOD_DIR_PATH,
    TRANSCODE_HLS_FILE_ID,
    TRANSCODE_HLS_VOD_DIR_PATH,
    CUT_HLS_FILE_TYPE,
    CUT_HLS_FILE_ID,
    CUT_HLS_VOD_DIR_PATH,
    MERGE_HLS_FILE_ID,
    MERGE_HLS_FILE_TYPE,
    MERGE_HLS_VOD_DIR_PATH,
    UPLOAD_ACCEPT_URL,
    UPLOAD_COMPLETE_URL,
    UPLOAD_DELETE_URL,
    TRANSCODE_URL,
    CUT_URL,
    MERGE_URL,
    MP4_FILE_UPLOAD_STORAGE_NAS_PATH,
    HLS_FILE_VOD_HLS_DIR_PATH,
    HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH,
    CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH,
    MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH,
    TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH,
    ResourcesNAS,
)


class TestUpload(ResourcesNAS, unittest.TestCase):
    def test_upload_mp4_file(self):
        # type: () -> None
        # 提交 ACCEPT
        files = {'file': open(SRC_MP4_PATH, 'rb')}
        values = {'task_id': '1001', 'chunk': 0}
        r = requests.post(UPLOAD_ACCEPT_URL, files=files, data=values)

        # 检查 ACCEPT 返回值
        self.assertEqual(r.status_code, 200)
        upload_file_save_path = APP_UPLOAD_ROOT_PATH + '/%s%s' % (
            values['task_id'], values['chunk'])
        self.assertTrue(os.path.exists(upload_file_save_path))

        # 提交 COMPLETE
        params = {
            'task_id': '1001',
            'file_id': UPLOAD_MP4_FILE_ID,
            'file_type': UPLOAD_MP4_FILE_TYPE,
        }
        r = requests.get(UPLOAD_COMPLETE_URL, params=params)
        self.assertEqual(r.status_code, 200)

        # 等待文件合并完成
        time.sleep(0.1)

        self.assertFalse(os.path.exists(upload_file_save_path))

        # 检查对应的文件是否在文件存储中心
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(os.path.exists(MP4_FILE_UPLOAD_STORAGE_NAS_PATH))
            self.assertEqual(
                os.path.getsize(MP4_FILE_UPLOAD_STORAGE_NAS_PATH),
                SRC_MP4_SIZE)

        # 检测删除接口是否可用
        values = {
            'file_id': UPLOAD_MP4_FILE_ID,
            'file_type': UPLOAD_MP4_FILE_TYPE
        }
        r = requests.post(UPLOAD_DELETE_URL, data=values)

        # 检查 DELETE 返回值
        self.assertEqual(r.status_code, 200)
        if APP_STORAGE_TYPE == 'NAS':
            self.assertFalse(os.path.exists(MP4_FILE_UPLOAD_STORAGE_NAS_PATH))

    def test_upload_mp4_file_with_twice_upload(self):
        # type: () -> None
        # 提交 ACCEPT
        files = {'file': open(SRC_MP4_PATH, 'rb')}
        values = {'task_id': '1001', 'chunk': 0}
        r = requests.post(UPLOAD_ACCEPT_URL, files=files, data=values)

        # 检查 ACCEPT 返回值
        self.assertEqual(r.status_code, 200)
        upload_file_save_path = APP_UPLOAD_ROOT_PATH + '/%s%s' % (
            values['task_id'], values['chunk'])
        self.assertTrue(os.path.exists(upload_file_save_path))

        # 再次提交 ACCEPT
        files = {'file': open(SRC_MP4_PATH, 'rb')}
        values = {'task_id': '1001', 'chunk': 1}
        r = requests.post(UPLOAD_ACCEPT_URL, files=files, data=values)

        # 检查 ACCEPT 返回值
        self.assertEqual(r.status_code, 200)
        upload_file_save_path = APP_UPLOAD_ROOT_PATH + '/%s%s' % (
            values['task_id'], values['chunk'])
        self.assertTrue(os.path.exists(upload_file_save_path))

        # 提交 COMPLETE
        params = {
            'task_id': '1001',
            'file_id': UPLOAD_MP4_FILE_ID,
            'file_type': UPLOAD_MP4_FILE_TYPE,
        }
        r = requests.get(UPLOAD_COMPLETE_URL, params=params)
        self.assertEqual(r.status_code, 200)

        # 等待文件合并完成
        time.sleep(0.1)

        self.assertFalse(os.path.exists(upload_file_save_path))

        # 检查对应的文件是否在文件存储中心
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(os.path.exists(MP4_FILE_UPLOAD_STORAGE_NAS_PATH))
            self.assertEqual(
                os.path.getsize(MP4_FILE_UPLOAD_STORAGE_NAS_PATH),
                SRC_MP4_SIZE * 2)


class TestTranscode(ResourcesNAS, unittest.TestCase):
    def setUp(self):
        # type: () -> None
        super(TestTranscode, self).setUp()
        if APP_STORAGE_TYPE == 'NAS':
            shutil.copy(SRC_MP4_PATH, MP4_FILE_UPLOAD_STORAGE_NAS_PATH)
        else:
            shutil.copy(SRC_MP4_PATH, MP4_FILE_UPLOAD_PATH)

    def tearDown(self):
        # type: () -> None
        super(TestTranscode, self).tearDown()

    def test_mp4(self):
        # type: () -> None
        # 提交 Transcode
        transcode_args = {
            "template_type": 1,
            "s": "848x480",
            "r": 24,
            "crf": 34,
            "file_id": TRANSCODE_HLS_FILE_ID,
            "file_type": "m3u8",
        }
        values = {
            'task_id': '1001',
            'file_id': UPLOAD_MP4_FILE_ID,
            'file_type': UPLOAD_MP4_FILE_TYPE,
            'transcode_args': json.dumps(transcode_args),
            'action_type': 'transcode_upload_file',
        }
        r = requests.post(TRANSCODE_URL, json=values)

        # 检查 ACCEPT 返回值
        self.assertEqual(r.status_code, 200)

        # 等待文件从仓储中心取回完成
        time.sleep(0.1)
        self.assertTrue(os.path.exists(MP4_FILE_UPLOAD_PATH))

        # 等待文件转码完成
        time.sleep(5.0)

        # 存储中心源文件不能被删除
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(os.path.exists(MP4_FILE_UPLOAD_STORAGE_NAS_PATH))

        # VOD 是否存有转码后文件
        self.assertTrue(os.path.exists(TRANSCODE_HLS_VOD_DIR_PATH))

        # 存储中心是否存有转码后文件
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(
                os.path.exists(
                    TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH))


class TestCut(ResourcesNAS, unittest.TestCase):
    def setUp(self):
        # type: () -> None
        super(TestCut, self).setUp()

        if APP_STORAGE_TYPE == 'NAS':
            shutil.copytree(SRC_HLS_PATH,
                            HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
        else:
            shutil.copytree(SRC_HLS_PATH, HLS_FILE_VOD_HLS_DIR_PATH)

    def test_hls(self):
        # type: () -> None
        # 提交 cut
        cut_args = {
            "template_type": 1,
            "ss": 0,
            "t": 5,
            "file_id": CUT_HLS_FILE_ID,
            "file_type": CUT_HLS_FILE_TYPE,
        }
        values = {
            'task_id': '1001',
            'file_id': SRC_HLS_FILE_ID,
            'file_type': SRC_HLS_FILE_TYPE,
            'cut_args': json.dumps(cut_args),
            'action_type': 'cut_vod_file',
        }
        r = requests.post(CUT_URL, json=values)

        # 检查 ACCEPT 返回值
        self.assertEqual(r.status_code, 200)

        # 等待文件从仓储中心取回完成
        time.sleep(0.1)
        self.assertTrue(os.path.exists(SRC_HLS_VOD_DIR_PATH))

        # 等待剪切完成
        time.sleep(0.5)

        # VOD 是否存有剪切后文件
        self.assertTrue(os.path.exists(CUT_HLS_VOD_DIR_PATH))

        # 存储中心是否存有剪切后文件
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(
                os.path.exists(CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH))


class TestMergeNAS(ResourcesNAS, unittest.TestCase):
    def setUp(self):
        # type: () -> None
        super(TestMergeNAS, self).setUp()

        if APP_STORAGE_TYPE == 'NAS':
            shutil.copytree(SRC_HLS_PATH,
                            HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
        else:
            shutil.copytree(SRC_HLS_PATH, HLS_FILE_VOD_HLS_DIR_PATH)

    def test_hls(self):
        # type: () -> None
        # 提交合并
        merge_files = [{
            'file_id': SRC_HLS_FILE_ID,
            'file_type': SRC_HLS_FILE_TYPE,
        }]
        merge_args = {
            "template_type": 1,
            "file_id": MERGE_HLS_FILE_ID,
            "file_type": MERGE_HLS_FILE_TYPE,
            "merge_files": merge_files,
        }
        values = {
            'task_id': '1001',
            'file_id': SRC_HLS_FILE_ID,
            'file_type': SRC_HLS_FILE_TYPE,
            'merge_args': json.dumps(merge_args),
            'action_type': 'merge_vod_file',
        }
        r = requests.post(MERGE_URL, json=values)

        # 检查 ACCEPT 返回值
        self.assertEqual(r.status_code, 200)

        # 等待文件从仓储中心取回完成
        time.sleep(0.1)
        self.assertTrue(os.path.exists(SRC_HLS_VOD_DIR_PATH))

        # 等待合并完成
        time.sleep(0.5)

        # VOD 是否存有合并后文件
        self.assertTrue(os.path.exists(MERGE_HLS_VOD_DIR_PATH))

        # 存储中心是否存有合并后文件
        if APP_STORAGE_TYPE == 'NAS':
            self.assertTrue(
                os.path.exists(MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH))
