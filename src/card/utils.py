# coding: utf-8


def _processCard(cardname, rules):
    result = cardname
    for k, v in rules.items():
        result = cardname.replace(k, v)
    return result


_STRINGS_TO_ESCAPE = {
    'Æ': 'AE',
}
_STRINGS_TO_UNESCAPE = {}
for k, v in _STRINGS_TO_ESCAPE.items():
    _STRINGS_TO_UNESCAPE[v] = k

_STRINGS_TO_CLEAN = {
    '//': '/',
}


def escape(cardname):
    return _processCard(cardname, _STRINGS_TO_ESCAPE)


def unescape(cardname):
    return _processCard(cardname, _STRINGS_TO_UNESCAPE)


def clean(cardname):
    return _processCard(cardname, _STRINGS_TO_CLEAN)
