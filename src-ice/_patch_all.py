# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

try:
    from encodings import codecs  # type: ignore  # noqa
    from encodings import utf_8  # noqa
except ImportError:
    pass

import sys

from crlib.env import env

env.init(env_file=sys.argv[1])  # noqa

import crlib.patch_log  # noqa
import auto_build_slice  # noqa
