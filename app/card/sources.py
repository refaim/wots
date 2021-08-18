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
from typing import List, Optional, Tuple

import lxml.html

import core.network
from card.components import SetOracle, ConditionOracle, LanguageOracle
from card.utils import CardUtils
from core.utils import ILogger, load_json_resource, StringUtils, LangUtils


class CardSource(object):
    def __init__(self, logger: ILogger, url: str, queryUrlTemplate: str, queryEncoding: str = 'utf-8', responseEncoding: str = 'utf-8', setMap=None):
        self.url = url
        self.queryUrlTemplate = url + queryUrlTemplate
        self.sourceSpecificSets = setMap or {}
        self.queryEncoding = queryEncoding
        self.responseEncoding = responseEncoding
        self.foundCardsCount = 0
        self.wasEstimated = False
        self.estimatedCardsCount = None
        self.estimatedCardsPerPageCount = None
        self.requestCache = {}
        self.verifySsl = True
        self.currentQuery = None
        self.logger = logger.get_child(self.getTitle())
        self.langOracle = LanguageOracle(self.logger, thorough=False)
        self.setOracle = SetOracle(self.logger, thorough=False)
        self.conditionOracle = ConditionOracle(self.logger, thorough=False)

    def getTitle(self):
        location = urllib.parse.urlparse(self.url).netloc
        return re.sub(r'^www\.', '', location)

    @staticmethod
    def extractToken(pattern, dataString):
        flags = re.IGNORECASE | re.UNICODE
        token = None
        match = re.search(pattern, dataString, flags)
        if match is not None:
            token = match.groupdict()['token']
            dataString = re.sub(pattern, '', dataString, count=1, flags=flags)
        return token, dataString

    def escapeQueryText(self, queryText):
        return queryText.replace(u'`', "'").replace(u'’', "'")

    def getHtml(self, url: str):
        url = self.makeAbsUrl(url)
        if url not in self.requestCache:
            byteString = core.network.getUrl(url, self.logger, None, False, self.verifySsl)
            self.requestCache[url] = lxml.html.document_fromstring(byteString.decode(self.responseEncoding))
        return self.requestCache.get(url)

    @staticmethod
    def packName(caption, description=None):
        return {'caption': caption.strip(), 'description': description}

    def makeAbsUrl(self, path):
        return urllib.parse.urljoin(self.url, path)

    def packSource(self, caption, cardUrl=None):
        if cardUrl is not None:
            cardUrl = self.makeAbsUrl(cardUrl)
        result = {'caption': caption, 'url': cardUrl or caption}
        return result

    def __fillCardInfo(self, cardInfo: dict) -> dict:
        cardInfo.setdefault('language', None)
        if isinstance(cardInfo['name'], str):
            cardInfo['name'] = self.packName(cardInfo['name'])
        if cardInfo.get('condition') is not None:
            cardInfo['condition'] = self.conditionOracle.get_abbreviation(cardInfo['condition'])
        if cardInfo.get('set') is not None:
            cardInfo['set'] = self.setOracle.get_abbreviation(self.sourceSpecificSets.get(cardInfo['set'], cardInfo['set']))
        if cardInfo.get('language') is not None:
            cardInfo['language'] = self.langOracle.get_abbreviation(cardInfo['language'])
        if isinstance(cardInfo['source'], str):
            cardInfo['source'] = self.packSource(self.getTitle(), cardInfo['source'])
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
                yield self.__fillCardInfo(cardInfo)

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
            response = self.getHtml(requestUrl)
            if response is None:
                continue

            if not pageCount:
                pageCount = max(1, self._getPageCount(response))
            expectedPageCardsCount = self._getPageCardsCount(response)
            if not self.wasEstimated:
                self.wasEstimated = True
                self.estimatedCardsPerPageCount = expectedPageCardsCount
                if self.estimatedCardsCount is None:
                    self.estimatedCardsCount = 0
                totalCount = self._getTotalCardsCount(response)
                if totalCount is None:
                    totalCount = pageCount * expectedPageCardsCount
                self.estimatedCardsCount += totalCount
            if expectedPageCardsCount < self.estimatedCardsPerPageCount:
                self.estimatedCardsCount -= self.estimatedCardsPerPageCount - expectedPageCardsCount

            pageCards = 0
            for cardInfo in self._parseResponse(queryText, requestUrl, response):
                if isinstance(cardInfo, dict):
                    # noinspection PyTypeChecker
                    cardInfo = self.__fillCardInfo(cardInfo)
                    pageCards += 1
                elif isinstance(cardInfo, int):
                    self.estimatedCardsCount -= cardInfo
                    cardInfo = None
                elif cardInfo is None:
                    self.estimatedCardsCount -= 1
                else:
                    raise Exception('Unhandled card info type')
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

    @staticmethod
    def _isCardUnrelated(cardName: str, queryText: str) -> bool:
        return LangUtils.guess_language(cardName) == LangUtils.guess_language(queryText) \
               and StringUtils.letters(queryText).lower() not in StringUtils.letters(cardName).lower()


class AngryBottleGnome(CardSource):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://angrybottlegnome.ru', '/shop/search/{query}/filter/instock', setMap={'Promo - Special': 'Media Inserts'})
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
            cardVersionsHtml = self.getHtml(cardUrl)
            cardVersions = cardVersionsHtml.cssselect('.abg-card-version-instock')
            if len(cardVersions) > 0:
                self.estimatedCardsCount += len(cardVersions) - 1  # одну карту уже учли выше
            for cardVersion in cardVersions:
                rawInfo = self.cardInfoRegexp.match(cardVersion.text).groupdict()
                yield {
                    'name': cardName,
                    'set': cardSet,
                    'language': rawInfo['language'],
                    'condition': rawInfo['condition'].rstrip(','),
                    'foilness': bool(rawInfo['foilness']),
                    'count': int(rawInfo['count']),
                    'price': decimal.Decimal(rawInfo['price']),
                    'currency': core.utils.Currency.RUR,
                    'source': cardUrl,
                }


class MtgRuShop(CardSource):
    def __init__(self, logger: ILogger, url: str, promoUrl: str):
        super().__init__(logger, url, '/catalog.phtml?Title={query}&page={page}', 'cp1251', 'cp1251', MtgRu.SPECIFIC_SETS)
        self.promoUrl = promoUrl
        if self.promoUrl is not None:
            self.promoHtml = self.getHtml(self.makeAbsUrl(self.promoUrl))
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
            langImage = os.path.basename(urllib.parse.urlparse(dataCells[1].cssselect('img')[0].attrib['src']).path)
            language = self.langOracle.get_abbreviation(os.path.splitext(langImage)[0])
            nameSelector = 'span.CardName' if language == 'EN' else 'span.Zebra'
            yield {
                'name': dataCells[2].cssselect(nameSelector)[0].text,
                'set': dataCells[0].cssselect('img')[0].attrib['alt'],
                'language': language,
                'foilness': bool(dataCells[3].text),
                'count': int(re.match(r'(\d+)', dataCells[5].text).group(0)),
                'price': decimal.Decimal(re.match(r'(\d+)', dataCells[6].text.replace('`', '')).group(0)),
                'currency': core.utils.Currency.RUR,
                'source': url,
            }


class ManaPoint(MtgRuShop):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://manapoint.mtg.ru', '2.html')
        # TODO move to json
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

            cardInfo = re.match(r'^(\[.+?])?(?P<name>[^\[(]+)\s*(\((?P<lang>[^)]+)\))?.+$', cardString).groupdict()
            cardName = cardInfo['name'].split('/')[0].strip()

            if queryText.lower() in cardName.lower():
                cardLang = self.langOracle.get_abbreviation(cardInfo['lang'] or '', quiet=True)
                if cardLang is None:
                    cardLang = LangUtils.guess_language(CardUtils.make_key(cardName))

                propStrings = []
                supported = True  # TODO support archenemy & planechase
                foil = False
                setString = None
                for match in re.finditer(r'\[([^]]+)]', cardString):
                    propString = match.group(1).lower()
                    if any(s in propString for s in ['archenemy', 'planechase']):
                        supported = False
                    elif propString == 'foil':
                        foil = True
                    elif setString is None:
                        setString = self.setOracle.get_abbreviation(propString, quiet=True)
                        propStrings.append(propString)

                if supported:
                    if setString is None:
                        for subtuple, subset in self.promoSetsSubstrings.items():
                            for substring in subtuple:
                                if substring in cardString.lower().replace(' ', ''):
                                    setString = subset
                    if setString is None:
                        print('Unable to detect set', propStrings)

                    results.append({
                        'name': cardName,
                        'set': setString,
                        'language': cardLang,
                        'foilness': foil,
                        'count': int(re.match(r'(\d+)', dataCells[1].text).group(0)),
                        'price': decimal.Decimal(re.match(r'(\d+)', dataCells[2].text.replace('`', '')).group(0)),
                        'currency': core.utils.Currency.RUR,
                        'source': self.promoUrl,
                    })
        return results


class MtgSale(CardSource):
    def __init__(self, logger: ILogger):
        sourceSpecificSets = {
            'MI': 'Mirrodin',
            'MR': 'Mirage',
            'TP': 'Tempest',
        }
        super().__init__(logger, 'https://mtgsale.ru', '/home/search-results?Name={query}&Page={page}', setMap=sourceSpecificSets)
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
                yield None
                continue

            nameSelector = 'p.tname .tnamec'
            language = self.langOracle.get_abbreviation(resultsEntry.cssselect('p.lang i')[0].attrib['title'])
            if language is not None and language != 'EN':
                nameSelector = 'p.tname .smallfont'

            entrySet = resultsEntry.cssselect('p.nabor span')[0].attrib['title']
            if not (language or entrySet):
                yield None
                continue

            priceString = resultsEntry.cssselect('p.pprice')[0].text
            discountPriceBlocks = resultsEntry.cssselect('p.pprice .discount_price')
            if len(discountPriceBlocks) > 0:
                priceString = discountPriceBlocks[0].text
            price = None
            if priceString and not priceString.isspace():
                price = decimal.Decimal(re.match(r'(\d+)', priceString.strip()).group(0))

            yield {
                'name': resultsEntry.cssselect(nameSelector)[0].text,
                'set': entrySet,
                'language': language,
                'condition': resultsEntry.cssselect('p.sost span')[0].text,
                'foilness': bool(resultsEntry.cssselect('p.foil')[0].text),
                'count': count,
                'price': price,
                'currency': core.utils.Currency.RUR,
                'source': url,
            }


class CardPlace(CardSource):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://cardplace.ru', '/directory/new_search/{query}/singlemtg', queryEncoding='cp1251', setMap={'DCI Legends': 'Media Inserts'})

    def _getPageCardsCount(self, html):
        return len(html.cssselect('#mtgksingles tbody tr'))

    def _parseResponse(self, queryText, url, html):
        for resultsEntry in html.cssselect('#mtgksingles tbody tr'):

            cardCount = 0
            countBlocks = resultsEntry.cssselect('td.t_s_count ul.count_cart_list li')
            if len(countBlocks) > 0:
                cardCount = int(countBlocks[-1].text)

            if cardCount == 0:
                yield None
                continue

            cardLanguage = None
            languageBlocks = resultsEntry.cssselect('td.t_s_flag img')
            if len(languageBlocks) > 0:
                cardLanguage = languageBlocks[0].attrib['title']

            cardNameAnchors = resultsEntry.cssselect('td.t_s_name a')
            secondaryNameString, primaryNameString = self.extractToken(r'\s?\((?P<token>[^\)]+)\)', cardNameAnchors[0].text)
            cardName = primaryNameString
            if cardLanguage != 'Английский' and secondaryNameString is not None:
                cardName = secondaryNameString

            cardCondition = 'NM'
            if len(cardNameAnchors) > 1:
                conditionAnchor = cardNameAnchors[1]
                if 'condition_guide' in conditionAnchor.attrib['href']:
                    cardCondition = conditionAnchor.text

            cardNameImages = resultsEntry.cssselect('td.t_s_name img')

            yield {
                'name': cardName,
                'foilness': len(cardNameImages) > 0 and cardNameImages[0].attrib['title'].lower() == 'foil',
                'set': resultsEntry.cssselect('td.t_s_edition')[0].text_content(),
                'language': cardLanguage,
                'condition': cardCondition,
                'price': decimal.Decimal(resultsEntry.cssselect('td.t_s_price input')[0].attrib['value']),
                'currency': core.utils.Currency.RUR,
                'count': cardCount,
                'source': cardNameAnchors[0].attrib['href'],
            }


class MtgRu(CardSource):
    SPECIFIC_SETS = {
        'AN': 'Arabian Nights',
        'AQ': 'Antiquities',
        'LE': 'Legions',
        'LG': 'Legends',
        'MI': 'Mirage',
        'MR': 'Mirrodin',
        'PC': 'Planar Chaos',
        'PCH': 'Planechase',
        'ST': 'Starter 1999',
    }

    def __init__(self, logger: ILogger):
        self.sourceSubstringsToExclude = [
            'autumnsmagic.com',
            'cardplace.ru',
            'manapoint.mtg.ru',
            'mtgsale.ru',
            'mtgshop',
            'mtgtrade.net',
            'myupkeep.ru',
        ]
        super().__init__(logger, 'http://mtg.ru', '/exchange/card.phtml?Title={query}&Amount=1', 'cp1251', 'cp1251', self.SPECIFIC_SETS)

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
                yield None
            else:
                shopFound = not exchangeUrl.endswith('.html')
                if shopFound:
                    cardSource = exchangeUrl
                    self.logger.warning('Found new shop: %s', exchangeUrl)
                else:
                    cardSource = self.getTitle() + '/' + nickname

                userCards = userEntry.cssselect('table.CardInfo')
                if len(userCards) > 0:
                    self.estimatedCardsCount += len(userCards) - 1

                for cardInfo in userCards:
                    cardName = cardInfo.cssselect('th.txt0')[0].text
                    cardUrl = exchangeUrl
                    if not shopFound:
                        cardUrl += '?Title={}'.format(cardName)

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
                        language = languageSource[0].text

                    setSource = cardInfo.cssselect('#table0 td img')[0].attrib['alt']

                    yield {
                        'id': cardId,
                        'name': cardName,
                        'foilness': foilness,
                        'set': setSource,
                        'language': language,
                        'price': price,
                        'currency': core.utils.Currency.RUR,
                        'count': int(cardInfo.cssselect('td.txt15 b')[0].text.split()[0]),
                        'source': self.packSource(cardSource, cardUrl),
                    }


class TopTrade(CardSource):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'https://topdeck.ru', '/apps/toptrade/singles/search?q={query}')
        self.excludedSellers = [
            'angrybottlegnome',
            'bigmagic',
            'mtgsale',
            'mymagic.ru',
            'myupkeep',
        ]
        self.searchResults = None

    def query(self, queryText):
        self.searchResults = None
        yield from super().query(queryText)

    def _extractResults(self, html):
        if self.searchResults is None:
            result = []
            for script in html.cssselect('script'):
                match = re.search(r'var singles = JSON.parse\((.+)\);', script.text_content())
                if match:
                    jsonString = match.group(1).strip("'")
                    jsonString = re.sub(r'\\x([a-zA-Z0-9]{2})', lambda m: chr(int('0x{}'.format(m.group(1)), 16)), jsonString)
                    for card in json.loads(jsonString):
                        if card['source'] not in self.excludedSellers:
                            result.append(card)
            self.searchResults = result
        return self.searchResults

    def _getTotalCardsCount(self, html):
        return len(self._extractResults(html))

    def _getPageCardsCount(self, html):
        return self._getTotalCardsCount(html)

    def _parseResponse(self, queryText, url, html):
        for entry in self._extractResults(html):
            rawDataString = re.sub(r'</?[^>]+>', '', entry['line'].strip())
            dataString = rawDataString.lower()
            for key in ['name', 'eng_name', 'rus_name']:
                dataString = dataString.replace(entry.get(key, '').lower(), '')

            reserveString, dataString = self.extractToken(r'(?P<token>((за)?резерв(ирован(н)?(о|а|ы)?)?)|(reserv(e(d)?)?)|(отложен(н)?(о|а|ы)?))', dataString)
            if reserveString is not None:
                yield None
                continue

            cardSet = None
            cardLanguage = None
            cardCondition = None

            foilString, dataString = self.extractToken(r'(?P<token>foil|фо(и|й)л(а|(ов(ый|ая)?)?)?)', dataString)
            cardFoil = foilString is not None

            prPromoString, dataString = self.extractToken(r'(?P<token>((pre)?release)|((пре)?рел(из)?)|(прер))', dataString)
            if prPromoString is not None:
                cardSet = 'Prerelease & Release Cards'

            foundLangsNum = 0
            langCluster = None
            for cluster in StringUtils.letter_clusters(dataString):
                langAbbrv = self.langOracle.get_abbreviation(cluster, quiet=True)
                if langAbbrv is not None:
                    langCluster = cluster
                    cardLanguage = langAbbrv
                    foundLangsNum += 1
            if foundLangsNum == 1:
                dataString = dataString.replace(langCluster, '')
            else:
                cardLanguage = None

            foundConditions = set()
            for cluster in StringUtils.letter_clusters(dataString):
                cnd = self.conditionOracle.get_abbreviation(cluster.lower(), quiet=True)
                if cnd is not None:
                    foundConditions.add(cnd)
            if len(foundConditions) > 0:
                cardCondition = sorted(foundConditions, key=ConditionOracle.get_order().index)[0]

            seller = entry['source']
            if seller != 'topdeck':
                self.logger.warning('Found new shop: %s', seller)
            else:
                seller = entry['seller']['name']

            yield {
                'name': self.packName(entry['name'], rawDataString),
                'foilness': cardFoil,
                'set': cardSet,
                'language': cardLanguage,
                'price': decimal.Decimal(entry['cost']),
                'currency': core.utils.Currency.RUR,
                'count': entry['qty'],
                'condition': cardCondition,
                'source': self.packSource('topdeck.ru/' + seller, entry['url']),
            }


class MtgTradeShop(CardSource):
    def __init__(self, logger: ILogger, shopUrl: str, sourceSubstringsToExclude: List[str]):
        super().__init__(logger, shopUrl, '/search/?query={query}')
        self.cardSelector = 'table.search-card tbody tr'
        self.sourceSubstringsToExclude = set(sourceSubstringsToExclude + [
            'ambersonmtg',
        ])

    def getHtml(self, url):
        result = lxml.html.document_fromstring('<html/>')
        try:
            result = super().getHtml(url)
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
                yield len(resultsEntry.cssselect(self.cardSelector))
                continue

            for cardsGroup in resultsEntry.cssselect('table.search-card'):
                sellerBlock = cardsGroup.cssselect('td.user-name-td')[0]

                sellerNickname = None
                sellerNameBlocks = sellerBlock.cssselect('div.trader-name')
                if len(sellerNameBlocks) > 0:
                    sellerNickname = sellerNameBlocks[0].text.strip()
                if not sellerNickname:
                    sellerNickname = sellerBlock.cssselect('a')[0].text

                cardEntries = cardsGroup.cssselect('tbody tr')
                if any(source in sellerNickname.lower() for source in self.sourceSubstringsToExclude):
                    yield len(cardEntries)
                    continue

                sourceCaption = self.getTitle()
                if sourceCaption != sellerNickname:
                    sourceCaption = '{}/{}'.format(sourceCaption, sellerNickname)

                for cardEntry in cardEntries:
                    condition = None
                    conditionBlocks = cardEntry.cssselect('.js-card-quality-tooltip')
                    if len(conditionBlocks) > 0:
                        condition = conditionBlocks[0].text

                    language = None
                    languageBlocks = cardEntry.cssselect('.lang-item-info')
                    if len(languageBlocks) > 0:
                        language = languageBlocks[0].attrib['title']

                    cardSet = cardEntry.cssselect('.choose-set')[0].attrib['title']
                    if 'mtgo' in cardSet.lower():
                        yield None
                        continue

                    yield {
                        'name': ' '.join(anchor.text_content().split()),
                        'foilness': len(cardEntry.cssselect('img.foil')) > 0,
                        'set': cardSet,
                        'language': language,
                        'price': decimal.Decimal(''.join(cardEntry.cssselect('.catalog-rate-price b')[0].text.split()).strip('" ')),
                        'currency': core.utils.Currency.RUR,
                        'count': int(cardEntry.cssselect('td .sale-count')[0].text.strip()),
                        'condition': condition,
                        'source': self.packSource(sourceCaption, anchor.attrib['href']),  # TODO specify url to specific player + card
                    }


class MtgTrade(MtgTradeShop):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://mtgtrade.net', ['bigmagic', 'upkeep', 'mtgshop', 'magiccardmarket'])


class BigMagic(MtgTradeShop):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://bigmagic.ru', [])


class MyUpKeep(MtgTradeShop):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://myupkeep.ru', [])


class MtgShopRu(MtgTradeShop):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://mtgshop.ru', [])


class AutumnsMagic(CardSource):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://autumnsmagic.com', '/catalog?search={query}&page={page}')

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
                yield None
                continue

            nameTags = entry.cssselect('.card-name')
            if len(nameTags) == 0:
                yield None
                continue
            cardName = nameTags[0].cssselect('a')[0].text.strip()
            if self._isCardUnrelated(cardName, queryText):
                yield None
                continue

            dscBlock = entry.cssselect('.product-description')[0]
            dscImages = dscBlock.cssselect('img')

            language = None
            lngTitles = [img.attrib['title'] for img in dscImages if 'flags' in img.attrib['src']]
            if len(lngTitles) > 0:
                language = lngTitles[0]
            if not language:
                language = LangUtils.guess_language(cardName)

            foilString, cardName = self.extractToken(r'(?P<token>\s?\(фойловая\))', cardName)
            foil = foilString is not None

            countTag = [tag for tag in dscBlock.cssselect('span') if 'шт' in tag.text][0]
            priceTag = entry.cssselect('.product-footer .product-price .product-default-price')[0]

            yield {
                'name': cardName,
                'set': dscBlock.cssselect('i')[0].attrib['class'].split()[1][len('ss-'):],
                'language': language,
                'foilness': foil or len([img for img in dscImages if 'foil' in img.attrib['src']]) > 0,
                'count': int(re.match(r'^([\d]+).*', countTag.text.replace(' ', '')).group(1)),
                'price': decimal.Decimal(re.match(r'.*?([\d ]+).*', priceTag.text.strip()).group(1).replace(' ', '')),
                'currency': core.utils.Currency.RUR,
                'source': cardUrl,
            }


class BuyMagic(CardSource):
    __PRODUCT_SELECTOR = 'input[value="Купить"]'

    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://www.buymagic.com.ua', '/edition/?color=-1&type=-1&rare=-1&id=-1&name={query}&page={page}&submit=%s' % urllib.parse.quote('Искать'))

    def _getPageCount(self, html):
        result = 1
        anchors = html.cssselect('div.c2 div table div a')
        if len(anchors) > 0:
            result = int(anchors[-1].text)
        return result

    def _getPageCardsCount(self, html):
        return len(html.cssselect(self.__PRODUCT_SELECTOR))

    def _parseDoubleName(self, nameString: str) -> Tuple[str, Optional[str], Optional[str]]:
        n1, n2 = re.match(r'^([^(]+)?(?:\((.+)\))?', nameString).groups()
        name = n1
        lang = None
        comment = None
        if n2 is not None:
            lang = self.langOracle.get_abbreviation('RU' if 'рус' in n2.lower() else n2, quiet=True)
            if lang is None:
                if LangUtils.guess_language(n2) != 'EN':
                    comment = n2
                else:
                    name = n2
        return name.strip(), lang, comment

    def _parseResponse(self, queryText, url, html):
        blocks = {}
        for image in html.cssselect('a.single_image'):
            block = list(image.iterancestors())[0]
            blocks[id(block)] = block
        for block in blocks.values():
            numProducts = len(block.cssselect(self.__PRODUCT_SELECTOR))
            if 'Тип карты' not in block.text_content():
                yield numProducts
                continue
            anchor = block.cssselect('a.link_card_name')[0]
            cardName, blockSet = [s for s in anchor.text_content().split('\t') if s.strip()]
            if any(s in cardName.lower() for s in ['token', 'emblem']):
                yield numProducts
                continue
            cardName, langFromName, comment = self._parseDoubleName(cardName)
            setIsRus, blockSet = self.extractToken(r'(?P<token>\sРУС)', blockSet)
            blockSet = re.match(r'^\[(.+?)]$', blockSet).group(1)
            for entry in block.cssselect('table tr'):
                text = entry.text_content()
                cardSet = blockSet
                langFromSet = self.langOracle.get_abbreviation(cardSet, quiet=True)
                if langFromSet is not None:
                    cardSet = None
                language = langFromName
                if language is None:
                    language = self.langOracle.get_abbreviation(re.search(r'Язык: (\w+)', text).group(1))
                    if language == 'RU' and setIsRus is None:
                        language = 'EN'
                    elif langFromSet is not None:
                        language = langFromSet
                yield {
                    'name': self.packName(cardName, comment),
                    'foilness': re.search(r'Тип: FOIL', text) is not None,
                    'set': cardSet,
                    'language': language,
                    'price': decimal.Decimal(re.search(r'([\d.]+) грн\.', text).group(1)),
                    'currency': core.utils.Currency.UAH,
                    'count': int(entry.cssselect('select[name="card_count"] option')[-1].text),
                    'source': anchor.attrib['href'],
                }


class OfflineTestSource(CardSource):
    def __init__(self, logger: ILogger):
        super().__init__(logger, 'http://offline.shop', '?query={query}')
        self.setAbbreviations = list(load_json_resource('set_names.json').keys())

    def query(self, queryText):
        self.estimatedCardsCount = random.randint(1, 10)
        for _ in range(self.estimatedCardsCount):
            if bool(random.randint(0, 1)):
                time.sleep(random.randint(0, 1))
            # noinspection PyProtectedMember
            yield {
                'id': random.randint(1, 300),
                'name': random.choice(string.ascii_letters) * random.randint(10, 25),
                'foilness': bool(random.randint(0, 1)),
                'set': random.choice(self.setAbbreviations),
                'language': random.choice(['RU', 'EN', 'FR', 'DE', 'ES']),
                'price': decimal.Decimal(random.randint(10, 1000)) if bool(random.randint(0, 1)) else None,
                'currency': random.choice([core.utils.Currency.RUR, core.utils.Currency.USD, core.utils.Currency.EUR]),
                'count': random.randint(1, 10),
                'condition': random.choice(['HP', 'NM', 'SP', 'MP']),
                'source': '',
            }


def getCardSourceClasses():
    classes = [
        AngryBottleGnome,
        AutumnsMagic,
        BigMagic,
        BuyMagic,
        CardPlace,
        ManaPoint,
        MtgRu,
        MtgSale,
        MtgTrade,
        MyUpKeep,
        MtgShopRu,
        TopTrade,
    ]
    random.shuffle(classes)
    return classes
