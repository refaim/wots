# coding: utf-8

import re
from abc import ABC
from typing import List

from core.utils import LangUtils, StringUtils


class CardUtils(ABC):
    __UTF_TO_STD = {
        'Æ': 'AE',
        '│': '|',
        '’': "'",
        '“': '"',
        '”': '"',
        '«': '"',
        '»': '"',
    }
    __STD_TO_UTF = {
        "'": '’',
        'AE': 'Æ',
        '|': '│',
        '/': '│',
    }
    __LANG_QUOTES = {
        'EN': ('“', '”'),
        'RU': ('«', '»'),
    }
    __DOUBLE_CARD_REGEXP = re.compile(r'\s*(\|+|\\+|/+|│+)\s*', re.UNICODE)

    @classmethod
    def make_key(cls, card: str) -> str:
        return StringUtils.letters(cls.utf2std(card)).lower()

    @classmethod
    def utf2std(cls, card: str) -> str:
        result = card
        for k, v in cls.__UTF_TO_STD.items():
            result = result.replace(k, v)
        return result

    @classmethod
    def std2utf(cls, card: str) -> str:
        result = card
        num_quotes = card.count('"')
        assert num_quotes == 0 or num_quotes == 2
        if num_quotes == 2:
            for c in cls.__LANG_QUOTES[LangUtils.guess_language(card)]:
                result = result.replace('"', c, 1)
        for k, v in cls.__STD_TO_UTF.items():
            result = result.replace(k, v)
        return result

    @classmethod
    def unquote(cls, card: str) -> str:
        return card.replace('"', '')

    @classmethod
    def get_primary_name(cls, double_card: str) -> str:
        return cls.split_name(double_card)[0]

    @classmethod
    def split_name(cls, double_card: str) -> List[str]:
        parts = cls.__DOUBLE_CARD_REGEXP.split(double_card)
        result = []
        for i in range(0, len(parts), 2):
            result.append(parts[i])
        return result
