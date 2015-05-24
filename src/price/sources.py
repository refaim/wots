import decimal
import re
import string
import urllib
from lxml import html

import card.sets
import card.utils
import core.currency
import core.network


def getCardKey(cardName, language, foil):
    return ';'.join([
        ''.join(c.lower() for c in cardName if c in string.letters),
        language,
        'foil' if foil else 'regular'
    ])


class TcgPlayer(object):
    def __init__(self):
        self.setQueryUrlTemplate = 'http://magic.tcgplayer.com/db/price_guide.asp?setname={}'
        self.cardQueryUrlTemplate = 'http://shop.tcgplayer.com/magic/{}/{}'
        self.pricesBySetAbbrv = {}
        self.fullSetNames = {
            '10E': '10th Edition',
            'TST': 'Timeshifted',
            'M10': 'Magic 2010 (M10)',
            'M11': 'Magic 2011 (M11)',
            'M12': 'Magic 2012 (M12)',
            'M13': 'Magic 2013 (M13)',
            'M14': 'Magic 2014 (M14)',
            'M15': 'Magic 2015 (M15)',
            'MD1': 'Magic Modern Event Deck',
            'RAV': 'Ravnica',
            '9ED': '9th Edition',
        }

    def getTitle(self):
        return 'tcgplayer.com'

    def getFullSetName(self, setId):
        return self.fullSetNames.get(setId, card.sets.getFullName(setId))

    def makeUrlPart(self, rawString):
        result = []
        for c in rawString.lower():
            rc = c
            if c == ' ':
                rc = '-'
            elif c not in string.letters:
                rc = ''
            result.append(rc)
        return ''.join(result)

    def cacheSingleCardPrice(self, cardName, setId, language):
        tcgSetName = self.makeUrlPart(self.getFullSetName(setId))
        tcgCardName = self.makeUrlPart(card.utils.escape(cardName))
        priceHtml = html.document_fromstring(core.network.getUrl(self.cardQueryUrlTemplate.format(tcgSetName, tcgCardName)))
        for priceBlock in priceHtml.cssselect('.priceGuideClass'):
            foil = priceBlock.cssselect('.cardStyle b')[0].text == 'Foil'
            self.pricesBySetAbbrv[card.sets.getAbbreviation(setId)][getCardKey(cardName, language, foil)] = {
                'price': decimal.Decimal(re.match(r'.*?\$([\d\.]+).*', priceBlock.cssselect('.priceRange .median')[0].text).group(1)),
                'currency': core.currency.USD,
                'source_id': 'tcg',
            }

    def cacheSetCardsPrices(self, setId, language):
        setAbbrv = card.sets.getAbbreviation(setId)
        if setAbbrv not in self.pricesBySetAbbrv:
            self.pricesBySetAbbrv[setAbbrv] = {}

        setPrices = html.document_fromstring(core.network.getUrl(self.setQueryUrlTemplate.format(urllib.quote(self.getFullSetName(setId)))))
        tables = setPrices.cssselect('table')
        if not tables:
            return
        priceTable = tables[-1]
        for resultsEntry in priceTable.cssselect('tr'):
            cells = resultsEntry.cssselect('td')
            if cells and len(cells) >= 5:
                cellCardNameString = cells[0].cssselect('font')[0].text
                if cellCardNameString.startswith('&nbsp;'):
                    cellCardNameString = cellCardNameString[6:]
                cellCardKey = getCardKey(cellCardNameString, language, False)
                priceString = cells[6].cssselect('font')[0].text
                if priceString and priceString.startswith('$'):
                    self.pricesBySetAbbrv[setAbbrv][cellCardKey] = {
                        # 'name': cellCardNameString.strip(),
                        # 'set': setAbbrv,
                        'price': decimal.Decimal(re.match(r'\$([\d\.]+).*', priceString).group(1)),
                        'currency': core.currency.USD,
                        'source_id': 'tcg',
                    }

    def queryPrice(self, cardName, setId, language, foil):
        if not foil:
            language = ''
        setAbbrv = card.sets.getAbbreviation(setId)
        cardKey = getCardKey(cardName, language, foil)
        if setAbbrv not in self.pricesBySetAbbrv:
            self.cacheSetCardsPrices(setId, language)
        # if cardKey not in self.pricesBySetAbbrv[setAbbrv]:
        #     self.cacheSingleCardPrice(cardName, setId, language)
        # if cardKey not in self.pricesBySetAbbrv[setAbbrv] and not foil:
        #     cardKey = getCardKey(cardName, 'en', False)
        result = self.pricesBySetAbbrv.get(setAbbrv, {}).get(cardKey, {})
        return result


def getPriceSourceClasses():
    return [
        TcgPlayer,
    ]
