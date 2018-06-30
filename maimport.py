# coding: utf-8

import codecs
import csv
import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
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
    complSet = set()
    complMap = {}
    database = {}

    with codecs.open(args[0], encoding='utf_16_le') as fobj:
        fobj.readline()  # skip header
        reader = unicode_csv_reader(fobj, dialect=csv.excel_tab, fieldnames=['set', 'name', 'original', 'lang', 'foil', 'number'])
        for row in reader:
            row['name'] = card.utils.escape(card.utils.getPrimaryName(row['name']))
            if row['original'] is None:
                print(row)
            row['original'] = card.utils.getPrimaryName(row['original'])
            for key in (card.utils.getNameKey(cardName) for cardName in (row['name'], row['original']) if row['lang'] in ('RUS', 'ENG')):
                complSet.add(card.utils.escape(row['original']))
                completionString = card.utils.escape(row['name'])
                values = complMap.setdefault(key, [])
                if completionString not in values:
                    values.append(completionString)

            # workaround for some sort of csv parse bug
            if row['foil'] in ('POR', 'FRA'):
                row['lang'] = row['foil']
                row['foil'] = row['number']
                row['number'] = row[None]
                del row[None]

            numberValue = None
            numberString = row['number']
            if '*' not in numberString and all(s not in row['set'].lower() for s in ('promos', 'game day')):
                match = re.match(r'\s*(\d+)\/.*', numberString)
                if match:
                    numberValue = int(match.group(1))

            cardKey = card.utils.getNameKey(row['name'])
            setInfo = database.setdefault(row['set'], { 'cards': {}, 'foil': set(), 'languages': set() })
            setInfo['cards'][cardKey] = (numberValue, row['foil'])
            setInfo['foil'].add(row['foil'])
            setInfo['languages'].add(row['lang'])

    for setId, entry in database.iteritems():
        entry['languages'] = list(entry['languages'])
        entry['foil'] = list(entry['foil'])

    del complMap['']
    complSet.discard('')
    for variable, filepath in ((sorted(list(complSet)), 'completion_set.json'), (complMap, 'completion_map.json'), (database, 'database.json')):
        with codecs.open(filepath, 'w', 'utf-8') as fobj:
            fobj.write(json.dumps(variable, ensure_ascii=False, encoding='utf-8', sort_keys=True))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
