# coding: utf-8

import codecs
import csv
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'src')))
import card.utils


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.DictReader(utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
    for row in csv_reader:
        result = {}
        for title, cell in row.iteritems():
            if isinstance(cell, list) and len(cell) == 1:
                cell = cell[0]
            result[title] = unicode(cell, 'utf-8')
        yield result


def main(args):
    autocomplete = {}

    nameSeparator = u'\u2502'
    with codecs.open(args[0], encoding='utf_16_le') as fp:
        fp.readline()  # skip header
        reader = unicode_csv_reader(fp, dialect=csv.excel_tab, fieldnames=['set', 'name', 'original', 'lang', 'number'])
        for row in reader:
            row['name'] = row['name'].replace(nameSeparator, u'|')
            row['original'] = row['original'].replace(nameSeparator, u'|')
            for key in (card.utils.getNameKey(cardName) for cardName in (row['name'], row['original']) if row['lang'] in ('RUS', 'ENG')):
                values = autocomplete.setdefault(key, [])
                if not row['name'] in values:
                    values.append(row['name'])

    del autocomplete['']
    with codecs.open('autocomplete.json', 'w', 'utf-8') as output:
        output.write(json.dumps(autocomplete, ensure_ascii=False, encoding='utf-8'))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
