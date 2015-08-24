from __future__ import print_function

import multiprocessing
import os
import sys
import time

LEVEL_ERROR = 1
LEVEL_WARNING = 2
LEVEL_INFO = 3
LEVEL_ALL = 10

_LEVEL_STRING = {
    LEVEL_WARNING: '[WARNING]',
    LEVEL_ERROR: '[ERROR]',
    LEVEL_INFO: '',
}

_BASE_TIME = time.time()
STDERR_LOCK = multiprocessing.Lock()


class Logger(object):
    def __init__(self, loggerId):
        self.id = loggerId
        self.level = LEVEL_ALL

    def info(self, message):
        self.write(message, LEVEL_INFO)

    def warning(self, message):
        self.write(message, LEVEL_WARNING)

    def error(self, message):
        self.write(message, LEVEL_ERROR)

    def write(self, message, level):
        if self.level >= level:
            logEntry = '[{:0>4}] [{:0>7}] {: <10}{: >10} {}'.format(
                os.getpid(),
                int((time.time() - _BASE_TIME) * 1000.0),
                self.id,
                _LEVEL_STRING[level],
                message,
            )
            # with STDERR_LOCK:
            #     sys.stderr.write(logEntry + '\n')
            #     sys.stderr.flush()
