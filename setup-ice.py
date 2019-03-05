# -*- coding: utf-8 -*-
import os
import sys

from cx_Freeze import setup, Executable

sys.path.append(
    os.path.abspath(os.path.dirname(__file__)) + '/src-ice')  # noqa

NAME = 'live-gateway-ice'

build_options = {
    "packages": [],
    "excludes": [],
    "include_files": ['src-ice/Slice'],
    "include_msvcr": True,
}

executables = [Executable('src-ice/main.py', targetName=NAME)]

setup(
    name=NAME,
    description='Live Gateway Ice',
    options=dict(build_exe=build_options),
    executables=executables)
