import codecs
import enum
import json
import logging
import os
import platform
import re
import string
import sys
from abc import ABC, abstractmethod
from multiprocessing import Queue as MpQueue
from typing import List, Optional


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


class OsUtils(ABC):
    @classmethod
    def is_windows(cls):
        return platform.system() == 'Windows'

    @classmethod
    def is_linux(cls):
        return platform.system() == 'Linux'

    @classmethod
    def is_winxp_or_older(cls):
        return cls.is_windows() and sys.getwindowsversion().major <= 5

    @classmethod
    def is_win10(cls):
        return cls.is_windows() and sys.getwindowsversion().major == 10


@enum.unique
class Currency(enum.IntEnum):
    RUR = enum.auto()
    EUR = enum.auto()
    USD = enum.auto()


class StringUtils(ABC):
    LOWERCASE_LETTERS_RUSSIAN = set('абвгдеёжзийклмнопрстуфхцчшщьыъэюя')
    LOWERCASE_LETTERS_ENGLISH = set(string.ascii_lowercase)

    __CURRENCY_FORMATS = {
        Currency.RUR: lambda: '{}р.' if OsUtils.is_winxp_or_older() else '{}₽',
        Currency.EUR: lambda: '€{}',
        Currency.USD: lambda: '${}',
    }

    @classmethod
    def letters(cls, s: str) -> str:
        return re.sub(r'[\W\d_]+', '', s)

    @classmethod
    def letter_clusters(cls, s: str) -> List[str]:
        result = []
        for match in re.finditer(r'([^\W\d_]+)', s, re.UNICODE):
            result.append(match.group(1))
        return result

    @classmethod
    def format_money(cls, amount, currency: Currency):
        return cls.__CURRENCY_FORMATS[currency]().format(amount)


class LangUtils(ABC):
    @classmethod
    def guess_language(cls, s: str) -> Optional[str]:
        result = None
        for language, lang_letters in {'EN': StringUtils.LOWERCASE_LETTERS_ENGLISH, 'RU': StringUtils.LOWERCASE_LETTERS_RUSSIAN}.items():
            if set(StringUtils.letters(s).lower()) <= lang_letters:
                result = language
                break
        return result


class DictUtils(ABC):
    @classmethod
    def flip(cls, d: dict) -> dict:
        return {v: k for k, v in d.items()}
