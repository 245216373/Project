# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from typing import cast, Dict, Any
import logging
import traceback
import uuid
import time
import json
import re
import os

from flask import Flask, request, jsonify, make_response, redirect, abort
from flask_cors import CORS
import requests

from crlib.env import env

from record_manager import VodManagerFactory
from upload_file_complete import upload_file_completer
from transcode import transcoder
from cut import cutter
from merge import merger
from storage import storage

LOGGER = logging.getLogger(__name__)

app_public = Flask(__name__)
app_public.debug = True

CORS(app_public, resources=r'/*')


@app_public.route("/<int:meeting_id>", methods=["GET", "POST"])  # type: ignore
@app_public.route("/", methods=["GET", "POST"])  # type: ignore
def app_meeting_view(meeting_id=''):
    # type: (str) -> Dict[str, Any]
    request_id = str(uuid.uuid4()).replace('-', '')
    body = request.get_json(silent=True)
    LOGGER.debug(
        '[%s] %s request body is: %s' % (meeting_id, request_id, body))

    try:
        action_type = body['action_type']
        processor = MeetingProcessorFactory.make(request_id, meeting_id,
                                                 action_type, body)
        result_body = processor.process()
    except Exception:
        LOGGER.error(traceback.format_exc())
        result_body = {'error_code': -1, 'error_info': 'UNKOWN_ERROR'}
    LOGGER.debug(
        '[%s] %s result body is: %s' % (meeting_id, request_id, result_body))
    return cast(Dict[str, Any], jsonify(result_body))


class MeetingProcessorInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def process(self):
        # type: () -> Dict[str, Any]
        pass


class MeetingProcessorImplement(MeetingProcessorInterface):
    def __init__(self, request_id, meeting_id, action_type, body):
        # type: (str, str, str, Dict[str, str]) -> None
        super(MeetingProcessorImplement, self).__init__()
        self.request_id = request_id
        self.meeting_id = meeting_id
        self.action_type = action_type
        self.body = body
        self.vod_manager = VodManagerFactory.make(
            self.meeting_id, file_id=self.record_file_id)

    @property
    def record_file_id(self):
        # type: () -> str
        # return self.body['file_id']
        return self.body.get('file_id')

    @property
    def BUSINESS_APP_SERVER_URL(self):
        # type: () -> str
        return cast(str, env.get('BUSINESS_APP_SERVER_URL'))

    def process(self):
        # type: () -> Dict[str, Any]
        LOGGER.debug('[%s] %s process action %s' %
                     (self.meeting_id, self.request_id, self.action_type))
        func_map = {
            'info_record_file': self.process_info_record_file,
            'delete_record_file': self.process_delete_record_file,
            'transcode_upload_file': self.process_transcode_upload_file,
            'cut_vod_file': self.process_cut_vod_file,
            'merge_vod_file': self.process_merge_vod_file,
        }
        if self.action_type in func_map:
            return func_map[self.action_type]()
        else:
            LOGGER.error('[%s] %s unknow action type %s' %
                         (self.meeting_id, self.request_id, self.action_type))
            raise ValueError('unknow action type')

    def process_info_record_file(self):
        # type: () -> Dict[str, Any]
        if not self.vod_manager.is_vod_file_exists():
            LOGGER.error(
                '[%s] %s void file %s not exists' %
                (self.meeting_id, self.request_id, self.record_file_id))
            raise IOError
        vod_info = self.vod_manager.vod_info
        result = {
            'error_code': 0,
            'error_info': '',
        }
        result.update(vod_info)
        return result

    def process_delete_record_file(self):
        # type: () -> Dict[str, Any]
        if not self.vod_manager.is_vod_file_exists():
            raise IOError
        self.vod_manager.delete_vod_file()

        result = {
            'error_code': 0,
            'error_info': '',
        }
        return result

    def process_transcode_upload_file(self):
        # type: () -> Dict[str, Any]
        def callback_ok():
            # type: () -> None
            LOGGER.debug('[%s] %s task_id %s callback_ok' %
                         (self.meeting_id, self.request_id, task_id))
            body = {
                "error_code": 0,
                'error_info': '',
                'task_id': task_id,
                "file_id": file_id,
                "file_type": file_type,
            }
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_transcode_file_done',
            }
            data.update(body)
            vod_manager = VodManagerFactory.make(
                self.meeting_id, file_id=transcode_args['file_id'])
            data.update(vod_manager.vod_info)
            LOGGER.debug('Transcode info is %s' % (data,))
            requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        def callback_error():
            # type: () -> None
            LOGGER.debug('[%s] %s task_id%s callback_error' %
                         (self.meeting_id, self.request_id, task_id))
            body = {
                'error_code': -1,
                'error_info': 'UNKOWN_ERROR',
                'task_id': task_id,
                "file_id": file_id,
                "file_type": file_type,
            }
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_transcode_file_done',
            }
            data.update(body)
            requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        file_id = self.body.get('file_id', '')
        file_type = self.body.get('file_type', '')
        if not file_id:
            abort(404)
        filename = file_id + '.' + file_type
        upload_path = env.get('APP_UPLOAD_ROOT_PATH')
        vod_path = env.get('APP_VOD_ROOT_PATH')

        task_id = self.body.get('task_id')
        if not task_id:
            task_id = str(uuid.uuid4()).replace('-', '')
        transcode_args_str = self.body.get('transcode_args', '{}')
        transcode_args = json.loads(transcode_args_str)  # type: Dict[str, Any]
        if 'file_id' not in transcode_args:
            transcode_args['file_id'] = str(uuid.uuid4()).replace('-', '')
        transcoder.submit_task(task_id, file_id, file_type, filename,
                               upload_path, vod_path, transcode_args,
                               callback_ok, callback_error)
        result_body = {
            '_id': self.request_id,
            'task_id': task_id,
            "error_code": 0,
            "error_info": "",
        }
        return result_body

    def process_cut_vod_file(self):
        # type: () -> Dict[str, Any]
        def callback_ok():
            # type: () -> None
            LOGGER.debug('[%s] %s task_id %s callback_ok' %
                         (self.meeting_id, self.request_id, task_id))
            body = {
                "error_code": 0,
                'error_info': '',
                'task_id': task_id,
                "file_id": file_id,
                "file_type": file_type,
                'source_fileid': source_fileid,
                "source_url": source_url,
                "addition": addition,
                'file_name': file_name,
            }
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_cut_vod_file_done',
            }
            data.update(body)
            vod_manager = VodManagerFactory.make(
                self.meeting_id, file_id=cut_args['file_id'])
            data.update(vod_manager.vod_info)
            LOGGER.debug('cut info is %s' % (data, ))
            requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        def callback_error():
            # type: () -> None
            LOGGER.debug('[%s] %s task_id%s callback_error' %
                         (self.meeting_id, self.request_id, task_id))
            body = {
                'error_code': -1,
                'error_info': 'UNKOWN_ERROR',
                'task_id': task_id,
                "file_id": file_id,
                "file_type": file_type,
                "addition": addition,
                'file_name': file_name,
            }
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_cut_vod_file_done',
            }
            data.update(body)
            requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        APP_VOD_PALY_URL = env.get('APP_VOD_PALY_URL')

        file_id = self.body.get('file_id', '')
        if not file_id:
            abort(404)
        file_type = self.body.get('file_type', '')

        source_fileid = file_id
        source_url = '%s/%s/index.%s' % (APP_VOD_PALY_URL, file_id, file_type)

        filename = file_id + '.' + file_type
        vod_path = env.get('APP_VOD_ROOT_PATH')

        task_id = self.body.get('task_id')
        if not task_id:
            task_id = str(uuid.uuid4()).replace('-', '')
        # cut_args_str = self.body.get('cut_args', '{}')
        # cut_args = json.loads(cut_args_str)  # type: Dict[str, Any]
        cut_args = self.body.get('cut_args', '{}')
        file_name = cut_args.get('file_name')
        LOGGER.debug('file_name is %s, cut_args is %s' % (file_name, cut_args))
        # 接收附加参数addition
        addition = self.body.get('addition')

        if 'file_id' not in cut_args:
            cut_args['file_id'] = str(uuid.uuid4()).replace('-', '')

        cutter.submit_task(task_id, file_id, file_type, filename, vod_path,
                           cut_args, callback_ok, callback_error)
        result_body = {
            '_id': self.request_id,
            'task_id': task_id,
            "error_code": 0,
            "error_info": "",
        }
        return result_body

    def process_merge_vod_file(self):
        # type: () -> Dict[str, Any]
        def callback_ok():
            # type: () -> None
            LOGGER.debug('[%s] %s task_id %s callback_ok' %
                         (self.meeting_id, self.request_id, task_id))
            body = {
                "error_code": 0,
                'error_info': '',
                'task_id': task_id,
                "file_id": merge_args['file_id'],
                "file_type": merge_args['file_type'],
                "addition": addition,
            }
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_merge_vod_file_done',
            }
            data.update(body)
            vod_manager = VodManagerFactory.make(
                self.meeting_id, file_id=merge_args['file_id'])
            data.update(vod_manager.vod_info)
            LOGGER.debug('Merge info is %s' % (data,))
            requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        def callback_error():
            # type: () -> None
            LOGGER.debug('[%s] %s task_id%s callback_error' %
                         (self.meeting_id, self.request_id, task_id))
            body = {
                'error_code': -1,
                'error_info': 'UNKOWN_ERROR',
                'task_id': task_id,
                # "file_id": file_id,
                # "file_type": file_type,
                "addition": addition,
            }
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_merge_vod_file_done',
            }
            data.update(body)
            requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        # file_id = self.body.get('file_id', '')
        # if not file_id:
        #     abort(404)
        # file_type = self.body.get('file_type', '')
        # filename = file_id + '.' + file_type
        vod_path = env.get('APP_VOD_ROOT_PATH')

        # 接收附加参数addition
        addition = self.body.get('addition', {})

        task_id = self.body.get('task_id')
        if not task_id:
            task_id = str(uuid.uuid4()).replace('-', '')
        # merge_args_str = self.body.get('merge_args', '{}')
        # merge_args = json.loads(merge_args_str)  # type: Dict[str, Any]

        merge_args = self.body.get('merge_args', {})
        merge_files = self.body.get('merge_files', {})
        if 'file_id' not in merge_args:
            merge_args['file_id'] = str(uuid.uuid4()).replace('-', '')
        #merger.submit_task(task_id, file_id, file_type, filename, vod_path,
        #                   merge_args, callback_ok, callback_error)

        LOGGER.debug('merge_args is %s, merge_files is %s' % (merge_args, merge_files))

        merger.submit_task(task_id, vod_path, merge_args, merge_files, callback_ok, callback_error)
        result_body = {
            '_id': self.request_id,
            'task_id': task_id,
            "error_code": 0,
            "error_info": "",
        }
        # result_body.update({'file_id': file_id, 'file_type': file_type})
        result_body.update({'file_id': merge_args['file_id'], 'file_type': merge_args['file_type']})
        return result_body


class MeetingProcessorFactory(object):

    @classmethod
    def make(cls, request_id, meeting_id, action_type, body):
        # type: (str, str, str, Dict[str, str]) -> MeetingProcessorInterface
        o = MeetingProcessorImplement(request_id, meeting_id, action_type,
                                      body)  # type: MeetingProcessorInterface
        assert isinstance(o, MeetingProcessorInterface)
        return o


@app_public.route("/upload/check", methods=["POST"])  # type: ignore
def app_upload_accept_check_view():
    # type: () -> ignore
    request_id = str(uuid.uuid4()).replace('-', '')

    upload_path = env.get("APP_UPLOAD_ROOT_PATH")
    fileMd5 = request.form.get('fileMd5')
    chunk = request.form.get('chunk', 0)
    file_slice_name = "%s%s" % (fileMd5, chunk)
    file_slice_path = upload_path + '/' + file_slice_name
    LOGGER.debug('fileMd5 is %s, file_slice_path is %s' % (fileMd5, file_slice_path))

    if os.path.exists(file_slice_path):
        result_body = {"_id": request_id, "error_code": 1, "error_info": "exists"}
    else:
        result_body = {"_id": request_id, "error_code": 0, "error_info": ""}

    response = make_response(jsonify(result_body))  # type: ignore
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


@app_public.route("/upload/accept", methods=["POST"])  # type: ignore
def app_upload_accept_view():
    # type: () -> ignore
    request_id = str(uuid.uuid4()).replace('-', '')
    upload_file = request.files['file']
    # task_id = request.form.get('task_id')
    fileMd5 = request.form.get('fileMd5')
    LOGGER.debug('fileMd5 is %s ' % (fileMd5, ))
    chunk = request.form.get('chunk', 0)
    # filename = '%s%s' % (task_id, chunk)
    filename = '%s%s' % (fileMd5, chunk)
    upload_file.save('%s/%s' % (env.get('APP_UPLOAD_ROOT_PATH'), filename))
    result_body = {"_id": request_id, "error_code": 0, "error_info": ""}

    response = make_response(jsonify(result_body))  # type: ignore
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


@app_public.route("/upload/complete", methods=["GET"])  # type: ignore
def app_upload_complete_view():
    # type: () -> ignore
    BUSINESS_APP_SERVER_URL = env.get('BUSINESS_APP_SERVER_URL')  # type: str
    request_id = str(uuid.uuid4()).replace('-', '')

    def callback_ok():
        # type: () -> None
        LOGGER.debug('%s task_id %s callback_ok' % (request_id, task_id))
        body = {
            "error_code": 0,
            'error_info': '',
            'task_id': task_id,
            "file_id": file_id,
            "file_type": file_type,
        }
        data = {
            '_id': request_id,
            't': int(float(time.time())),
            'sign_type': 'md5',
            'sign': '00000000000000000000000000000000',
            'nonce': '123456',
            'event_type': 'notify_update_file_done',
        }
        data.update(body)
        LOGGER.debug('complete data is %s' % (data, ))
        requests.post(BUSINESS_APP_SERVER_URL, json=data, timeout=60)

    def callback_error():
        # type: () -> None
        LOGGER.debug('%s task_id %s callback_error' % (request_id, task_id))
        body = {
            'error_code': -1,
            'error_info': 'UNKOWN_ERROR',
            'task_id': task_id,
            "file_id": file_id,
            "file_type": file_type,
        }
        data = {
            '_id': request_id,
            't': int(float(time.time())),
            'sign_type': 'md5',
            'sign': '00000000000000000000000000000000',
            'nonce': '123456',
            'event_type': 'notify_update_file_done',
        }
        data.update(body)
        requests.post(BUSINESS_APP_SERVER_URL, json=data, timeout=60)

    origin_filename = request.args.get('file_id').strip()
    file_id = str(uuid.uuid4()).replace('-', '')
    if not origin_filename:
        origin_filename = file_id
    file_type = request.args.get('file_type')
    compid = request.args.get('compid')

    target_filename = file_id + '.' + file_type
    task_id = request.args.get('task_id')
    upload_path = env.get('APP_UPLOAD_ROOT_PATH')
    target_file_path = '%s/%s' % (upload_path, target_filename)

    auto_transcode = request.args.get('auto_transcode')
    meeting_id = request.args.get('meeting_id')

    upload_file_completer.submit_task(task_id, target_filename,
                                      target_file_path, upload_path,
                                      callback_ok, callback_error)

    upload_file_path = upload_path + '/' + target_filename

    def AutoTranscode():

        LOGGER.debug('Enter autotranscode !!!')

        def callback_ok():
            # type: () -> None

            upload_filename = file_id + '.' + file_type
            upload_file_path = '/' + 'upload' + "/" + upload_filename

            body = {
                "error_code": 0,
                'error_info': '',
                'task_id': task_id,
                "file_id": file_id,
                "file_type": 'm3u8',
                "compid" : compid,
                "filename" : origin_filename,
                "base_url" : upload_file_path,
                "source_type": source_type,
            }
            data = {
                '_id': request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_transcode_file_done',
            }
            data.update(body)
            vod_manager = VodManagerFactory.make(
                meeting_id, file_id=transcode_args['file_id'])
            data.update(vod_manager.vod_info)
            LOGGER.debug('Transcode data is %s' % (data, ))
            requests.post(BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        def callback_error():
            # type: () -> None

            body = {
                'error_code': -1,
                'error_info': 'UNKOWN_ERROR',
                'task_id': task_id,
                "file_id": file_id,
                "file_type": file_type,
                "source_type": source_type,
            }
            data = {
                '_id': request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'notify_transcode_file_done',
            }
            data.update(body)
            requests.post(BUSINESS_APP_SERVER_URL, json=data, timeout=60)

        transcode_args = {
            "template_type": 1,
            "s": "1280x720",
            "r": 24,
            "crf": 34,
            "file_id": file_id,
            "file_type": "m3u8",
        }

        filename = file_id + '.' + file_type
        upload_path = env.get('APP_UPLOAD_ROOT_PATH')
        vod_path = env.get('APP_VOD_ROOT_PATH')

        task_id = request.args.get('task_id')
        if not task_id:
            task_id = str(uuid.uuid4()).replace('-', '')
        if 'file_id' not in transcode_args:
            transcode_args['file_id'] = str(uuid.uuid4()).replace('-', '')
        transcoder.submit_task(task_id, file_id, file_type, filename,
                               upload_path, vod_path, transcode_args,
                               callback_ok, callback_error)

    if auto_transcode > 0:
        source_type = 1
        LOGGER.debug('Transcoding, origin_filename is %s, file_id is %s, \
        file_type is %s, upload_file_path is %s' % (
            origin_filename, file_id, file_type, upload_file_path))
        while True:
            if os.path.exists(upload_file_path):
                AutoTranscode()
                break
            time.sleep(0.5)
    else:
        source_type = ''

    result_body = {'_id': request_id, "error_code": 0, "error_info": ""}
    result_body.update({'file_id': file_id, 'file_type': file_type})

    response = make_response(jsonify(result_body))  # type: ignore
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response


@app_public.route("/upload/delete", methods=["POST"])  # type: ignore
def app_upload_delete_view():
    # type: () -> Dict[str, Any]
    request_id = str(uuid.uuid4()).replace('-', '')

    file_id = request.form.get('file_id')
    if not file_id:
        file_id = str(uuid.uuid4()).replace('-', '')
    file_type = request.form.get('file_type')
    target_filename = file_id + '.' + file_type

    # 删除上传文件
    storage.delete_upload_file(target_filename).get(timeout=600)
    result_body = {'_id': request_id, "error_code": 0, "error_info": ""}
    result_body.update({'file_id': file_id, 'file_type': file_type})
    return cast(Dict[str, Any], jsonify(result_body))


@app_public.route("/vod/<string:filename>", methods=["GET"])  # type: ignore
def app_vod_view(filename):
    # type: (str) -> ignore
    r = re.match(r'.*?:(\d+)/', request.url_root)
    # XXX: 不能假定端口是减一的
    port = int(r.group(1)) if r else 80
    re_url = str(request.url).replace(":%d/" % port,
                                      ":%d/" % (port - 1))  # type: str

    vod_path = env.get('APP_VOD_ROOT_PATH')
    if filename[-5:] == '.m3u8':
        file_id = filename[:-5]
        if not storage.is_vod_dir_exists(file_id).get(timeout=60):
            abort(404)
        storage.get_vod_dir(file_id, vod_path + '/' + file_id).get(timeout=600)
        re_url = re_url.replace(filename, '%s/index.m3u8' % (file_id, ))
    elif filename[-4:] == '.flv':
        file_id = filename[:-4]
        if not storage.is_vod_file_exists(filename).get(timeout=60):
            abort(404)
        storage.get_vod_file(filename,
                             vod_path + '/' + filename).get(timeout=600)

    return redirect(re_url)
