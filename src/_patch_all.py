# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

from gevent import monkey
monkey.patch_all()  # noqa

try:
    from encodings import codecs  # type: ignore  # noqa
    from encodings import utf_8  # noqa
except ImportError:
    pass
import argparse

from crlib.env import env

parser = argparse.ArgumentParser()
parser.add_argument('--config-file', type=str, default=None)
args = parser.parse_args()

env.init(env_file=args.config_file)  # noqa

import crlib.patch_log  # noqa
