import json
import math
import multiprocessing
import os
import sys
import time

import raven

LEVEL_ERROR = 1
LEVEL_WARNING = 2
LEVEL_INFO = 3
LEVEL_ALL = 10

_LEVEL_STRING = {
    LEVEL_WARNING: '[WARNING]',
    LEVEL_ERROR: '[ERROR]',
    LEVEL_INFO: '',
}

STDERR_LOCK = multiprocessing.Lock()


class Logger(object):
    def __init__(self, loggerId):
        with open(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'config.json')) as fobj:
            self.sentry = raven.Client(json.load(fobj)['sentry_dsn'])
        self.id = loggerId
        self.level = LEVEL_ALL
        self.baseTime = time.time()

    def info(self, message):
        self.write(message, LEVEL_INFO)

    def warning(self, message):
        self.write(message, LEVEL_WARNING)

    def error(self, message):
        self.write(message, LEVEL_ERROR)

    def write(self, message, level):
        if level == LEVEL_WARNING or level == LEVEL_ERROR:
            self.sentry.captureMessage(message)
        if self.level >= level:
            timeDiff = time.time() - self.baseTime
            logEntry = '[{:0>8}] [{}] {: <10}{: >10} {}'.format(
                os.getpid(),
                '{}.{:0>3}'.format(time.strftime('%H:%M:%S', time.gmtime(timeDiff)), str(round(math.modf(timeDiff % 1000)[0], 3)).replace('0.', '')),
                self.id,
                _LEVEL_STRING[level],
                message,
            )
            if not getattr(sys, 'frozen', False):
                with STDERR_LOCK:
                    sys.stderr.write(logEntry + '\n')
                    sys.stderr.flush()
