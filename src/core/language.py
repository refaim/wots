# coding: utf-8

import re
import string

import tools.dict

_LANGUAGES_SOURCE = {
    'cn': ('китайский', 'кит', 'chinese', 'chi', 'kit',),
    'de': ('немецкий', 'нем', 'deutch', 'nem',),
    'en': ('английский', 'англ', 'анг', 'english', 'eng',),
    'es': ('испанский', 'исп', 'isp', 'esp',),
    'fr': ('французский', 'франц', 'french', 'fre',),
    'it': ('итальянский', 'итал', 'ita', 'ital',),
    'jp': ('японский', 'яп', 'japanese', 'jap',),
    'ko': ('корейский', 'кор', 'korean', 'kor',),
    'pt': ('португальский', 'пор', 'portuguese', 'por', 'port',),
    'ru': ('русский', 'рус', 'russian', 'rus',),
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
    return re.sub(r'^([^.]+)(\.[^.]+)?$', r'\1', langStr.lower(), flags=re.U)


def tryGetAbbreviation(langStr):
    result = _LANGUAGES.get(_cleanLangStr(langStr))
    if result is not None:
        result = result.upper()
    return result


def getAbbreviation(langStr):
    return _LANGUAGES[_cleanLangStr(langStr)].upper()
