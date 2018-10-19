# coding: utf-8

import codecs
import csv
import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
from card.utils import CardUtils

def main(args):
    complSet = set()
    complMap = {}
    database = {}

    with codecs.open(args[0], encoding='utf_16_le') as fobj:
        fobj.readline()  # skip header
        reader = csv.DictReader(fobj, dialect=csv.excel_tab, fieldnames=['set', 'eng_name', 'lng_name', 'lang', 'foil', 'number'])
        for row in reader:
            if row['lang'] in ('RUS', 'ENG'):
                stdEngName = CardUtils.utf2std(row['eng_name'])
                for fieldKey in ['eng_name', 'lng_name']:
                    name = row[fieldKey]
                    for part in CardUtils.split_name(name) + [name]:
                        values = complMap.setdefault(CardUtils.make_key(part), [])
                        if stdEngName not in values:
                            values.append(stdEngName)
                    complSet.add(CardUtils.unquote(CardUtils.utf2std(CardUtils.get_primary_name(name))))

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

            cardKey = CardUtils.make_key(row['eng_name'])
            setInfo = database.setdefault(row['set'], { 'cards': {}, 'foil': set(), 'languages': set() })
            setInfo['cards'][cardKey] = (numberValue, row['foil'])
            setInfo['foil'].add(row['foil'])
            setInfo['languages'].add(row['lang'])

    for setId, entry in database.items():
        entry['languages'] = list(entry['languages'])
        entry['foil'] = list(entry['foil'])

    del complMap['']
    complSet.discard('')
    for variable, filepath in ((sorted(list(complSet)), 'completion_set.json'), (complMap, 'completion_map.json'), (database, 'database.json')):
        with codecs.open(filepath, 'w', 'utf-8') as fobj:
            fobj.write(json.dumps(variable, ensure_ascii=False, sort_keys=True))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
