# coding: utf-8

from __future__ import print_function

import errno
import http.client
import io
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

import core.logger

MAX_ATTEMPTS = 30
HTTP_DELAY_SECONDS_MULTIPLIER = 2
CHUNK_SIZE_BYTES = 1024 * 100

_logger = core.logger.Logger('Network')


def getUrl(url, parametersDict=None, verbose=False):
    url = url.replace('https://', 'http://')

    parametersBytes = None
    representation = '[{}] {}'.format('POST' if parametersDict else 'GET', url)
    if parametersDict:
        parametersString = urllib.parse.urlencode(parametersDict)
        parametersBytes = parametersString.encode('utf-8')
        representation += '?{}'.format(parametersString)

    attempt = 0
    if verbose:
        _logger.info('Loading {}'.format(representation))
    while True:
        try:
            retry = False
            lastException = None
            attempt += 1
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor)
            srcObj = opener.open(url, parametersBytes)
            dstObj = io.BytesIO()
            while True:
                chunk = srcObj.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                dstObj.write(chunk)
            dstObj.seek(0)
            srcObj.close()
            if verbose:
                _logger.info('Finished {}'.format(representation))
            return dstObj.read()
        except urllib.error.HTTPError as ex:
            if ex.code == http.client.INTERNAL_SERVER_ERROR:
                retry = attempt <= 3
            elif ex.code in (http.client.NOT_FOUND, http.client.REQUESTED_RANGE_NOT_SATISFIABLE):
                raise
            lastException = ex
        except urllib.error.URLError as ex:
            try:
                errorCode = ex.args[0].errno
                if errorCode == errno.ECONNREFUSED:
                    retry = attempt <= 3
            except:
                pass
            lastException = ex
        except ssl.CertificateError:
            raise
        except Exception as ex:
            retry = False
            lastException = ex
        if retry and attempt <= MAX_ATTEMPTS:
            _logger.info('Restarting ({}/{}) {}'.format(attempt, MAX_ATTEMPTS, representation))
            time.sleep(attempt * HTTP_DELAY_SECONDS_MULTIPLIER)
            continue
        raise lastException
