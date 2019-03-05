# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import os

import Ice


def get_base_dir():
    # type: () -> str
    d1 = os.path.dirname(os.path.abspath(__file__))
    if d1.endswith("library.zip"):
        # cx_Freeze
        # F:\build\exe.win32-2.7\lib\library.zip
        d1 = d1[:-1 * len(r"lib\library.zip")]

    if d1.endswith("\\"):
        d1 = d1[:-1]
        d1 = d1.replace("\\", "/")

    return d1


BASE_DIR = get_base_dir()

# build Ice file
SLICE_FILE_DIR = BASE_DIR + "/Slice"
SLICE_FILE_INCLUDE_DIR = SLICE_FILE_DIR + "/include"

for file_name in os.listdir(SLICE_FILE_DIR):
    if file_name.endswith(".ice"):
        Ice.loadSlice('--underscore -I%s %s/%s' % (SLICE_FILE_INCLUDE_DIR,
                                                   SLICE_FILE_DIR, file_name))
