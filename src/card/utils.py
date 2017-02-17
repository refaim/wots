# coding: utf-8

import re

import core.language


def _processCard(cardname, rules):
    result = cardname
    for k, v in rules.items():
        result = result.replace(k, v)
    return result


_STRINGS_TO_ESCAPE = {
    u'Æ': u'AE',
    u'\u2019': u"'",
    u'“': u'',
    u'”': u'',
}
_STRINGS_TO_UNESCAPE = {}
for k, v in _STRINGS_TO_ESCAPE.items():
    if len(v) > 0:
        _STRINGS_TO_UNESCAPE[v] = k

_STRINGS_TO_CLEAN = {
    u'//': u'/',
}

_CACHE_ESCAPE = {}
_CACHE_UNESCAPE = {}

_LETTERS = core.language.LOWERCASE_LETTERS_ENGLISH | core.language.LOWERCASE_LETTERS_RUSSIAN

_DOUBLE_FACED_CARD_RE = re.compile(r'\|+|\\+|\/+')


def escape(cardname):
    if cardname not in _CACHE_ESCAPE:
        _CACHE_ESCAPE[cardname] = _processCard(cardname, _STRINGS_TO_ESCAPE)
    return _CACHE_ESCAPE[cardname]


def unescape(cardname):
    if cardname not in _CACHE_UNESCAPE:
        _CACHE_UNESCAPE[cardname] = _processCard(cardname, _STRINGS_TO_UNESCAPE)
    return _CACHE_UNESCAPE[cardname]


def clean(cardname):
    return _processCard(cardname, _STRINGS_TO_CLEAN)


def getNameKey(cardname):
    return u''.join(c for c in escape(cardname).lower() if c in _LETTERS)


def getPrimaryName(cardname):
    nameSeparator = u'\u2502'
    return _DOUBLE_FACED_CARD_RE.split(cardname.replace(nameSeparator, u'|'))[0]
