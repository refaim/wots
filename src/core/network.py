# coding: utf-8

from __future__ import print_function

import httplib
import StringIO
import time
import urllib2

import logger

MAX_ATTEMPTS = 30
HTTP_DELAY_SECONDS = 1
CHUNK_SIZE_BYTES = 1024 * 100

_logger = logger.Logger('Network')


def getUrl(url):
    attempt = 0
    _logger.info('Loading [GET] {}'.format(url))
    while True:
        try:
            attempt += 1
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor)
            srcObj = opener.open(url)
            dstObj = StringIO.StringIO()
            while True:
                chunk = srcObj.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                dstObj.write(chunk)
            dstObj.seek(0)
            srcObj.close()
            _logger.info('Finished [GET] {}'.format(url))
            return dstObj.read()
        except urllib2.HTTPError, ex:
            if ex.code == httplib.NOT_FOUND:
                raise
        except Exception:
            if attempt <= MAX_ATTEMPTS:
                _logger.info('Restarting ({}/{}) [GET] {}'.format(attempt, MAX_ATTEMPTS, url))
                time.sleep(HTTP_DELAY_SECONDS)
                continue
            raise
