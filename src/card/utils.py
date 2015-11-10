# coding: utf-8


def _processCard(cardname, rules):
    result = cardname
    for k, v in rules.items():
        result = cardname.replace(k, v)
    return result


_STRINGS_TO_ESCAPE = {
    u'Æ': u'AE',
}
_STRINGS_TO_UNESCAPE = {}
for k, v in _STRINGS_TO_ESCAPE.items():
    _STRINGS_TO_UNESCAPE[v] = k

_STRINGS_TO_CLEAN = {
    u'//': u'/',
}

_CACHE_ESCAPE = {}
_CACHE_UNESCAPE = {}


def escape(cardname):
    if not cardname in _CACHE_ESCAPE:
        _CACHE_ESCAPE[cardname] = _processCard(cardname, _STRINGS_TO_ESCAPE)
    return _CACHE_ESCAPE[cardname]


def unescape(cardname):
    if not cardname in _CACHE_UNESCAPE:
        _CACHE_UNESCAPE[cardname] = _processCard(cardname, _STRINGS_TO_UNESCAPE)
    return _CACHE_UNESCAPE[cardname]


def clean(cardname):
    return _processCard(cardname, _STRINGS_TO_CLEAN)
