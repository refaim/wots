import copy

from card.components import SetOracle, LanguageOracle
from card.utils import CardUtils
from core.utils import ILogger


class CardsFixer(object):
    def __init__(self, cardsInfo, cardsNames, setOracle: SetOracle, langOracle: LanguageOracle, logger: ILogger):
        self.logger = logger
        self.setOracle = setOracle
        self.langOracle = langOracle
        self.cardsNames = cardsNames
        self.setsLanguages = {}
        self.setsFoilness = {}
        self.cardsIds = {}
        self.cardSets = {}

        for setId, setInfo in cardsInfo.items():
            setKey = self.setOracle.get_abbreviation(setId)
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
                    self.cardsIds.setdefault(setKey, {})[cardKey] = cardInfo[0]

    def fixCardInfo(self, cardInfo):
        cardInfo = copy.deepcopy(cardInfo)
        cardInfo['name']['caption'] = CardUtils.get_primary_name(cardInfo['name']['caption'])

        cardKey = CardUtils.make_key(cardInfo['name']['caption'])
        if cardKey in self.cardsNames:
            newCardName = self.cardsNames[cardKey][0]
            cardInfo['name']['caption'] = newCardName
            cardKey = CardUtils.make_key(newCardName)

        if 'description' not in cardInfo['name'] or cardInfo['name']['description'] is None:
            cardInfo['name']['description'] = ''

        cardSets = self.cardSets.get(cardKey, set())
        oldCardSet = cardInfo.get('set')
        if oldCardSet is not None:
            oldCardSetKey = self.setOracle.get_abbreviation(oldCardSet)
            if oldCardSetKey is None:
                self.logger.warning('Unknown set %s on card %s', oldCardSet, cardKey)
            if oldCardSetKey is None or oldCardSetKey in self.cardsIds and cardKey not in self.cardsIds[oldCardSetKey]:
                del cardInfo['set']
                if 'id' in cardInfo:
                    del cardInfo['id']

        matchedSets = []
        for possibleSet in cardSets:
            possibleSetKey = self.setOracle.get_abbreviation(possibleSet)
            if possibleSetKey is None:
                self.logger.warning('Unknown internal set %s', possibleSet)
            if possibleSetKey is not None:
                cardFoilness = cardInfo.get('foilness')
                setFoilness = self.setsFoilness.get(possibleSetKey)
                if setFoilness is None or cardFoilness is None or setFoilness == cardFoilness:
                    matchedSets.append(possibleSetKey)
        if len(matchedSets) == 1:
            cardInfo['set'] = matchedSets[0]

        newCardSet = cardInfo.get('set')
        if newCardSet is not None:
            newCardSetKey = self.setOracle.get_abbreviation(newCardSet)
            if newCardSetKey in self.cardsIds:
                newCardId = self.cardsIds[newCardSetKey].get(cardKey, None)
                if newCardId is not None:
                    cardInfo['id'] = newCardId

            if newCardSetKey in self.setsLanguages and len(self.setsLanguages[newCardSetKey]) == 1:
                cardInfo['language'] = self.langOracle.get_abbreviation(self.setsLanguages[newCardSetKey][0])

            setFoilness = self.setsFoilness.get(newCardSetKey, None)
            if setFoilness is not None:
                cardInfo['foilness'] = setFoilness

        return cardInfo
