import codecs
import json
import logging
import os
import re
import string
import sys
from abc import ABC, abstractmethod
from multiprocessing import Queue as MpQueue
from typing import List


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


class ILogger(ABC):
    @abstractmethod
    def get_child(self, name: str) -> 'ILogger':
        raise NotImplementedError()

    @abstractmethod
    def debug(self, message, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def info(self, message, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def warning(self, message, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def error(self, message, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def critical(self, message, *args, **kwargs):
        raise NotImplementedError()


class DummyLogger(ILogger):
    def get_child(self, name: str) -> 'ILogger':
        return self

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


class StringUtils(ABC):
    LOWERCASE_LETTERS_RUSSIAN = set(u'абвгдеёжзийклмнопрстуфхцчшщьыъэюя')
    LOWERCASE_LETTERS_ENGLISH = set(string.ascii_lowercase)

    @classmethod
    def letters(cls, s: str) -> str:
        return re.sub(r'[\W\d_]+', '', s)

    @classmethod
    def letter_clusters(cls, s: str) -> List[str]:
        result = []
        for match in re.finditer(r'([^\W\d_]+)', s, re.UNICODE):
            result.append(match.group(1))
        return result
