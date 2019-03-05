# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import os
import subprocess
from threading import Timer

FFMPEG_CMD_PATH = os.environ['FFMPEG_CMD_PATH']  # type: str


def ffmpeg_run_cmd(cmd_args, timeout=30):
    # type: (List[str], int) -> None
    cmd_list = [FFMPEG_CMD_PATH] + cmd_args
    p = subprocess.Popen(
        cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timer = Timer(timeout, p.kill)
    try:
        timer.start()
        p_out, p_err = p.communicate()
        p_exit_code = p.poll()
        if p_exit_code == -9:
            pass
        elif p_exit_code != 0:
            raise IOError('ffmpeg cmd %s conv file error '
                          'p_out: %s p_err: %s returncode: %s' %
                          (cmd_list, p_out, p_err, p_exit_code))
    except Exception as e:
        raise IOError('ffmpeg conv file error %s' % (e, ))
    finally:
        timer.cancel()
