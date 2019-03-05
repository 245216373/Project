# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa
from mock import Mock, MagicMock, PropertyMock  # noqa
from pytest_mock import MockFixture  # noqa

import subprocess

import pytest

from ffmpeg_run import (FFmpegRunnerInterface, FFmpegRunnerImplement,
                        FFmpegRunnerFactory)


class TestFFmpegRunnerImplement(object):
    def test_is_implement_of_interface(self):
        # type: () -> None
        assert issubclass(FFmpegRunnerImplement, FFmpegRunnerInterface)

    @pytest.fixture(autouse=True)
    def mock_ENVs(self, mocker):
        # type: (MockFixture) -> None
        def side_effect_env_get(name, default=None, type_=None):
            # type: (str, Optional[Any], Optional[Type]) -> Any
            if name == 'FFMPEG_CMD_PATH':
                return 'ffmpeg'

        mocker.patch('ffmpeg_run.env.get', side_effect=side_effect_env_get)

    def test_run_cmd(self, mocker):
        # type: (MockFixture) -> None
        obj = FFmpegRunnerImplement()
        mock_popen = mocker.MagicMock()  # type: MagicMock
        configure_mock = {
            'communicate.return_value': ('', ''),
            'poll.return_value': 0,
        }
        mock_popen.configure_mock(**configure_mock)
        mock_Popen = mocker.patch("subprocess.Popen", return_value=mock_popen)
        obj.run_cmd([])
        mock_Popen.assert_called_once_with(['ffmpeg'],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
        mock_popen.communicate.assert_called_once()
        mock_popen.poll.assert_called_once()

    def test_run_cmd_raise_IOError_with_exit_code_eq_1(self, mocker):
        # type: (MockFixture) -> None
        obj = FFmpegRunnerImplement()
        mock_popen = mocker.MagicMock()  # type: MagicMock
        configure_mock = {
            'communicate.return_value': ('', ''),
            'poll.return_value': 1,
        }
        mock_popen.configure_mock(**configure_mock)
        mocker.patch("subprocess.Popen", return_value=mock_popen)
        with pytest.raises(IOError):
            obj.run_cmd([])

    def test_run_cmd_raise_IOError_with_timer_timeout(self, mocker):
        # type: (MockFixture) -> None
        obj = FFmpegRunnerImplement()
        mock_popen = mocker.MagicMock()  # type: MagicMock
        configure_mock = {
            'communicate.return_value': ('', ''),
            'poll.return_value': -1,
        }
        mock_popen.configure_mock(**configure_mock)
        mocker.patch("subprocess.Popen", return_value=mock_popen)

        mock_Timer_ = mocker.MagicMock()  # type: MagicMock
        mock_Timer = mocker.patch("ffmpeg_run.Timer", return_value=mock_Timer_)
        with pytest.raises(IOError):
            obj.run_cmd([])

        mock_Timer.assert_called_once_with(7200, mock_popen.kill)
        mock_Timer_.start.assert_called_once()


class TestFFmpegRunnerFactory(object):
    def test_make(self):
        # type: () -> None
        obj = FFmpegRunnerFactory.make()
        assert isinstance(obj, FFmpegRunnerInterface)
