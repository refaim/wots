import codecs
import json
import logging
import os
import sys
from multiprocessing import Queue as MpQueue


def get_project_root() -> str:
    if getattr(sys, 'frozen', False):
        result = os.path.dirname(sys.executable)
    else:
        result = os.path.join(os.path.dirname(__file__), '..', '..')
    return os.path.normpath(result)


def get_resource_path(filename: str) -> str:
    return os.path.normpath(os.path.join(get_project_root(), 'res', filename))


def load_json_resource(filename: str):
    with codecs.open(get_resource_path(filename), 'r', 'utf-8') as fobj:
        return json.load(fobj)


class ILogger(object):
    def get_child(self, name: str) -> 'ILogger':
        pass

    def debug(self, message, *args, **kwargs):
        pass

    def info(self, message, *args, **kwargs):
        pass

    def warning(self, message, *args, **kwargs):
        pass

    def error(self, message, *args, **kwargs):
        pass

    def critical(self, message, *args, **kwargs):
        pass


class DummyLogger(ILogger):
    pass


class MultiprocessingLogger(ILogger):
    def __init__(self, name: str, queue: MpQueue):
        logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
        self.__name = name
        self.__queue = queue

    def get_child(self, name: str) -> 'ILogger':
        child_name = name
        if self.__name:
            child_name = '{}.{}'.format(self.__name, child_name)
        return MultiprocessingLogger(child_name, self.__queue)

    def __log(self, name, level, message, *args, **kwargs):
        self.__queue.put((name, level, message, args, kwargs))

    def debug(self, message, *args, **kwargs):
        self.__log(self.__name, logging.DEBUG, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.__log(self.__name, logging.INFO, message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.__log(self.__name, logging.WARNING, message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.__log(self.__name, logging.ERROR, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.__log(self.__name, logging.CRITICAL, message, *args, **kwargs)
