# coding: utf-8

import re
import string

import tools.dict

_LANGUAGES_SOURCE = {
    'cn': ('китайский', 'chinese', 'chi', 'kit',),
    'de': ('немецкий', 'deutch', 'nem',),
    'en': ('английский', 'english', 'eng',),
    'es': ('испанский', 'isp', 'esp',),
    'fr': ('французский', 'french', 'fre',),
    'it': ('итальянский', 'ita',),
    'jp': ('японский', 'japanese', 'jap',),
    'ko': ('корейский', 'korean', 'kor',),
    'pt': ('португальский', 'portuguese', 'por', 'port',),
    'ru': ('русский', 'russian', 'rus',),
    'tw': ('тайваньский',),
    '': ('other',),
}
_LANGUAGES = tools.dict.expandMapping(_LANGUAGES_SOURCE)

LOWERCASE_LETTERS_RUSSIAN = set(u'абвгдеёжзийклмнопрстуфхцчшщьыъэюя')
LOWERCASE_LETTERS_ENGLISH = set(string.ascii_lowercase)

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
