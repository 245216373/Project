# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa
from typing import *  # noqa
from abc import ABCMeta, abstractmethod  # noqa

import _patch_all  # noqa

import logging
import traceback
import sys
import time

from app import AppAsyncFactory
from app_monitor import AppMonitorAsyncFactory

LOGGER = logging.getLogger(__name__)


def main():
    # type: () -> None
    try:
        app = AppAsyncFactory.make()
        app.run()
        AppMonitorAsyncFactory.make(app).run()
        while True:
            time.sleep(60)
    except Exception:
        LOGGER.critical(traceback.format_exc())
        LOGGER.warning('will quit 90 s later')
        time.sleep(90)
        sys.exit(-1)


if __name__ == "__main__":
    main()
