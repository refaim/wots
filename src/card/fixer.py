import copy

import card.sets
import core.language

class CardsFixer(object):
    def __init__(self, cardsInfo, cardsNames):
        self.cardsNames = cardsNames
        self.setsLanguages = {}
        self.setsFoilness = {}
        self.cardIds = {}
        self.cardSets = {}
        for setId, setInfo in cardsInfo.items():
            setKey = card.sets.tryGetAbbreviation(setId)
            assert setKey is not None
            self.setsLanguages[setKey] = setInfo['languages']

            # Possible values: Yes (foil and non-foil), No (non-foil only), Only (foil only)
            rawSetFoilness = setInfo['foil']
            finSetFoilness = None
            if len(rawSetFoilness) == 1:
                if rawSetFoilness[0] == 'No':
                    finSetFoilness = False
                elif rawSetFoilness[0] == 'Only':
                    finSetFoilness = True
            self.setsFoilness[setKey] = finSetFoilness

            for cardKey, cardInfo in setInfo['cards'].items():
                cardSets = self.cardSets.setdefault(cardKey, set())
                cardSets.add(setKey)
                if cardInfo[0] is not None:
                    self.cardIds.setdefault(setKey, {})[cardKey] = cardInfo[0]

    def fixCardInfo(self, cardInfo):
        cardInfo = copy.deepcopy(cardInfo)
        cardKey = card.utils.getNameKey(cardInfo['name']['caption'])
        cardSets = self.cardSets.get(cardKey, None)

        if cardKey in self.cardsNames:
            newCardName = self.cardsNames[cardKey][0]
            cardInfo['name']['caption'] = newCardName
            cardKey = card.utils.getNameKey(newCardName)

        oldCardSet = cardInfo.get('set')
        if oldCardSet is not None:
            oldCardSetKey = card.sets.tryGetAbbreviation(oldCardSet)
            if oldCardSetKey is not None and cardSets is not None and oldCardSetKey not in cardSets:
                del cardInfo['set']

        newCardSetKey = None
        if cardSets is not None and len(cardSets) == 1:
            newCardSetKey = card.sets.tryGetAbbreviation(list(cardSets)[0])
            if newCardSetKey is not None:
                cardInfo['set'] = newCardSetKey

        if newCardSetKey is not None:
            if newCardSetKey in self.cardIds:
                newCardId = self.cardIds[newCardSetKey].get(cardKey, None)
                if newCardId is not None:
                    cardInfo['id'] = newCardId

            if newCardSetKey in self.setsLanguages and len(self.setsLanguages[newCardSetKey]) == 1:
                cardInfo['language'] = core.language.tryGetAbbreviation(self.setsLanguages[newCardSetKey][0])

            setFoilness = self.setsFoilness.get(newCardSetKey, None)
            if setFoilness is not None:
                # if 'foilness' in cardInfo and cardInfo['foilness'] != setFoilness:
                #     self.logger.warning('Foilness data conflict: card {} says {}, set {} says {}'.format(cardInfo['name']['caption'], cardInfo['foilness'], setKey, setFoilness))
                cardInfo['foilness'] = setFoilness

        return cardInfo
