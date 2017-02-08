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
        if cardKey in self.cardsNames:
            newCardName = self.cardsNames[cardKey][0]
            cardInfo['name']['caption'] = newCardName
            cardKey = card.utils.getNameKey(newCardName)

        cardSets = self.cardSets.get(cardKey, None)
        print(cardSets) # TODO !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if cardSets is not None and len(cardSets) == 1:
            newCardSet = card.sets.tryGetAbbreviation(list(cardSets)[0])
            if newCardSet is not None:
                cardInfo['set'] = newCardSet

        if cardInfo.get('set') is not None:
            setKey = card.sets.tryGetAbbreviation(cardInfo['set'])
            if setKey in self.cardIds:
                newCardId = self.cardIds[setKey].get(cardKey, None)
                if newCardId is not None:
                    cardInfo['id'] = newCardId

            if setKey in self.setsLanguages and len(self.setsLanguages[setKey]) == 1:
                cardInfo['language'] = core.language.tryGetAbbreviation(self.setsLanguages[setKey][0])

            setFoilness = self.setsFoilness.get(setKey, None)
            if setFoilness is not None:
                # if 'foilness' in cardInfo and cardInfo['foilness'] != setFoilness:
                #     self.logger.warning('Foilness data conflict: card {} says {}, set {} says {}'.format(cardInfo['name']['caption'], cardInfo['foilness'], setKey, setFoilness))
                cardInfo['foilness'] = setFoilness

        return cardInfo
