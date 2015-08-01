# coding: utf-8

import re
import string

import tools.dict

_LANGUAGES_SOURCE = {
    'cn': (u'китайский', 'chinese', 'chi', 'kit',),
    'de': (u'немецкий', 'deutch',),
    'en': (u'английский', 'english', 'eng',),
    'es': (u'испанский',),
    'fr': (u'французский',),
    'it': (u'итальянский',),
    'jp': (u'японский', 'japanese', 'jap',),
    'ko': (u'корейский', 'korean', 'kor',),
    'pt': (u'португальский', 'portuguese',),
    'ru': (u'русский', 'russian', 'rus',),
    'tw': (u'тайваньский',),
    '': ('other',),
}
_LANGUAGES = tools.dict.expandMapping(_LANGUAGES_SOURCE)

LOWERCASE_LETTERS_RUSSIAN = set(u'абвгдеёжзийклмнопрстуфхцчшщьыъэюя')
LOWERCASE_LETTERS_ENGLISH = set(string.lowercase)

LANGUAGES_TO_LOWERCASE_LETTERS = {
    'ru': LOWERCASE_LETTERS_RUSSIAN,
    'en': LOWERCASE_LETTERS_ENGLISH,
}


def _cleanLangStr(langStr):
    return re.sub(r'^([^\.]+)(\.[^\.]+)?$', r'\1', langStr.lower(), flags=re.U)


def tryGetAbbreviation(langStr):
    result = _LANGUAGES.get(_cleanLangStr(langStr))
    if result is not None:
        result = result.upper()
    return result


def getAbbreviation(langStr):
    return _LANGUAGES[_cleanLangStr(langStr)].upper()
