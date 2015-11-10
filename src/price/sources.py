import decimal
import lxml.html
import queue
import re
import string
import threading
import urllib.parse

import card.sets
import card.utils
import core.currency
import core.language
import core.network


def getCardKey(cardName, language, foil):
    return ';'.join([
        ''.join(c.lower() for c in cardName if c in string.ascii_letters),
        language.lower(),
        'foil' if foil else 'regular'
    ])


def tcgProcessRequests(priceRequests, priceResults, setsRequests, setsResults, singlesRequests, singlesResults, exitEvent):
    postponedRequests = {}
    requestedSets = set()
    requestedSingles = set()
    pricesCache = {}
    while True:
        if exitEvent.is_set():
            return

        while not setsResults.empty():
            setAbbrv, setPrices = setsResults.get_nowait()
            if setAbbrv not in pricesCache:
                pricesCache[setAbbrv] = {}
            pricesCache[setAbbrv].update(setPrices)

        while not singlesResults.empty():
            setAbbrv, cardKey, priceInfo = singlesResults.get_nowait()
            if setAbbrv not in pricesCache:
                pricesCache[setAbbrv] = {}
            pricesCache[setAbbrv][cardKey] = priceInfo

        while not priceRequests.empty():
            cardName, setName, cardLang, foil, cookie = priceRequests.get_nowait()
            if not foil:
                cardLang = 'en'
            cardLang = core.language.getAbbreviation(cardLang)
            cardKey = getCardKey(cardName, cardLang, foil)
            setAbbrv = card.sets.getAbbreviation(setName)
            if setAbbrv not in pricesCache or cardKey not in pricesCache[setAbbrv]:
                if not foil and setAbbrv not in requestedSets:
                    setsRequests.put(setName)
                    requestedSets.add(setAbbrv)
                elif foil and cardKey not in requestedSingles and cardLang == 'EN':
                    pass  # TODO bypass security restrictions
                    # singlesRequests.put((cardName, setName, cardLang))
                    # requestedSingles.add(cardKey)
            if setAbbrv not in postponedRequests:
                postponedRequests[setAbbrv] = {}
            if cardKey not in postponedRequests[setAbbrv]:
                postponedRequests[setAbbrv][cardKey] = []
            postponedRequests[setAbbrv][cardKey].append(cookie)

        for setAbbrv, cardsDict in postponedRequests.items():
            if setAbbrv in pricesCache:
                fulfilled = set()
                for cardKey, cookiesList in cardsDict.items():
                    if cardKey in pricesCache[setAbbrv]:
                        for cookie in cookiesList:
                            priceResults.put((pricesCache[setAbbrv][cardKey], cookie,))
                        fulfilled.add(cardKey)
                for cardKey in fulfilled:
                    del cardsDict[cardKey]


def tcgObtainSets(requests, results, exitEvent):
    setQueryUrlTemplate = 'http://magic.tcgplayer.com/db/price_guide.asp?setname={}'
    setsPrices = {}
    while True:
        if exitEvent.is_set():
            return

        setFullName = requests.get()
        setAbbrv = card.sets.getAbbreviation(setFullName)
        if setAbbrv not in setsPrices:
            html = lxml.html.document_fromstring(core.network.getUrl(setQueryUrlTemplate.format(urllib.parse.quote(setFullName))))
            tables = html.cssselect('table')
            if tables:
                setsPrices[setAbbrv] = {}
                for resultsEntry in tables[-1].cssselect('tr'):
                    cells = resultsEntry.cssselect('td')
                    if cells and len(cells) >= 5:
                        cellCardNameString = cells[0].cssselect('font')[0].text
                        if cellCardNameString.startswith('&nbsp;'):
                            cellCardNameString = cellCardNameString[6:]
                        cellCardKey = getCardKey(cellCardNameString, 'EN', False)
                        priceString = cells[6].cssselect('font')[0].text
                        if priceString and priceString.startswith('$'):
                            setsPrices[setAbbrv][cellCardKey] = {
                                'price': decimal.Decimal(re.match(r'\$([\d\.]+).*', priceString).group(1)),
                                'currency': core.currency.USD,
                            }
        results.put((setAbbrv, setsPrices[setAbbrv]))


def tcgObtainSingles(requests, results, exitEvent):
    cardQueryUrlTemplate = 'http://shop.tcgplayer.com/magic/{}/{}'
    while True:
        if exitEvent.is_set():
            return

        cardName, setName, cardLang = requests.get()
        tcgSetName = tcgMakeUrlPart(setName)
        tcgCardName = tcgMakeUrlPart(card.utils.escape(cardName))
        priceHtml = lxml.html.document_fromstring(core.network.getUrl(cardQueryUrlTemplate.format(tcgSetName, tcgCardName)))
        for priceBlock in priceHtml.cssselect('.priceGuideClass'):
            foil = priceBlock.cssselect('.cardStyle b')[0].text == 'Foil'
            priceInfo = {
                'price': decimal.Decimal(re.match(r'.*?\$([\d\.]+).*', priceBlock.cssselect('.priceRange .median')[0].text).group(1)),
                'currency': core.currency.USD,
            }
            results.put((card.sets.getAbbreviation(setName), getCardKey(cardName, cardLang, foil), priceInfo,))


def tcgMakeUrlPart(rawString):
    result = []
    for character in rawString.lower():
        replacement = character
        if character == ' ':
            replacement = '-'
        elif character not in string.ascii_letters:
            replacement = ''
        result.append(replacement)
    return ''.join(result)


class TcgPlayer(object):
    def __init__(self, resultsQueue):
        self.fullSetNames = {
            '10E': '10th Edition',
            '9ED': '9th Edition',
            'M10': 'Magic 2010 (M10)',
            'M11': 'Magic 2011 (M11)',
            'M12': 'Magic 2012 (M12)',
            'M13': 'Magic 2013 (M13)',
            'M14': 'Magic 2014 (M14)',
            'M15': 'Magic 2015 (M15)',
            'MD1': 'Magic Modern Event Deck',
            'RAV': 'Ravnica',
            'TST': 'Timeshifted',
        }
        self.resultsPrice = resultsQueue
        self.restart()

    def getTitle(self):
        return 'tcgplayer.com'

    def getFullSetName(self, setId):
        return self.fullSetNames.get(setId, card.sets.getFullName(setId))

    def queryPrice(self, cardName, setId, language, foil, cookie):
        self.requestsPrice.put((cardName, self.getFullSetName(setId), language, foil, cookie))

    def terminate(self):
        self.exitEvent.set()

    def restart(self):
        if hasattr(self, 'exitEvent'):
            self.exitEvent.set()
        self.exitEvent = threading.Event()

        self.requestsPrice = queue.Queue()

        self.requestsSingles = queue.Queue()
        self.resultsSingles = queue.Queue()

        self.requestsSet = queue.Queue()
        self.resultsSet = queue.Queue()

        # self.singlesObtainer = threading.Thread(name='TCG-Singles', target=tcgObtainSingles, args=(self.requestsSingles, self.resultsSingles, self.exitEvent,), daemon=True)
        self.setsObtainer = threading.Thread(name='TCG-Sets', target=tcgObtainSets, args=(self.requestsSet, self.resultsSet, self.exitEvent,), daemon=True)
        self.priceRequestsProcessor = threading.Thread(
            name='TCG-Main',
            target=tcgProcessRequests,
            args=(self.requestsPrice, self.resultsPrice, self.requestsSet, self.resultsSet, self.requestsSingles, self.resultsSingles, self.exitEvent,),
            daemon=True)
        # self.singlesObtainer.start()
        self.setsObtainer.start()
        self.priceRequestsProcessor.start()


def getpricesBySetourceClasses():
    return [
        TcgPlayer,
    ]
