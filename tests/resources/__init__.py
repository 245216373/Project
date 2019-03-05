# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import os
import shutil

APP_WEB_SERVER_PUBLIC_PORT = int(
    os.environ['APP_WEB_SERVER_PUBLIC_PORT'])  # type: int
APP_UPLOAD_ROOT_PATH = os.environ['APP_UPLOAD_ROOT_PATH']  # type: str
APP_RECORD_ROOT_PATH = os.environ['APP_RECORD_ROOT_PATH']  # type: str
APP_VOD_ROOT_PATH = os.environ['APP_VOD_ROOT_PATH']  # type: str
APP_STORAGE_TYPE = os.environ['APP_STORAGE_TYPE']  # type: str
APP_STORAGE_NAS_ROOT_PATH = \
    os.environ['APP_STORAGE_NAS_ROOT_PATH']  # type: str
APP_STORAGE_NAS_UPLOAD_PATH = \
    APP_STORAGE_NAS_ROOT_PATH + '/upload'  # type: str
APP_STORAGE_NAS_VOD_PATH = \
    APP_STORAGE_NAS_ROOT_PATH + '/vod'  # type: str

RES_PATH = os.path.dirname(os.path.abspath(__file__))  # type: str

SRC_MP4_PATH = RES_PATH + '/upload-src-mp4.mp4'  # type: str
SRC_MP4_SIZE = os.path.getsize(SRC_MP4_PATH)  # type: int
SRC_LONG_MP4_PATH = RES_PATH + '/upload-src-long-mp4.mp4'  # type: str
SRC_LONG_MP4_SIZE = os.path.getsize(SRC_LONG_MP4_PATH)  # type: int

UPLOAD_MP4_FILE_NAME = 'upload-mp4.mp4'  # type: str
UPLOAD_MP4_FILE_TYPE = 'mp4'  # type: str
UPLOAD_MP4_FILE_ID = 'upload-mp4'  # type: str


MP4_FILE_VOD_HLS_DIR_PATH = \
    APP_VOD_ROOT_PATH + '/' + UPLOAD_MP4_FILE_ID  # type: str
MP4_FILE_VOD_HLS_FILE_PATH = \
    MP4_FILE_VOD_HLS_DIR_PATH + '/index.m3u8'  # type: str
MP4_FILE_VOD_FLV_FILE_PATH = \
    MP4_FILE_VOD_HLS_DIR_PATH + '.flv'  # type: str
MP4_FILE_RECORD_HLS_DIR_PATH = \
    APP_RECORD_ROOT_PATH + '/' + UPLOAD_MP4_FILE_ID  # type: str
MP4_FILE_RECORD_HLS_FILE_PATH = \
    MP4_FILE_RECORD_HLS_DIR_PATH + '/index.m3u8'  # type: str
MP4_FILE_RECORD_FLV_FILE_PATH = \
    MP4_FILE_RECORD_HLS_DIR_PATH + '.flv'  # type: str

SRC_HLS_PATH = RES_PATH + '/upload-src-hls'  # type: str
SRC_HLS_SIZE = os.path.getsize(SRC_HLS_PATH)  # type: int
SRC_HLS_FILE_ID = 'upload-src-hls'  # type: str
SRC_HLS_FILE_NAME = 'index.m3u8'  # type: str
SRC_HLS_FILE_TYPE = 'm3u8'  # type: str
SRC_HLS_VOD_DIR_PATH = \
    APP_VOD_ROOT_PATH + '/' + SRC_HLS_FILE_ID  # type: str
CUT_HLS_FILE_NAME = 'index.m3u8'  # type: str
CUT_HLS_FILE_TYPE = 'm3u8'  # type: str
CUT_HLS_FILE_ID = 'upload-hls'  # type: str
CUT_HLS_VOD_DIR_PATH = \
    APP_VOD_ROOT_PATH + '/' + CUT_HLS_FILE_ID  # type: str
TRANSCODE_HLS_FILE_NAME = 'index.m3u8'  # type: str
TRANSCODE_HLS_FILE_TYPE = 'm3u8'  # type: str
TRANSCODE_HLS_FILE_ID = 'upload-hls'  # type: str
TRANSCODE_HLS_VOD_DIR_PATH = \
    APP_VOD_ROOT_PATH + '/' + TRANSCODE_HLS_FILE_ID  # type: str
MERGE_HLS_FILE_NAME = 'index.m3u8'  # type: str
MERGE_HLS_FILE_TYPE = 'm3u8'  # type: str
MERGE_HLS_FILE_ID = 'upload-hls'  # type: str
MERGE_HLS_VOD_DIR_PATH = \
    APP_VOD_ROOT_PATH + '/' + MERGE_HLS_FILE_ID  # type: str

UPLOAD_ACCEPT_URL = \
    'http://localhost:%s/upload/accept' % \
    (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str
UPLOAD_COMPLETE_URL = \
    'http://localhost:%s/upload/complete' % \
    (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str
UPLOAD_DELETE_URL = \
    'http://localhost:%s/upload/delete' % \
    (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str
TRANSCODE_URL = \
    'http://localhost:%s' % (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str
CUT_URL = \
    'http://localhost:%s' % (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str
MERGE_URL = \
    'http://localhost:%s' % (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str
INFO_RECORD_FILE_URL = \
    'http://localhost:%s' % (APP_WEB_SERVER_PUBLIC_PORT, )  # type: str

MP4_FILE_UPLOAD_PATH = \
    APP_UPLOAD_ROOT_PATH + '/' + UPLOAD_MP4_FILE_NAME  # type: str
MP4_FILE_UPLOAD_STORAGE_NAS_PATH = \
    APP_STORAGE_NAS_UPLOAD_PATH + '/' + UPLOAD_MP4_FILE_NAME  # type: str
MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH = \
    APP_STORAGE_NAS_VOD_PATH + '/' + UPLOAD_MP4_FILE_ID  # type: str
MP4_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH = \
    MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH + '/index.m3u8'  # type: str
MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH = \
    MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH + '.flv'  # type: str
HLS_FILE_VOD_HLS_DIR_PATH = \
    APP_VOD_ROOT_PATH + '/' + SRC_HLS_FILE_ID  # type: str
HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH = \
    APP_STORAGE_NAS_VOD_PATH + '/' + SRC_HLS_FILE_ID  # type: str
HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH = \
    HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH + '/index.m3u8'  # type: str
CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH = \
    APP_STORAGE_NAS_VOD_PATH + '/' + CUT_HLS_FILE_ID  # type: str
CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH = \
    CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH + '/index.m3u8'  # type: str
MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH = \
    APP_STORAGE_NAS_VOD_PATH + '/' + MERGE_HLS_FILE_ID  # type: str
MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH = \
    MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH + '/index.m3u8'  # type: str
TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH = \
    APP_STORAGE_NAS_VOD_PATH + '/' + TRANSCODE_HLS_FILE_ID  # type: str
TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_FILE_PATH = \
    TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH + \
    '/index.m3u8'  # type: str

RTMP_CHANNEL_ID = '0'  # type: str
RTMP_MEETING_ID = '12345678'  # type: str
RTMP_ROOT_URL = 'rtmp://localhost:1935'  # type: str
RTMP_ROOT_PUBLIC_URL_PARAMS = '?meeting_id=%s&file_id=%s' % \
        (RTMP_MEETING_ID, UPLOAD_MP4_FILE_ID)  # type: str
RTMP_LIVE_PUBLISH_URL = '%s/live/%s%s' % \
    (RTMP_ROOT_URL, RTMP_CHANNEL_ID, RTMP_ROOT_PUBLIC_URL_PARAMS)  # type: str
RTMP_SRC_1080TO720_PUBLISH_URL = '%s/src-1080to720/%s%s' % \
    (RTMP_ROOT_URL, RTMP_CHANNEL_ID, RTMP_ROOT_PUBLIC_URL_PARAMS)  # type: str


class Resources(object):
    def setUp(self):
        # type: () -> None
        self.__clean_init_files()

    def tearDown(self):
        # type: () -> None
        self.__clean_init_files()

    def __clean_init_files(self):
        # type: () -> None
        if os.path.exists(MP4_FILE_RECORD_HLS_DIR_PATH):
            shutil.rmtree(MP4_FILE_RECORD_HLS_DIR_PATH)
        if os.path.exists(MP4_FILE_VOD_HLS_DIR_PATH):
            shutil.rmtree(MP4_FILE_VOD_HLS_DIR_PATH)
        if os.path.exists(SRC_HLS_VOD_DIR_PATH):
            shutil.rmtree(SRC_HLS_VOD_DIR_PATH)
        if os.path.exists(CUT_HLS_VOD_DIR_PATH):
            shutil.rmtree(CUT_HLS_VOD_DIR_PATH)
        if os.path.exists(MERGE_HLS_VOD_DIR_PATH):
            shutil.rmtree(MERGE_HLS_VOD_DIR_PATH)
        if os.path.exists(TRANSCODE_HLS_VOD_DIR_PATH):
            shutil.rmtree(TRANSCODE_HLS_VOD_DIR_PATH)


class ResourcesNAS(Resources):
    def setUp(self):
        # type: () -> None
        super(ResourcesNAS, self).setUp()
        self.__clean_init_files()

        if not os.path.exists(APP_STORAGE_NAS_ROOT_PATH):
            os.mkdir(APP_STORAGE_NAS_ROOT_PATH)
        if not os.path.exists(APP_STORAGE_NAS_UPLOAD_PATH):
            os.mkdir(APP_STORAGE_NAS_UPLOAD_PATH)
        if not os.path.exists(APP_STORAGE_NAS_VOD_PATH):
            os.mkdir(APP_STORAGE_NAS_VOD_PATH)

    def tearDown(self):
        # type: () -> None
        super(ResourcesNAS, self).tearDown()
        self.__clean_init_files()

    def __clean_init_files(self):
        # type: () -> None
        if os.path.exists(MP4_FILE_UPLOAD_STORAGE_NAS_PATH):
            os.remove(MP4_FILE_UPLOAD_STORAGE_NAS_PATH)
        if os.path.exists(MP4_FILE_UPLOAD_PATH):
            os.remove(MP4_FILE_UPLOAD_PATH)
        if os.path.exists(MP4_FILE_RECORD_FLV_FILE_PATH):
            os.remove(MP4_FILE_RECORD_FLV_FILE_PATH)
        if os.path.exists(MP4_FILE_VOD_FLV_FILE_PATH):
            os.remove(MP4_FILE_VOD_FLV_FILE_PATH)
        if os.path.exists(MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH):
            os.remove(MP4_FILE_VOD_STORAGE_NAS_FLV_FILE_PATH)
        if os.path.exists(MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH):
            shutil.rmtree(MP4_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
        if os.path.exists(HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH):
            shutil.rmtree(HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
        if os.path.exists(CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH):
            shutil.rmtree(CUT_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
        if os.path.exists(MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH):
            shutil.rmtree(MERGE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
        if os.path.exists(TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH):
            shutil.rmtree(TRANSCODE_HLS_FILE_VOD_STORAGE_NAS_HLS_DIR_PATH)
