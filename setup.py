# -*- coding: utf-8 -*-
import os
import sys
import six

from cx_Freeze import setup, Executable

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/src')  # noqa

NAME = 'live-gateway'

packages = ['idna']

if six.PY3:
    packages += ['asyncio', 'jinja2']
else:
    packages += ['gevent.builtins']

build_options = {
    "packages": packages,
    "excludes": [],
    "include_files": [],
    "include_msvcr": True,
}

executables = [Executable('src/main.py', targetName=NAME)]

setup(
    name=NAME,
    description='Live Gateway',
    options=dict(build_exe=build_options),
    executables=executables)
