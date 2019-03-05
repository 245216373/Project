# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import logging
from cloghandler import ConcurrentRotatingFileHandler

from .env import env

assert env.is_inited(), "Use env.init before, please!"

LOG_HAS_FILE = env.get('LOG_HAS_FILE', False, type_=bool)
LOG_LEVEL = env.get('LOG_LEVEL', 10, type_=int)
LOG_FILE_PATH = env.get('LOG_FILE_PATH', '')
LOG_FILE_MAX_MB = env.get('LOG_FILE_MB', 100, type_=int) * 1024 * 1024
LOG_FILE_BACKUP_COUNT = env.get('LOG_FILE_BACKUP_COUNT', 20, type_=int)
LOG_HAS_STREAM = env.get('LOG_HAS_STREAM', False, type_=bool)

formatter = logging.Formatter(
    '%(asctime)s %(levelname)-7s %(name)-24s %(lineno)-4s - %(message)s')

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
if LOG_HAS_FILE:
    handler = ConcurrentRotatingFileHandler(
        LOG_FILE_PATH, 'a', LOG_FILE_MAX_MB, LOG_FILE_BACKUP_COUNT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if LOG_HAS_STREAM:
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
