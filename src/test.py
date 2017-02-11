from __future__ import print_function

import codecs
import collections
import json
import random
import traceback
import unittest

import card.sources
import wizard

class TestCardSource(unittest.TestCase):
    # def test_upper(self):
    #     self.assertEqual('foo'.upper(), 'FOO')

    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())

    def test_search(self):
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

        cardSourcesClasses = sorted(card.sources.getCardSourceClasses(), key=lambda x: x.__name__)
        cardSourcesInstances = [classObject() for classObject in cardSourcesClasses]
        cardSourcesIds = [instance.getTitle() for instance in cardSourcesInstances]

        numsFound = collections.Counter()
        for setId in sorted(setsCards.keys()):
            sample = random.sample(setsCards[setId], 10)
            for cardName in sample:
                for sourceIndex, sourceId in enumerate(cardSourcesIds):
                    stateString = '[{}] {} >= {}...'.format(setId, cardName, sourceId)
                    print(stateString, end=' ', flush=True)
                    numFound = 0
                    try:
                        for cardInfo in cardSourcesInstances[sourceIndex].query(cardName):
                            numFound += 1
                        print('{} found'.format(numFound), flush=True)
                    except Exception:
                        print('FAIL!', flush=True)
                        with open('test_errors.log', 'a') as fobj:
                            fobj.write(stateString + '\n')
                            traceback.print_exc(file=fobj)
                            fobj.write(('=' * 100) + '\n')
                        cardSourcesInstances[sourceIndex] = cardSourcesClasses[sourceIndex]()
                    finally:
                        numsFound[sourceId] += numFound

if __name__ == '__main__':
    unittest.main()
