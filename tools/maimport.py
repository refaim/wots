# coding: utf-8

import codecs
import itertools
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'src')))
import wizard


def main(args):
    english = codecs.open('en', 'r', 'utf-8').read().splitlines()
    russian = codecs.open('ru', 'r', 'utf-8').read().splitlines()
    if len(english) != len(russian):
        raise Exception('Length mismatch')

    cards = {}
    for en, ru in itertools.izip(english, russian):
        en = en.replace(u'│', u' / ')
        ru = ru.replace(u'│', u' / ')
        for cardname in (en, ru):
            key = wizard.getCardCompletionKey(cardname)
            if key:
                values = cards.setdefault(key, [])
                if not en in values:
                    values.append(en)
    with codecs.open('../resources/autocomplete.json', 'w', 'utf-8') as output:
        output.write(json.dumps(cards, ensure_ascii=False, encoding='utf-8'))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
