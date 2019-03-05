# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from typing import cast, Dict, Any
import logging
import traceback
import uuid
import time
import hashlib

from toolz import keyfilter
import requests
from flask import Flask, request, jsonify

from crlib.env import env

from record_manager import RecorderFactory, VodManagerFactory

LOGGER = logging.getLogger(__name__)

app_nginx_rtmp = Flask(__name__)
app_nginx_rtmp.debug = True


@app_nginx_rtmp.route("/nginx_callback", methods=["POST"])  # type: ignore
def app_nginx_callback_view():
    # type: () -> str
    request_id = str(uuid.uuid4()).replace('-', '')
    forms = request.form.to_dict()  # type: Dict[str, str]
    LOGGER.debug('[None] %s recv forms is %s' % (request_id, forms))
    processor = NotifyProcessorFactory.make(request_id, forms)
    processor.process()
    return ''


@app_nginx_rtmp.route(  # type: ignore
    "/web_simulator", methods=["POST", "GET"])
def app_web_simulator_view():
    # type: () -> Dict[str, Any]
    body = request.get_json(silent=True)
    LOGGER.debug('simulator recv body: %s' % (body, ))
    return cast(Dict[str, Any], jsonify({'error_code': 0, 'error_info': ''}))


class NotifyProcessorInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def process(self):
        # type: () -> None
        pass


class NotifyProcessorImplement(NotifyProcessorInterface):
    def __init__(
            self,
            request_id,  # type: str
            notify_type,  # type: str
            channel_id,  # type: str
            meeting_id,  # type: str
            other_params,  # type: Dict[str, str]
    ):
        # type: (...) -> None
        self.request_id = request_id
        self.notify_type = notify_type
        self.channel_id = channel_id
        self.meeting_id = meeting_id
        self.other_params = other_params
        self.recoder = RecorderFactory.make(channel_id, meeting_id,
                                            other_params.get('file_id'))
        self.vod_manager = VodManagerFactory.make(
            self.meeting_id, file_id=self.recoder.file_id)

    @property
    def APP_LIVE_NEED_AUTH_PUBLISH(self):
        # type: () -> bool
        r = env.get('APP_LIVE_NEED_AUTH_PUBLISH', default=False, type_=bool)
        return cast(bool, r)

    @property
    def BUSINESS_APP_SERVER_URL(self):
        # type: () -> str
        return cast(str, env.get('BUSINESS_APP_SERVER_URL'))

    @property
    def BUSINESS_APP_NEED_AUTH_PUBLISH(self):
        # type: () -> bool
        r = env.get(
            'BUSINESS_APP_NEED_AUTH_PUBLISH', default=False, type_=bool)
        return cast(bool, r)

    def process(self):
        # type: () -> None
        LOGGER.debug('[%s] %s process notify %s' %
                     (self.channel_id, self.request_id, self.notify_type))
        func_map = {
            'publish': self.process_publish,
            'publish_done': self.process_publish_done
        }

        LOGGER.debug('111111111111 %s ' % (func_map[self.notify_type], ))
        if self.notify_type in func_map:
            func_map[self.notify_type]()
        else:
            LOGGER.error('[%s] %s unknow notify type %s' %
                         (self.channel_id, self.request_id, self.notify_type))

    def process_publish(self):
        # type: () -> None

        if self.APP_LIVE_NEED_AUTH_PUBLISH:
            expire_t = int(self.other_params['expire_t'])
            if expire_t < time.time():
                raise ValueError(
                    "[%s] expire error %s" % (self.channel_id, expire_t))
            t_string = self.other_params.get('t', '')
            if t_string:
                t_sign_string = b'&t=' + t_string.encode()
            else:
                t_sign_string = b''
            sign_content = b'channel_id=' + self.channel_id.encode() + b'&' \
                + b'expire_t=' + str(expire_t).encode() \
                + t_sign_string \
                + b'11111111111111110000000011111111'
            dst_md5 = hashlib.md5(sign_content).hexdigest()
            if dst_md5 != self.other_params['sign']:
                raise ValueError("[%s] error sign" % (self.channel_id, ))

        if self.BUSINESS_APP_NEED_AUTH_PUBLISH:
            data = {
                '_id': self.request_id,
                't': int(float(time.time())),
                'sign_type': 'md5',
                'sign': '00000000000000000000000000000000',
                'nonce': '123456',
                'event_type': 'auth_publish',
                "channel_id": self.channel_id,
                "meeting_id": self.meeting_id,
            }
            data.update(self.other_params)
            r = requests.post(
                self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)
            if r.status_code != requests.codes.ok:
                raise ValueError(
                    "unknow server status code %s" % (r.status_code, ))
            body = r.json()
            LOGGER.debug('recv body is: %s' % (body, ))
            if body is None or body.get('error_code') != 0:
                LOGGER.error('error code is %s' % (body.get('error_code'), ))
                raise ValueError("unknow server error code %s error info %s" %
                                 (body['error_code'], body.get('error_info')))

        data = {
            '_id': self.request_id,
            't': int(float(time.time())),
            'sign_type': 'md5',
            'sign': '00000000000000000000000000000000',
            'nonce': '123456',
            'event_type': 'notify_publish',
            "channel_id": self.channel_id,
            "meeting_id": self.meeting_id,
        }
        data.update(self.other_params)
        requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)
        self.recoder.create_record_dir()

    def process_publish_done(self):
        # type: () -> None
        data = {
            '_id': self.request_id,
            't': int(float(time.time())),
            'sign_type': 'md5',
            'sign': '00000000000000000000000000000000',
            'nonce': '123456',
            'event_type': 'notify_publish_done',
            "channel_id": self.channel_id,
            "meeting_id": self.meeting_id,
        }
        data.update(self.other_params)
        requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)
        self.process_record_done()

    def process_record_done(self):
        # type: () -> None
        try:
            self.recoder.transfer()
        except Exception:
            LOGGER.error(traceback.format_exc())
            body = {
                'error_code': -1,
                'error_info': 'UNKOWN_ERROR',
                "file_id": self.recoder.file_id,
                "file_type": "m3u8"
            }
        else:
            body = {
                "error_code": 0,
                'error_info': '',
                "file_id": self.recoder.file_id,
                "file_type": "m3u8"
            }
            body.update(self.vod_manager.vod_info)
        data = {
            '_id': self.request_id,
            't': int(float(time.time())),
            'sign_type': 'md5',
            'sign': '00000000000000000000000000000000',
            'nonce': '123456',
            'event_type': 'notify_record_done',
            "channel_id": self.channel_id,
            "meeting_id": self.meeting_id,
        }
        data.update(body)
        data.update(self.other_params)
        requests.post(self.BUSINESS_APP_SERVER_URL, json=data, timeout=60)

    @classmethod
    def process_notify_base_info(cls, forms):
        # type: (Dict[str, str]) -> Tuple[str, str, str]
        return (forms['call'], forms['name'], forms.get('meeting_id', ''))

    @classmethod
    def process_other_params(cls, forms):
        # type: (dict) -> dict
        la = [
            'app', 'flashver', 'swfurl', 'tcurl', 'pageurl', 'addr',
            'clientid', 'call', 'name', 'type'
        ]
        other_params = keyfilter(lambda x: x not in la, forms)  # type: dict
        return other_params


class NotifyProcessorFactory(object):
    @classmethod
    def make(cls, request_id, forms):
        # type: (str, dict) -> NotifyProcessorInterface
        notify_type, channel_id, meeting_id = \
            NotifyProcessorImplement.process_notify_base_info(forms)
        other_params = NotifyProcessorImplement.process_other_params(forms)
        o = NotifyProcessorImplement(
            request_id, notify_type, channel_id, meeting_id,
            other_params)  # type: NotifyProcessorInterface
        assert isinstance(o, NotifyProcessorInterface)
        LOGGER.debug(
            '[%s] %s create a new processor, '
            'notify_type is %s, channel_id is %s, other_params is %s' %
            (channel_id, request_id, notify_type, channel_id, other_params))
        return o
