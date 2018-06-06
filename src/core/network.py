# coding: utf-8

import errno
import http
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

def httpCodeAnyOf(code, statuses):
    for candidate, _, _ in statuses:
        if code == candidate:
            return True
    return False

def getUrl(url, parametersDict=None, verbose=False, verifySsl=True):
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
        retry = False
        try:
            attempt += 1
            handlers = [urllib.request.HTTPCookieProcessor]
            if not verifySsl:
                context = ssl.create_default_context()
                context.check_hostname = False
                # noinspection PyUnresolvedReferences
                context.verify_mode = ssl.CERT_NONE
                # noinspection PyTypeChecker
                handlers.append(urllib.request.HTTPSHandler(0, context, False))
            opener = urllib.request.build_opener(*handlers)
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
            if httpCodeAnyOf(ex.code, [http.HTTPStatus.BAD_GATEWAY, http.HTTPStatus.GATEWAY_TIMEOUT, http.HTTPStatus.INTERNAL_SERVER_ERROR]):
                retry = attempt <= 3
            elif httpCodeAnyOf(ex.code, [http.HTTPStatus.NOT_FOUND, http.HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE]):
                raise
            lastException = ex
        except urllib.error.URLError as ex:
            # noinspection PyBroadException
            try:
                errorCode = ex.args[0].errno
                if errorCode == errno.ECONNREFUSED:
                    retry = attempt <= 3
            except Exception:
                pass
            lastException = ex
        except ssl.CertificateError:
            raise
        except http.client.BadStatusLine as ex:
            retry = True
            lastException = ex
        except http.client.IncompleteRead as ex:
            retry = True
            lastException = ex
        except Exception as ex:
            retry = False
            lastException = ex
        if retry and attempt <= MAX_ATTEMPTS:
            _logger.info('Restarting ({}/{}) {}'.format(attempt, MAX_ATTEMPTS, representation))
            time.sleep(attempt * HTTP_DELAY_SECONDS_MULTIPLIER)
            continue
        raise lastException
