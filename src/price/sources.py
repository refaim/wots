import re
import string
import urllib
from lxml import html

import card.sets
import core.currency
import core.network


def getCardKey(cardName):
    return ''.join(c.lower() for c in cardName if c in string.letters)


class TcgPlayer(object):
    def __init__(self):
        self.setQueryUrlTemplate = 'http://magic.tcgplayer.com/db/price_guide.asp?setname={}'
        self.pricesBySetAbbrv = {}

    def getTitle(self):
        return 'tcgplayer.com'

    def queryPrice(self, cardName, setId, language, foilness):
        return
        #print(cardName, setId, language, foilness)
        # TODO foilness
        # TODO cache
        setAbbrv = card.sets.getAbbreviation(setId)
        cardKey = getCardKey(cardName)
        if setAbbrv not in self.pricesBySetAbbrv or cardKey not in self.pricesBySetAbbrv[setAbbrv]:
            setPrices = html.document_fromstring(core.network.getUrl(self.setQueryUrlTemplate.format(urllib.quote(card.sets.getFullName(setId)))))
            tables = setPrices.cssselect('table')
            if tables:
                priceTable = tables[-1]
                for resultsEntry in priceTable.cssselect('tr'):
                    cells = resultsEntry.cssselect('td')
                    if cells and len(cells) >= 5:
                        cellCardNameString = cells[0].cssselect('font')[0].text
                        if cellCardNameString.startswith('&nbsp;'):
                            cellCardNameString = cellCardNameString[6:]
                        cellCardKey = getCardKey(cellCardNameString)
                        priceString = cells[6].cssselect('font')[0].text
                        if priceString and priceString.startswith('$'):
                            if setAbbrv not in self.pricesBySetAbbrv:
                                self.pricesBySetAbbrv[setAbbrv] = {}
                            self.pricesBySetAbbrv[setAbbrv][cellCardKey] = {
                                'name': cellCardNameString.strip(),
                                'set': setAbbrv,
                                'value': float(re.match(r'\$([\d\.]+).*', priceString).group(1)),
                                'currency': core.currency.USD,
                                'source': 'TCG',
                            }
        result = self.pricesBySetAbbrv.get(setAbbrv, {}).get(cardKey, {})
        return result


def getPriceSourceClasses():
    return [
        TcgPlayer,
    ]
