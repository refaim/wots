import decimal
import functools
import lxml.html
import queue
import re
import string
import sys
import threading
import urllib.parse

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtWebKitWidgets

import card.sets
import card.utils
import core.currency
import core.language
import core.logger
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
            cardName, setAbbrv, setName, cardLang, foil, cookie = priceRequests.get_nowait()
            if not foil:
                cardLang = 'en'
            cardLang = core.language.getAbbreviation(cardLang)
            cardKey = getCardKey(cardName, cardLang, foil)
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


def tcgObtainHtml(requests, results, exitEvent, logger):
    application = QtWidgets.QApplication(sys.argv)
    browser = QtWebKitWidgets.QWebView()
    browserLock = threading.Lock()
    browserTimer = QtCore.QTimer()
    browserTimer.timeout.connect(functools.partial(tcgObtainHtmlWaitData, browser, browserLock, results, exitEvent, logger))
    browserTimer.start(100)
    workTimer = QtCore.QTimer()
    workTimer.timeout.connect(functools.partial(tcgObtainHtmlProcessRequests, workTimer, browser, browserLock, requests, exitEvent, logger))
    workTimer.start(100)
    application.exec_()


def tcgObtainHtmlProcessRequests(timer, browser, browserLock, requests, exitEvent, logger):
    if exitEvent.is_set():
        QtWidgets.QApplication.quit()
        # TODO stop timer?
        # TODO send signal to application object

    if not browserLock.acquire(blocking=False):
        return

    try:
        qualifiedUrl = requests.get_nowait()
    except queue.Empty:
        browserLock.release()
        return

    logger.info('Loading [GET] {}'.format(qualifiedUrl))
    browser.load(QtCore.QUrl(qualifiedUrl))


def tcgObtainHtmlWaitData(browser, browserLock, results, exitEvent, logger):
    if exitEvent.is_set():
        QtWidgets.QApplication.quit()
        # TODO stop timer?
        # TODO send signal to application object

    htmlString = browser.page().mainFrame().toHtml()
    if len(htmlString) > 30 * 1024:
        results.put(htmlString)
        logger.info('Finished [GET] {}'.format(str(browser.url())))
        browser.setUrl(QtCore.QUrl(''))
        browserLock.release()


def tcgObtainSets(priceRequests, priceResults, htmlRequests, htmlResults, exitEvent, logger):
    setsPrices = {}
    setQueryUrlTemplate = 'http://shop.tcgplayer.com/price-guide/magic/{}'
    while True:
        if exitEvent.is_set():
            return

        htmlString = None
        try:
            htmlString = htmlResults.get_nowait()
        except queue.Empty:
            pass
        if htmlString is not None:
            html = lxml.html.document_fromstring(htmlString)
            setNameString = re.match(r'Magic: The Gathering - (.+?)Price Guide', html.cssselect('title')[0].text).group(1).strip()
            setAbbrv = card.sets.tryGetAbbreviation(setNameString)
            setsPrices[setAbbrv] = {}
            for row in html.cssselect('table.priceGuideTable tr'):
                cardUrls = row.cssselect('.productDetail a')
                if cardUrls:
                    cellCardKey = getCardKey(cardUrls[0].text, 'EN', False)
                    priceString = row.cssselect('.medianPrice .cellWrapper')[0].text
                    setsPrices[setAbbrv][cellCardKey] = {
                        'price': decimal.Decimal(re.match(r'\s*\$([\d\.]+).*', priceString).group(1)),
                        'currency': core.currency.USD,
                    }
            priceResults.put((setAbbrv, setsPrices[setAbbrv]))

        try:
            setFullName = priceRequests.get_nowait()
        except queue.Empty:
            continue
        setAbbrv = card.sets.tryGetAbbreviation(setFullName)
        if setAbbrv not in setsPrices:
            qualifiedUrl = setQueryUrlTemplate.format(urllib.parse.quote(setFullName.lower()))
            htmlRequests.put(qualifiedUrl)


# def tcgObtainSingles(requests, results, exitEvent):
#     cardQueryUrlTemplate = 'http://shop.tcgplayer.com/magic/{}/{}'
#     while True:
#         if exitEvent.is_set():
#             return

#         cardName, setName, cardLang = requests.get()
#         tcgSetName = tcgMakeUrlPart(setName)
#         tcgCardName = tcgMakeUrlPart(card.utils.escape(cardName))
#         priceHtml = lxml.html.document_fromstring(core.network.getUrl(cardQueryUrlTemplate.format(tcgSetName, tcgCardName)))
#         for priceBlock in priceHtml.cssselect('.priceGuideClass'):
#             foil = priceBlock.cssselect('.cardStyle b')[0].text == 'Foil'
#             priceInfo = {
#                 'price': decimal.Decimal(re.match(r'.*?\$([\d\.]+).*', priceBlock.cssselect('.priceRange .median')[0].text).group(1)),
#                 'currency': core.currency.USD,
#             }
#             results.put((card.sets.tryGetAbbreviation(setName), getCardKey(cardName, cardLang, foil), priceInfo,))


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
            'FNM': 'FNM Promos',
            'M10': 'Magic 2010 (M10)',
            'M11': 'Magic 2011 (M11)',
            'M12': 'Magic 2012 (M12)',
            'M13': 'Magic 2013 (M13)',
            'M14': 'Magic 2014 (M14)',
            'M15': 'Magic 2015 (M15)',
            'MD1': 'Magic Modern Event Deck',
            'MGD': 'Game Day Promos',
            'RAV': 'Ravnica',
            'TST': 'Timeshifted',
        }
        self.priceResults = resultsQueue
        self.logger = core.logger.Logger('TcgPlayer')
        self.restart()

    def getTitle(self):
        return 'tcgplayer.com'

    def getFullSetName(self, setId):
        return self.fullSetNames.get(setId, card.sets.getFullName(setId))

    def queryPrice(self, cardName, setId, language, foil, cookie):
        self.priceRequests.put((cardName, setId, self.getFullSetName(setId), language, foil, cookie))

    def terminate(self):
        self.exitEvent.set()

    def restart(self):
        if hasattr(self, 'exitEvent'):
            self.exitEvent.set()
        self.exitEvent = threading.Event()
        self.priceRequests = queue.Queue()
        self.singlesRequests = queue.Queue()
        self.singlesResults = queue.Queue()
        self.setsRequests = queue.Queue()
        self.setsResults = queue.Queue()
        self.htmlRequests = queue.Queue()
        self.htmlResults = queue.Queue()

        self.htmlObtainer = threading.Thread(name='TCG-Html', target=tcgObtainHtml, args=(self.htmlRequests, self.htmlResults, self.exitEvent, self.logger,))
        # self.singlesObtainer = threading.Thread(name='TCG-Singles', target=tcgObtainSingles, args=(self.singlesRequests, self.singlesResults, self.exitEvent,), daemon=True)
        self.setsObtainer = threading.Thread(name='TCG-Sets', target=tcgObtainSets, args=(self.setsRequests, self.setsResults, self.htmlRequests, self.htmlResults, self.exitEvent, self.logger,), daemon=True)
        self.priceRequestsProcessor = threading.Thread(
            name='TCG-Main',
            target=tcgProcessRequests,
            args=(self.priceRequests, self.priceResults, self.setsRequests, self.setsResults, self.singlesRequests, self.singlesResults, self.exitEvent,),
            daemon=True)
        # self.singlesObtainer.start()
        self.htmlObtainer.start()
        self.setsObtainer.start()
        self.priceRequestsProcessor.start()


def getpricesBySetourceClasses():
    return [
        TcgPlayer,
    ]
