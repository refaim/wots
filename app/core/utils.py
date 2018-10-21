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
    def __init__(self, name: str):
        logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
        self._name = name

    @abstractmethod
    def get_child(self, name: str) -> 'ILogger':
        raise NotImplementedError()

    @abstractmethod
    def _log(self, name: str, level: int, message: str, *args, **kwargs) -> None:
        raise NotImplementedError()

    def debug(self, message: str, *args, **kwargs) -> None:
        self._log(self._name, logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self._log(self._name, logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self._log(self._name, logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self._log(self._name, logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        self._log(self._name, logging.CRITICAL, message, *args, **kwargs)


class StderrLogger(ILogger):
    def get_child(self, name: str) -> 'ILogger':
        return self

    def _log(self, name: str, level: int, message: str, *args, **kwargs) -> None:
        logging.getLogger(name).log(level, message, *args, *kwargs)


class MultiprocessingLogger(ILogger):
    def __init__(self, name: str, queue: MpQueue):
        super().__init__(name)
        self.__queue = queue

    def get_child(self, name: str) -> 'ILogger':
        child_name = name
        if self._name:
            child_name = '{}.{}'.format(self._name, child_name)
        return MultiprocessingLogger(child_name, self.__queue)

    def _log(self, name: str, level: int, message: str, *args, **kwargs) -> None:
        self.__queue.put((name, level, message, args, kwargs))


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

    @classmethod
    def is_x64(cls):
        return sys.maxsize > 2**32


class PathUtils(ABC):
    @classmethod
    def get_folder_size(cls, path: string) -> int:
        result = 0
        for root, dirs, files in os.walk(path):
            for filename in files:
                result += os.path.getsize(os.path.join(root, filename))
        return result

    @classmethod
    def quote(cls, path: string) -> string:
        if not OsUtils.is_windows():
            raise NotImplementedError
        path = path.strip('"')
        if ' ' in path:
            path = '"{}"'.format(path)
        return path

@enum.unique
class Currency(enum.IntEnum):
    EUR = enum.auto()
    RUR = enum.auto()
    UAH = enum.auto()
    USD = enum.auto()


class StringUtils(ABC):
    LOWERCASE_LETTERS_RUSSIAN = set('абвгдеёжзийклмнопрстуфхцчшщьыъэюя')
    LOWERCASE_LETTERS_ENGLISH = set(string.ascii_lowercase)

    __CURRENCY_FORMATS = {
        Currency.EUR: lambda: '€{}',
        Currency.RUR: lambda: '{}р.' if OsUtils.is_winxp_or_older() else '{}₽',
        Currency.UAH: lambda: '{} грн.' if OsUtils.is_winxp_or_older() else '{}₴',
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
