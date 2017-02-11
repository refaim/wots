import codecs
import collections
import json
import random
import sys
import traceback

import card.sources
import wizard

def main(args):
    sourceId, stdoutLog, stderrLog = args

    oldStdout = sys.stdout
    oldStderr = sys.stderr
    sys.stdout = codecs.open(stdoutLog, 'a', 'utf-8')
    sys.stderr = codecs.open(stderrLog, 'a', 'utf-8')

    with codecs.open(wizard.getResourcePath('autocomplete.json'), 'r', 'utf-8') as fobj:
        cardsNamesMap = json.load(fobj)
    with codecs.open(wizard.getResourcePath('database.json'), 'r', 'utf-8') as fobj:
        setsInfo = json.load(fobj)

    setsCards = {}
    for setId, setData in setsInfo.items():
        setsCards[setId] = []
        for cardKey in setData['cards'].keys():
            if len(cardKey) > 0 and cardKey not in ['plains', 'island', 'swamp', 'mountain', 'forest']:
                setsCards[setId].extend(cardsNamesMap[cardKey])

    cardSourceClass = None
    cardSource = None
    for classObject in sorted(card.sources.getCardSourceClasses(), key=lambda x: x.__name__):
        instance = classObject()
        if instance.getTitle() == sourceId:
            cardSourceClass = classObject
            cardSource = instance
            break

    numsFound = collections.Counter()
    for setId in setsCards.keys():
        sample = random.sample(setsCards[setId], min(10, len(setsCards[setId])))
        for cardName in sample:
            stateString = '[{}] {} >= {}...'.format(setId, card.utils.escape(cardName), sourceId)
            sys.stdout.write(stateString + ' ')
            numFound = 0
            try:
                for cardInfo in cardSource.query(cardName):
                    if cardInfo is not None:
                        numFound += 1
                sys.stdout.write('{} found'.format(numFound) + '\n')
            except KeyboardInterrupt:
                sys.stdout = oldStdout
                sys.stderr = oldStderr
                return 1
            except Exception:
                sys.stdout.write('<{} FAIL'.format('=' * 20) + '\n')
                sys.stderr.write(stateString + '\n')
                traceback.print_exc(file=sys.stderr)
                sys.stderr.write(('=' * 100) + '\n')
                cardSource = cardSourceClass()
            finally:
                numsFound[sourceId] += numFound
                sys.stdout.flush()
                sys.stderr.flush()

    sys.stdout.write('Finished\n')

    return 0

if __name__ == '__main__':
    rc = 1
    try:
        rc = main(sys.argv[1:])
    except KeyboardInterrupt:
        pass
    sys.exit(rc)
