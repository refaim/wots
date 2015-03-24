# coding: utf-8


def _processCard(cardname, rules):
    result = cardname
    for k, v in rules.iteritems():
        result = cardname.replace(k, v)
    return result


_STRINGS_TO_ESCAPE = {
    u'Æ': u'AE',
}
_STRINGS_TO_UNESCAPE = {}
for k, v in _STRINGS_TO_ESCAPE.iteritems():
    _STRINGS_TO_UNESCAPE[v] = k

_STRINGS_TO_CLEAN = {
    u'//': u'/',
}


def escape(cardname):
    return _processCard(cardname, _STRINGS_TO_ESCAPE)


def unescape(cardname):
    return _processCard(cardname, _STRINGS_TO_UNESCAPE)


def clean(cardname):
    return _processCard(cardname, _STRINGS_TO_CLEAN)
