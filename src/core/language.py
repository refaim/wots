# coding: utf-8

import re
import string

import tools.dict

_LANGUAGES_SOURCE = {
    'cn': (u'китайский', 'chinese',),
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


def getAbbreviation(langStr):
    cleaned = re.sub(r'^([^\.]+)(\.[^\.]+)?$', r'\1', langStr.lower())
    return _LANGUAGES[cleaned].upper()
