# coding: utf-8

import decimal
import http
import json
import os
import random
import re
import string
import time
import urllib
import urllib.error
import urllib.parse

import lxml.html

import card.sets
import card.utils
import core.currency
import core.language
import core.logger
import core.network
import tools.dict
import tools.string

CONDITIONS_ORDER = ('HP', 'MP', 'SP', 'NM')
_CONDITIONS_SOURCE = {
    'HP': ('Heavily Played', 'Hardly Played', 'ХП',),
    'MP': ('Moderately Played', 'Played', 'МП',),
    'SP': ('Slightly Played', 'СП',),
    'NM': ('Near Mint', 'M/NM', 'M', 'Mint', 'Excellent', 'great', 'НМ',),
}
_CONDITIONS = tools.dict.expandMapping(_CONDITIONS_SOURCE)
_CONDITIONS_CASE_INSENSITIVE = {}
for k, v in _CONDITIONS.items():
    _CONDITIONS_CASE_INSENSITIVE[k.lower()] = v

MTG_RU_SPECIFIC_SETS = {
    'AN': 'Arabian Nights',
    'AQ': 'Antiquities',
    'LE': 'Legions',
    'LG': 'Legends',
    'MI': 'Mirage',
    'MR': 'Mirrodin',
    'P1': 'Portal',
    'P2': 'Portal: Second Age',
    'P3': 'Portal: Three Kingdoms',
    'PC': 'Planar Chaos',
    'PCH': 'Planechase',
    'ST': 'Starter 1999',
    'UG': 'Unglued',
}


def getConditionHumanReadableString(conditionString):
    key = conditionString.lower()
    if key in _CONDITIONS_CASE_INSENSITIVE:
        return _CONDITIONS_SOURCE[_CONDITIONS_CASE_INSENSITIVE[key]][0]

def makeLwLettersKey(value):
    return re.sub(r'\W', '', value.lower())

def guessStringLanguage(value):
    language = None
    nameLetters = makeLwLettersKey(value)
    for abbrv, letters in core.language.LANGUAGES_TO_LOWERCASE_LETTERS.items():
        if all(c in letters for c in nameLetters):
            language = abbrv
            break
    return language


class CardSource(object):
    def __init__(self, url, queryUrlTemplate, queryEncoding, responseEncoding, sourceSpecificSets):
        self.url = url
        self.queryUrlTemplate = url + queryUrlTemplate
        self.sourceSpecificSets = sourceSpecificSets
        self.queryEncoding = queryEncoding
        self.responseEncoding = responseEncoding
        self.foundCardsCount = 0
        self.wasEstimated = False
        self.estimatedCardsCount = None
        self.estimatedCardsPerPageCount = None
        self.requestCache = {}
        self.logger = core.logger.Logger(self.__class__.__name__)
        self.verifySsl = True
        self.currentQuery = None

    def getTitle(self):
        location = urllib.parse.urlparse(self.url).netloc
        return re.sub(r'^www\.', '', location)

    def getSetAbbrv(self, setId):
        result = card.sets.tryGetAbbreviation(self.sourceSpecificSets.get(setId, setId), quiet=True)
        if result is None:
            self.logger.warning('Unable to recognize set "{}" for query "{}"'.format(setId, self.currentQuery))
        return result

    def extractToken(self, pattern, dataString):
        token = None
        match = re.search(pattern, dataString, re.IGNORECASE | re.UNICODE)
        if match is not None:
            token = match.groupdict()['token']
            dataString = re.sub(pattern, '', dataString, count=1)
        return token, dataString

    def escapeQueryText(self, queryText):
        return queryText.replace(u'`', "'").replace(u'’', "'")

    def makeRequest(self, url, data):
        cacheKey = url
        if data:
            cacheKey += ';' + urllib.parse.urlencode(data)
        if cacheKey not in self.requestCache:
            try:
                byteString = core.network.getUrl(url, data, False, self.verifySsl)
                self.requestCache[cacheKey] = lxml.html.document_fromstring(byteString.decode(self.responseEncoding))
            except Exception as ex:
                message = str(ex)
                if len(message) == 0 or message.isspace():
                    raise
                self.logger.warning(message)
        return self.requestCache.get(cacheKey)

    def packName(self, caption, description=None):
        return {'caption': card.utils.escape(card.utils.clean(caption.strip())), 'description': description}

    def makeAbsUrl(self, path):
        return urllib.parse.urljoin(self.url, path)

    def packSource(self, caption, cardUrl=None):
        if cardUrl is not None:
            cardUrl = self.makeAbsUrl(cardUrl)
        result = {'caption': caption, 'url': cardUrl or caption}
        return result

    def fillCardInfo(self, cardInfo):
        self.foundCardsCount += 1
        return cardInfo

    def getFoundCardsCount(self):
        return self.foundCardsCount

    def getEstimatedCardsCount(self):
        return self.estimatedCardsCount

    def query(self, queryText):
        self.currentQuery = queryText

        preloadedCards = self._searchPreloaded(queryText)
        self.estimatedCardsCount = len(preloadedCards)
        for cardInfo in preloadedCards:
            if cardInfo is not None:
                yield cardInfo

        loopIndex = 0
        pageIndex = 0
        pageCount = 0
        while pageIndex <= pageCount:
            pageIndex = loopIndex + 1
            escapedQuery = self.escapeQueryText(queryText)
            try:
                encodedQuery = escapedQuery.encode(self.queryEncoding)
            except UnicodeEncodeError:
                encodedQuery = escapedQuery
            requestUrl = self.queryUrlTemplate.format(**{'query': urllib.parse.quote(encodedQuery), 'page': pageIndex})
            response = self.makeRequest(requestUrl, None)
            if response is None:
                continue

            if not pageCount:
                pageCount = max(1, self._getPageCount(response))
            pageCardsCount = self._getPageCardsCount(response)
            if not self.wasEstimated:
                self.wasEstimated = True
                self.estimatedCardsPerPageCount = pageCardsCount
                if self.estimatedCardsCount is None:
                    self.estimatedCardsCount = 0
                totalCount = self._getTotalCardsCount(response)
                if totalCount is None:
                    totalCount = pageCount * pageCardsCount
                self.estimatedCardsCount += totalCount
            if pageCardsCount < self.estimatedCardsPerPageCount:
                self.estimatedCardsCount -= self.estimatedCardsPerPageCount - pageCardsCount

            pageCards = 0
            for cardInfo in self._parseResponse(queryText, requestUrl, response):
                pageCards += int(cardInfo is not None)
                yield cardInfo
            if pageCards == 0:
                self.estimatedCardsCount = self.foundCardsCount
                yield None
                break

            loopIndex += 1
            pageIndex = loopIndex + 1

    def _getPageCount(self, html):
        return 1

    def _getPageCardsCount(self, html):
        return 0

    def _getTotalCardsCount(self, html):
        return None

    def _parseResponse(self, queryText, url, html):
        yield None

    def _searchPreloaded(self, queryText):
        return []


class AngryBottleGnome(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'Promo - Special': 'Media Inserts',
            'Prerelease Events': 'Prerelease & Release Cards',
            'Release Events': 'Prerelease & Release Cards',
            'Launch Party': 'Magic: The Gathering Launch Parties',
        }
        super().__init__('http://angrybottlegnome.ru', '/shop/search/{query}/filter/instock', 'utf-8', 'utf-8', sourceSpecificSets)
        # <div class = "abg-float-left abg-card-margin abg-card-version-instock">Английский, M/NM  (30р., в наличии: 1)</div>
        # <div class = "abg-float-left abg-card-margin abg-card-version-instock">Итальянский, M/NM  Фойл (180р., в наличии: 1)</div>
        self.cardInfoRegexp = re.compile(r'(?P<language>[^,]+),\s*(?P<condition>[\S]+)\s*(?P<foilness>[^(]+)?\s*\((?P<price>\d+)[^\d]*(?P<count>\d+)\)')

    def escapeQueryText(self, queryText):
        # if query url contains & request will fail
        return super().escapeQueryText(queryText.replace('R&D', '').replace('&', ''))

    def _getPageCardsCount(self, html):
        return len(html.cssselect('#search-results tbody tr'))

    def _parseResponse(self, queryText, url, html):
        searchResults = html.cssselect('#search-results tbody tr')
        for resultsEntry in searchResults:
            dataCells = resultsEntry.cssselect('td')
            cardName = dataCells[0].cssselect('a')[0].text
            cardSet = dataCells[1].cssselect('a')[0].text
            cardUrl = self.makeAbsUrl(dataCells[0].cssselect('a')[0].attrib['href'])
            cardVersionsHtml = lxml.html.document_fromstring(core.network.getUrl(cardUrl))
            cardVersions = cardVersionsHtml.cssselect('.abg-card-version-instock')
            if len(cardVersions) > 0:
                self.estimatedCardsCount += len(cardVersions) - 1  # одну карту уже учли выше
            for cardVersion in cardVersions:
                rawInfo = self.cardInfoRegexp.match(cardVersion.text).groupdict()
                yield self.fillCardInfo({
                    'name': self.packName(cardName),
                    'set': self.getSetAbbrv(cardSet),
                    'language': core.language.getAbbreviation(rawInfo['language']),
                    'condition': _CONDITIONS[rawInfo['condition'].rstrip(',')],
                    'foilness': bool(rawInfo['foilness']),
                    'count': int(rawInfo['count']),
                    'price': decimal.Decimal(rawInfo['price']),
                    'currency': core.currency.RUR,
                    'source': self.packSource(self.getTitle(), cardUrl),
                })


class MtgRuShop(CardSource):
    def __init__(self, url, promoUrl):
        super().__init__(url, '/catalog.phtml?Title={query}&page={page}', 'cp1251', 'cp1251', MTG_RU_SPECIFIC_SETS)
        self.promoUrl = promoUrl
        if self.promoUrl is not None:
            self.promoHtml = self.makeRequest(self.makeAbsUrl(self.promoUrl), None)
        self.entrySelector = '#Catalog tr'

    def _getPageCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('.split-pages a')
        if len(pagesLinks) > 0:
            pagesCount = int(re.match(r'.+page=(\d+).*', pagesLinks[-1].attrib['href']).group(1))
        return pagesCount

    def _getPageCardsCount(self, html):
        return len(html.cssselect(self.entrySelector))

    def _parseResponse(self, queryText, url, html):
        for resultsEntry in html.cssselect(self.entrySelector):
            dataCells = resultsEntry.cssselect('td')
            language = core.language.getAbbreviation(os.path.basename(urllib.parse.urlparse(dataCells[1].cssselect('img')[0].attrib['src']).path))
            nameSelector = 'span.CardName' if language == 'EN' else 'span.Zebra'
            yield self.fillCardInfo({
                'name': self.packName(dataCells[2].cssselect(nameSelector)[0].text),
                'set': self.getSetAbbrv(dataCells[0].cssselect('img')[0].attrib['alt']),
                'language': language,
                'foilness': bool(dataCells[3].text),
                'count': int(re.match(r'(\d+)', dataCells[5].text).group(0)),
                'price': decimal.Decimal(re.match(r'(\d+)', dataCells[6].text.replace('`', '')).group(0)),
                'currency': core.currency.RUR,
                'source': self.packSource(self.getTitle(), url)
            })


class Amberson(MtgRuShop):
    def __init__(self):
        super().__init__('http://amberson.mtg.ru', '3.html')


class ManaPoint(MtgRuShop):
    def __init__(self):
        super().__init__('http://manapoint.mtg.ru', '2.html')
        self.promoSetsSubstrings = {
            ('release', 'launch',): 'Prerelease & Release Cards',
            ('gameday',): 'Magic Game Day Cards',
            ('oversized',): 'Oversized Cards',
            ('buy-a-box', 'fullbox',): 'Misc Promos',
        }

    def _searchPreloaded(self, queryText):
        if self.promoHtml is None:
            return []

        results = []
        for resultsEntry in self.promoHtml.cssselect('table.Catalog tr'):
            dataCells = resultsEntry.cssselect('td')
            cardString = dataCells[0].text

            cardInfo = re.match(r'^(\[.+?\])?(?P<name>[^\[(]+)\s*(\((?P<lang>[^)]+)\))?.+$', cardString).groupdict()
            cardName = cardInfo['name'].split('/')[0].strip()

            if queryText.lower() in cardName.lower():
                cardLang = core.language.tryGetAbbreviation(cardInfo['lang'] or '')
                if cardLang is None:
                    cardLang = core.language.getAbbreviation(guessStringLanguage(card.utils.getNameKey(cardName)))

                propStrings = []
                supported = True # TODO support archenemy & planechase
                foil = False
                setString = None
                for match in re.finditer(r'\[([^\]]+)\]', cardString):
                    propString = match.group(1).lower()
                    if any(s in propString for s in ['archenemy', 'planechase']):
                        supported = False
                    elif propString == 'foil':
                        foil = True
                    elif setString is None:
                        setString = card.sets.tryGetAbbreviation(propString, quiet=True)
                        propStrings.append(propString)

                if supported:
                    if setString is None:
                        for subtuple, subset in self.promoSetsSubstrings.items():
                            for substring in subtuple:
                                if substring in cardString.lower().replace(' ', ''):
                                    setString = subset
                    if setString is None:
                        print('Unable to detect set', propStrings)
                    if setString is not None:
                        setString = self.getSetAbbrv(setString)

                    results.append(self.fillCardInfo({
                        'name': self.packName(cardName),
                        'set': setString,
                        'language': cardLang,
                        'foilness': foil,
                        'count': int(re.match(r'(\d+)', dataCells[1].text).group(0)),
                        'price': decimal.Decimal(re.match(r'(\d+)', dataCells[2].text.replace('`', '')).group(0)),
                        'currency': core.currency.RUR,
                        'source': self.packSource(self.getTitle(), self.promoUrl)
                    }))
        return results

class MtgSale(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'MI': 'Mirrodin',
            'MR': 'Mirage',
            'TP': 'Tempest',
        }
        super().__init__('https://mtgsale.ru', '/home/search-results?Name={query}&Page={page}', 'utf-8', 'utf-8', sourceSpecificSets)
        self.verifySsl = False

    def _getPageCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('ul.tabsb li a')
        if len(pagesLinks) > 0:
            pagesCount = int(pagesLinks[-1].text)
        return pagesCount

    def _getTotalCardsCount(self, html):
        return int(re.match(r'\D*(\d+)\D*', html.cssselect('span.search-number')[0].text).group(1))

    def _getPageCardsCount(self, html):
        return 25

    def _parseResponse(self, queryText, url, html):
        for resultsEntry in html.cssselect('.tab_container div.ctclass'):
            count = int(re.match(r'(\d+)', resultsEntry.cssselect('p.colvo')[0].text).group(0))
            if count <= 0:
                self.estimatedCardsCount -= 1
                yield None
                continue

            nameSelector = 'p.tname .tnamec'
            language = core.language.getAbbreviation(resultsEntry.cssselect('p.lang i')[0].attrib['title'])
            if language is not None and language != 'EN':
                nameSelector = 'p.tname .smallfont'

            entrySet = resultsEntry.cssselect('p.nabor span')[0].attrib['title']
            if not (language or entrySet):
                self.estimatedCardsCount -= 1
                yield None
                continue

            priceString = resultsEntry.cssselect('p.pprice')[0].text
            discountPriceBlocks = resultsEntry.cssselect('p.pprice .discount_price')
            if len(discountPriceBlocks) > 0:
                priceString = discountPriceBlocks[0].text
            price = None
            if priceString and not priceString.isspace():
                price = decimal.Decimal(re.match(r'(\d+)', priceString.strip()).group(0))

            yield self.fillCardInfo({
                'name': self.packName(resultsEntry.cssselect(nameSelector)[0].text),
                'set': self.getSetAbbrv(entrySet),
                'language': language,
                'condition': _CONDITIONS[resultsEntry.cssselect('p.sost span')[0].text],
                'foilness': bool(resultsEntry.cssselect('p.foil')[0].text),
                'count': count,
                'price': price,
                'currency': core.currency.RUR,
                'source': self.packSource(self.getTitle(), url),
            })


class CardPlace(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'DCI Legends': 'Media Inserts',
            'Starter': 'Starter 1999',
            "OverSize Cards": 'Oversized Cards',
            'Premium deck: Graveborn': 'Premium Deck Series: Graveborn',
            'Release & Prerelease cards': 'Prerelease & Release Cards',
            "Commander's Aresnal": "Commander's Arsenal",
        }
        super().__init__('http://cardplace.ru', '/directory/new_search/{query}/singlemtg', 'cp1251', 'utf-8', sourceSpecificSets)
        conditions = {
            'NM': ['nm', 'nm/m', 'm'],
            'SP': ['vf', 'very fine'],
            'MP': ['f', 'fine'],
            'HP': ['poor'],
        }
        self.conditions = {}
        for key, values in conditions.items():
            for valueString in values:
                self.conditions[valueString] = key

    def _getPageCardsCount(self, html):
        return len(html.cssselect('#mtgksingles tbody tr'))

    def _parseResponse(self, queryText, url, html):
        for resultsEntry in html.cssselect('#mtgksingles tbody tr'):
            dataCells = resultsEntry.cssselect('td')

            language = None
            langImages = dataCells[3].cssselect('img')
            if len(langImages) > 0:
                language = core.language.getAbbreviation(os.path.basename(urllib.parse.urlparse(self.url + langImages[0].attrib['src']).path))

            conditionString = None
            for anchor in dataCells[2].cssselect('a'):
                if 'condition_guide' in anchor.attrib['href']:
                    conditionString = anchor.text
            if conditionString is not None:
                conditionString = _CONDITIONS[self.conditions[conditionString.lower()]]

            cardId = None
            cardSet = dataCells[1].cssselect('b')[0].text.strip("'")
            anchorName = dataCells[2].cssselect('a')[0]
            nameString = anchorName.text_content()
            cardName = nameString
            isSpecialPromo = any(s in nameString for s in ['APAC', 'EURO', 'MPS'])
            if not isSpecialPromo:
                cardId, nameString = self.extractToken(r'\s?\(?\#(?P<token>\d+)\)?', nameString)
                promoString, nameString = self.extractToken(r'\s?\((?P<token>(pre)?release)\)', nameString)
                if promoString is not None:
                    cardSet = promoString
                secondaryNameString, primaryNameString = self.extractToken(r'\s?\((?P<token>[^\)]+)\)', nameString)
                cardName = primaryNameString
                if (not language or language != 'EN') and secondaryNameString is not None:
                    cardName = secondaryNameString
                if '(PR)' in cardSet:
                    cardSet = 'Prerelease & Release Cards'

            nameImages = dataCells[2].cssselect('img')

            yield self.fillCardInfo({
                'id': cardId,
                'name': self.packName(cardName),
                'foilness': len(nameImages) > 0 and nameImages[0].attrib['title'].lower() == 'foil',
                'set': self.getSetAbbrv(cardSet),
                'language': language,
                'condition': conditionString,
                'price': decimal.Decimal(re.match(r'([\d.]+)', dataCells[6].text.strip()).group(0)),
                'currency': core.currency.RUR,
                'count': int(re.match(r'(\d+)', dataCells[7].text.strip()).group(0)),
                'source': self.packSource(self.getTitle(), anchorName.attrib['href']),
            })


class MtgRu(CardSource):
    def __init__(self):
        self.sourceSubstringsToExclude = [
            'amberson.mtg.ru',
            'autumnsmagic.com',
            'cardplace.ru',
            'easyboosters.com',
            'manapoint.mtg.ru',
            'mtgsale.ru',
            'mtgtrade.net',
            'myupkeep.ru',
        ]
        self.knownShopSourceSubstrings = []
        super().__init__('http://mtg.ru', '/exchange/card.phtml?Title={query}&Amount=1', 'cp1251', 'cp1251', MTG_RU_SPECIFIC_SETS)

    def escapeQueryText(self, queryText):
        return super().escapeQueryText(queryText)

    def _getPageCardsCount(self, html):
        return len(html.cssselect('table.NoteDivWidth'))

    def _parseResponse(self, queryText, url, html):
        for userEntry in html.cssselect('table.NoteDivWidth'):
            userInfo = userEntry.cssselect('tr table')[0]
            nickname = userInfo.cssselect('tr th')[0].text
            exchangeUrl = userInfo.cssselect('tr td')[-1].cssselect('a')[0].attrib['href']
            if any(source in exchangeUrl.lower() for source in self.sourceSubstringsToExclude):
                self.estimatedCardsCount -= 1
                yield None
            else:
                cardSource = self.getTitle() + '/' + nickname.lower().replace(' ', '_')
                if any(substring in exchangeUrl for substring in self.knownShopSourceSubstrings):
                    cardSource = urllib.parse.urlparse(exchangeUrl).netloc
                elif not exchangeUrl.endswith('.html'):
                    cardSource = exchangeUrl
                    print('Shop found: {}'.format(exchangeUrl))

                userCards = userEntry.cssselect('table.CardInfo')
                if len(userCards) > 0:
                    self.estimatedCardsCount += len(userCards) - 1

                for cardInfo in userCards:
                    idSource = cardInfo.cssselect('nobr.txt0')[0].text
                    cardId = int(re.match(r'[^\d]*(\d+)[^\d]*', idSource).group(1)) if idSource else None

                    price = None
                    priceSource = cardInfo.cssselect('td.txt15')[-1].cssselect('b')
                    if len(priceSource) > 0:
                        possiblePrice = priceSource[-1].text
                        if possiblePrice is not None:
                            possiblePrice = possiblePrice.split()[0]
                            if possiblePrice.isdigit():
                                price = decimal.Decimal(possiblePrice)

                    foilness = len(cardInfo.cssselect('#FoilCard')) > 0

                    language = None
                    languageSource = cardInfo.cssselect('td.txt15')[0].cssselect('font')
                    if len(languageSource) > 0:
                        language = core.language.getAbbreviation(languageSource[0].text)

                    setSource = cardInfo.cssselect('#table0 td img')[0].attrib['alt']

                    yield self.fillCardInfo({
                        'id': cardId,
                        'name': self.packName(cardInfo.cssselect('th.txt0')[0].text),
                        'foilness': foilness,
                        'set': self.getSetAbbrv(setSource),
                        'language': language,
                        'price': price,
                        'currency': core.currency.RUR,
                        'count': int(cardInfo.cssselect('td.txt15 b')[0].text.split()[0]),
                        'source': self.packSource(cardSource, exchangeUrl),
                    })


class TtTopdeck(CardSource):
    def __init__(self):
        super().__init__('http://tt.topdeck.ru', '/?req={query}&mode=sell&group=card', 'utf-8', 'utf-8', {})
        self.excludedSellers = [
            'angrybottlegnome',
            'mtgsale',
        ]

    def _getPageCardsCount(self, html):
        return len(html.cssselect('table table tr')[1:])

    def _parseResponse(self, queryText, url, html):
        for entry in html.cssselect('table table tr')[1:]:
            cells = entry.cssselect('td')
            cardName = cells[3].text
            sellerAnchor = cells[5].cssselect('a')[0]
            sellerNickname = sellerAnchor.text

            if not cardName or sellerNickname in self.excludedSellers:
                self.estimatedCardsCount -= 1
                yield None
                continue

            ttPriceValue = tools.string.parseSpacedInteger(cells[1].text)
            ttCountValue = tools.string.parseSpacedInteger(cells[2].text)
            myPriceValue = None
            myCountValue = None

            cardFoilness = False
            cardSet = None
            cardLanguage = None
            cardCondition = None

            detailsString = None
            rawDetailsString = cells[6].text
            if rawDetailsString:
                detailsString = ' '.join(rawDetailsString.split()).strip()
                if detailsString.isdigit():
                    detailsString = None

            if detailsString is not None:
                dataString = detailsString.lower().replace(cardName.lower(), '')

                foilString, dataString = self.extractToken(r'(?P<token>foil|фо(и|й)л(а|(ов(ый|ая)?)?)?)', dataString)
                cardFoilness = foilString is not None

                prPromoString, dataString = self.extractToken(r'(?P<token>((pre)?release)|((пре)?рел(из)?)|(прер))', dataString)
                if prPromoString is not None:
                    cardSet = 'Prerelease & Release Cards'

                reserveString, dataString = self.extractToken(r'(?P<token>((за)?резерв(ирован(н)?(о|а|ы)?)?)|(reserv(e(d)?)?)|(отложен(н)?(о|а|ы)?))', dataString)
                if reserveString is not None:
                    self.estimatedCardsCount -= 1
                    yield None
                    continue

                rawMyCountString, dataString = self.extractToken(r'(x|х)?\s*(?P<token>\d+)(?!(р(уб)?|\d))(\s|-)*(x|х|(шт\.?))?', dataString)
                rawMyPriceString, dataString = self.extractToken(r'(?P<token>\d{1,2}\s?\d*)(р(уб)?\.*(\/?шт\.?)?)?', dataString)
                myCountValue = tools.string.parseSpacedInteger(rawMyCountString)
                myPriceValue = tools.string.parseSpacedInteger(rawMyPriceString)

                if myPriceValue == ttPriceValue and myCountValue is None:
                    myCountValue = 1

                if myCountValue == ttPriceValue:
                    myCountValue = ttCountValue
                    myPriceValue = ttPriceValue

                if myCountValue > 20 > myPriceValue:
                    myCountValue, myPriceValue = myPriceValue, myCountValue

                foundLangsNum = 0
                langCluster = None
                for cluster in tools.string.splitByNonLetters(dataString):
                    langAbbrv = core.language.tryGetAbbreviation(cluster)
                    if langAbbrv is not None:
                        langCluster = cluster
                        cardLanguage = langAbbrv
                        foundLangsNum += 1
                if foundLangsNum == 1:
                    dataString = dataString.replace(langCluster, '')
                else:
                    cardLanguage = None

                foundConditions = set()
                for cluster in tools.string.splitByNonLetters(dataString):
                    lc = cluster.lower()
                    if lc in _CONDITIONS_CASE_INSENSITIVE:
                        foundConditions.add(_CONDITIONS_CASE_INSENSITIVE[lc])
                if len(foundConditions) > 0:
                    cardCondition = sorted(foundConditions, key=CONDITIONS_ORDER.index)[0]

            if myCountValue is None or myPriceValue is None:
                myCountValue = ttCountValue
                myPriceValue = ttPriceValue

            if myCountValue == 0:
                self.estimatedCardsCount -= 1
                yield None
                continue

            if cardSet is not None:
                cardSet = self.getSetAbbrv(cardSet)

            yield self.fillCardInfo({
                'name': self.packName(cardName, detailsString),
                'foilness': cardFoilness,
                'set': cardSet,
                'language': cardLanguage,
                'price': decimal.Decimal(myPriceValue),
                'currency': core.currency.RUR,
                'count': myCountValue,
                'condition': cardCondition,
                'source': self.packSource('topdeck.ru/' + sellerNickname.lower().replace(' ', '_'), sellerAnchor.attrib['href']),
            })


class EasyBoosters(CardSource):
    def __init__(self):
        super().__init__('https://easyboosters.com', '/search/?q={query}&how=r&PAGEN_3={page}', 'utf-8', 'utf-8', {})

    def _getPageCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('.bx-pagination li a')
        if len(pagesLinks) > 0:
            pagesCount = int(re.match(r'.+PAGEN_3=(\d+).*', pagesLinks[-1].attrib['href']).group(1))
        return pagesCount

    def _getPageCardsCount(self, html):
        return len(html.cssselect('.super-offer'))

    def _parseResponse(self, queryText, url, html):
        for entry in html.cssselect('.product-item'):
            offers = entry.cssselect('.super-offer')
            if len(offers) == 0:
                continue

            anchor = entry.cssselect('.product-item-title a')[0]
            cardUrl = anchor.attrib['href']
            cardPage = lxml.html.document_fromstring(core.network.getUrl(self.makeAbsUrl(cardUrl)))

            cardProps = cardPage.cssselect('.product-item-detail-properties')[0]
            tokenIndex = -1
            for i, dt in enumerate(cardProps.cssselect('dt')):
                if dt.text == 'Токен':
                    tokenIndex = i
                    break
            if tokenIndex >= 0 and cardProps.cssselect('dd')[tokenIndex].text.strip() == 'Да':
                self.estimatedCardsCount -= 1
                yield None
                continue

            cardName, foilString = re.match(r'^(.+?)(\s\(Foil\))?$', anchor.attrib['title']).groups()
            for offer in offers:
                condition, *language = offer.cssselect('.super-offer-name')[0].text.split()
                yield self.fillCardInfo({
                    'name': self.packName(cardName),
                    'foilness': foilString is not None,
                    'set': self.getSetAbbrv(cardPage.cssselect('.bx-breadcrumb-item a span')[-1].text),
                    'language': core.language.getAbbreviation(''.join(language)),
                    'price': decimal.Decimal(re.match(r'(\d+)', offer.cssselect('.offer-price')[0].text.strip()).group(0)),
                    'currency': core.currency.RUR,
                    'count': int(re.search(r'(\d+)', offer.cssselect('.super-offer span strong')[0].text).group(0)),
                    'condition': _CONDITIONS[condition],
                    'source': self.packSource(self.getTitle(), anchor.attrib['href'])
                })


class MtgTradeShop(CardSource):
    def __init__(self, shopUrl, sourceSubstringsToExclude):
        super().__init__(shopUrl, '/search/?query={query}', 'utf-8', 'utf-8', {})
        self.cardSelector = 'table.search-card tbody tr'
        self.sourceSubstringsToExclude = set(sourceSubstringsToExclude + [
            'ambersonmtg',
        ])

    def makeRequest(self, url, data):
        result = lxml.html.document_fromstring('<html/>')
        try:
            result = super().makeRequest(url, data)
        except urllib.error.HTTPError as ex:
            if not core.network.httpCodeAnyOf(ex.code, [http.HTTPStatus.INTERNAL_SERVER_ERROR]):
                raise
        return result

    def _getPageCardsCount(self, html):
        return len(html.cssselect(self.cardSelector))

    def _parseResponse(self, queryText, url, html):
        for resultsEntry in html.cssselect('.search-item'):
            anchor = resultsEntry.cssselect('.search-title')[0]
            isSingle = '/single/' in anchor.attrib['href']

            isToken = False
            for p in resultsEntry.cssselect('p'):
                if 'Token' in p.text:
                    isToken = True
                    break

            if not isSingle or isToken:
                self.estimatedCardsCount -= len(resultsEntry.cssselect(self.cardSelector))
                yield None
                continue

            for cardsGroup in resultsEntry.cssselect('table.search-card'):
                sellerBlock = cardsGroup.cssselect('td.user-name-td')[0]

                sellerNickname = None
                sellerNameBlocks = sellerBlock.cssselect('div.trader-name')
                if len(sellerNameBlocks) > 0:
                    sellerNickname = sellerNameBlocks[0].text.strip()
                if not sellerNickname:
                    sellerNickname = sellerBlock.cssselect('a')[0].text
                if any(source in sellerNickname.lower() for source in self.sourceSubstringsToExclude):
                    self.estimatedCardsCount -= 1
                    yield None
                    continue

                sourceCaption = self.getTitle()
                if sourceCaption != sellerNickname:
                    sourceCaption = '{}/{}'.format(sourceCaption, sellerNickname)

                for cardEntry in cardsGroup.cssselect('tbody tr'):
                    condition = None
                    conditionBlocks = cardEntry.cssselect('.js-card-quality-tooltip')
                    if len(conditionBlocks) > 0:
                        condition = _CONDITIONS[cardEntry.cssselect('.js-card-quality-tooltip')[0].text]

                    cardSet = cardEntry.cssselect('.choose-set')[0].attrib['title']
                    if 'mtgo' in cardSet.lower():
                        self.estimatedCardsCount -= 1
                        yield None
                        continue
                    yield self.fillCardInfo({
                        'name': self.packName(' '.join(anchor.text_content().split())),
                        'foilness': len(cardEntry.cssselect('img.foil')) > 0,
                        'set': self.getSetAbbrv(cardSet),
                        'language': core.language.getAbbreviation(''.join(cardEntry.cssselect('td .card-properties')[0].text.split()).strip('|"')),
                        'price': decimal.Decimal(''.join(cardEntry.cssselect('.catalog-rate-price b')[0].text.split()).strip('" ')),
                        'currency': core.currency.RUR,
                        'count': int(cardEntry.cssselect('td .sale-count')[0].text.strip()),
                        'condition': condition,
                        'source': self.packSource(sourceCaption, anchor.attrib['href'])
                    })


class MtgTrade(MtgTradeShop):
    def __init__(self):
        super().__init__('http://mtgtrade.net', ['bigmagic', 'upkeep'])


class BigMagic(MtgTradeShop):
    def __init__(self):
        super().__init__('http://bigmagic.ru', [])


class MyUpKeep(MtgTradeShop):
    def __init__(self):
        super().__init__('http://myupkeep.ru', [])


class MtgShopRu(MtgTradeShop):
    def __init__(self):
        super().__init__('http://mtgshop.ru', [])

class AutumnsMagic(CardSource):
    def __init__(self):
        super().__init__('http://autumnsmagic.com', '/catalog?search={query}&page={page}', 'utf-8', 'utf-8', {})

    def _getPageCount(self, html):
        result = 1
        pagesElements = html.cssselect('.allPages')
        if pagesElements:
            result = int(pagesElements[-1].text_content().split()[-1].strip())
        return result

    def _getPageCardsCount(self, html):
        return len(html.cssselect('.product-wrapper'))

    def _parseResponse(self, queryText, url, html):
        for entry in html.cssselect('.product-wrapper'):
            cardUrl = entry.cssselect('a')[0].attrib['href']
            if any((c not in string.printable) for c in cardUrl):
                self.estimatedCardsCount -= 1
                yield None
                continue

            nameTags = entry.cssselect('.card-name')
            if len(nameTags) == 0:
                self.estimatedCardsCount -= 1
                yield None
                continue
            cardName = nameTags[0].cssselect('a')[0].text.strip()

            dscBlock = entry.cssselect('.product-description')[0]
            dscImages = dscBlock.cssselect('img')

            language = None
            lngTitles = [img.attrib['title'] for img in dscImages if 'flags' in img.attrib['src']]
            if len(lngTitles) > 0:
                language = lngTitles[0]
            if not language:
                language = guessStringLanguage(cardName)
            if language:
                language = core.language.getAbbreviation(language)
            if language.lower() == guessStringLanguage(queryText) == 'en' and makeLwLettersKey(queryText) not in makeLwLettersKey(cardName):
                self.estimatedCardsCount -= 1
                yield None
                continue

            countTag = [tag for tag in dscBlock.cssselect('span') if 'шт' in tag.text][0]
            priceTag = entry.cssselect('.product-footer .product-price .product-default-price')[0]

            yield self.fillCardInfo({
                'name': self.packName(cardName),
                'set': self.getSetAbbrv(dscBlock.cssselect('i')[0].attrib['class'].split()[1][len('ss-'):]),
                'language': language,
                'foilness': len([img for img in dscImages if 'foil' in img.attrib['src']]) > 0,
                'count': int(re.match(r'^([\d]+).*', countTag.text.replace(' ', '')).group(1)),
                'price': decimal.Decimal(re.match(r'.*?([\d ]+).*', priceTag.text.strip()).group(1).replace(' ', '')),
                'currency': core.currency.RUR,
                'source': self.packSource(self.getTitle(), cardUrl),
            })


class HexproofRu(CardSource):
    def __init__(self):
        super().__init__('https://hexproof.ru', '/search?type=product&q={query}', 'utf-8', 'utf-8', {})

    def _getPageCount(self, html):
        return 1

    @staticmethod
    def _listEntries(html):
        return html.cssselect('.productgrid--items')[0].cssselect('.productgrid--item')

    def _getPageCardsCount(self, html):
        return len(self._listEntries(html))

    def _parseResponse(self, queryText, url, html):
        for entry in self._listEntries(html):
            product = entry.cssselect('.productitem')[0]
            cardData = json.loads(entry.cssselect('.productitem-quickshop script')[0].text)['product']
            cardSet = self.getSetAbbrv(re.match(r'^set_(.+)$', cardData['type']).group(1))
            for variant in cardData['variants']:
                if variant['available'] and variant['inventory_quantity'] > 0:
                    rawCnd, rawLng = variant['title'].split()
                    yield self.fillCardInfo({
                        'name': self.packName(cardData['title']),
                        'set': cardSet,
                        'language': core.language.getAbbreviation(rawLng),
                        'price': decimal.Decimal(cardData['price_max'] / 100),
                        'currency': core.currency.RUR,
                        'count': int(variant['inventory_quantity']),
                        'condition': _CONDITIONS[rawCnd],
                        'source': self.packSource(self.getTitle(), product.cssselect('.productitem--title a')[0].attrib['href']),
                    })


class OfflineTestSource(CardSource):
    def __init__(self):
        super().__init__('http://offline.shop', '?query={query}', 'utf-8', 'utf-8', {})

    def query(self, queryText):
        self.estimatedCardsCount = random.randint(1, 10)
        for _ in range(self.estimatedCardsCount):
            if bool(random.randint(0, 1)):
                time.sleep(random.randint(0, 1))
            # noinspection PyProtectedMember
            yield self.fillCardInfo({
                'id': random.randint(1, 300),
                'name': self.packName(random.choice(string.ascii_letters) * random.randint(10, 25)),
                'foilness': bool(random.randint(0, 1)),
                'set': random.choice(list(card.sets._SET_ABBREVIATIONS_SOURCE.keys())),
                'language': core.language.getAbbreviation(random.choice(list(core.language._LANGUAGES.keys()))),
                'price': decimal.Decimal(random.randint(10, 1000)) if bool(random.randint(0, 1)) else None,
                'currency': random.choice([core.currency.RUR, core.currency.USD, core.currency.EUR]),
                'count': random.randint(1, 10),
                'condition': _CONDITIONS[random.choice(list(_CONDITIONS.keys()))],
                'source': self.packSource(self.getTitle(), '')
            })


def getCardSourceClasses():
    classes = [
        Amberson,
        AngryBottleGnome,
        AutumnsMagic,
        BigMagic,
        CardPlace,
        EasyBoosters,
        HexproofRu,
        ManaPoint,
        MtgRu,
        MtgSale,
        MtgTrade,
        MyUpKeep,
        MtgShopRu,
        TtTopdeck,
    ]
    random.shuffle(classes)
    return classes
