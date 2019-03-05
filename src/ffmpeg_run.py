# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa
from typing import cast

import logging
import traceback

from threading import Timer
import subprocess

from crlib.env import env

LOGGER = logging.getLogger(__name__)


class FFmpegRunnerInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run_cmd(self, cmd_args, timeout=7200):
        # type: (List[str], int) -> None
        pass


class FFmpegRunnerImplement(FFmpegRunnerInterface):
    def __init__(self):
        # type: () -> None
        super(FFmpegRunnerImplement, self).__init__()

    @property
    def FFMPEG_CMD_PATH(self):
        # type: () -> str
        return cast(str, env.get('FFMPEG_CMD_PATH'))

    def run_cmd(self, cmd_args, timeout=7200):
        # type: (List[str], int) -> None
        cmd_list = [self.FFMPEG_CMD_PATH] + cmd_args
        LOGGER.debug('ffmpeg cmd is: %s' % (cmd_list, ))
        p = subprocess.Popen(
            cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = Timer(timeout, p.kill)
        try:
            timer.start()
            out, err = p.communicate()
            exit_code = p.poll()
            if exit_code != 0:
                LOGGER.debug(
                    'ffmpeg cmd %s run error out:%s err:%s, returncode:%s' %
                    (cmd_list, out, err, exit_code))
                raise IOError('ffmpeg conv file error code %s' % (exit_code, ))
        except Exception as e:
            logging.error("ffmpeg cmd run error %s" % traceback.format_exc())
            raise IOError('ffmpeg conv file error %s' % (e, ))
        finally:
            timer.cancel()


# class FFmpegRunnerFactory(object):
#     @classmethod
#     def make(cls):
#         # type: () -> FFmpegRunnerInterface
#         __obj = FFmpegRunnerImplement()  # type: FFmpegRunnerInterface
#         assert isinstance(__obj, FFmpegRunnerInterface)
#         return __obj

class FFmpegRunnerFactory(object):

    @classmethod
    def make(cls):
        # type: () -> FFmpegRunnerInterface
        __obj = FFmpegRunnerImplement()  # type: FFmpegRunnerInterface
        assert isinstance(__obj, FFmpegRunnerInterface)
        return __obj