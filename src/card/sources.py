# coding: utf-8

import decimal
import http.client
import lxml.html
import os
import random
import re
import string
import time
import urllib
import urllib.error
import urllib.parse

import card.sets
import core.currency
import core.language
import core.network
import tools.dict
import tools.string

_CONDITIONS_SOURCE = {
    'HP': ('Heavily Played', 'Hardly Played', 'ХП',),
    'MP': ('Moderately Played', 'Played', 'МП',),
    'SP': ('Slightly Played', 'СП',),
    'NM': ('Near Mint', 'M/NM', 'M', 'Mint', 'Excellent', 'great', 'НМ',),  # TODO great :(
}
_CONDITIONS_ORDER = ('HP', 'MP', 'SP', 'NM')
_CONDITIONS = tools.dict.expandMapping(_CONDITIONS_SOURCE)
_CONDITIONS_CASE_INSENSITIVE = {}
for k, v in _CONDITIONS.items():
    _CONDITIONS_CASE_INSENSITIVE[k.lower()] = v

MTG_RU_SPECIFIC_SETS = {
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
}


def getConditionHumanReadableString(conditionString):
    key = conditionString.lower()
    if key in _CONDITIONS_CASE_INSENSITIVE:
        return _CONDITIONS_SOURCE[_CONDITIONS_CASE_INSENSITIVE[key]][0]


def guessCardLanguage(cardName):
    language = None
    nameLetters = re.sub(r'\W', '', cardName.lower())
    for abbrv, letters in core.language.LANGUAGES_TO_LOWERCASE_LETTERS.items():
        if all(c in letters for c in nameLetters):
            language = abbrv
            break
    return language


class CardSource(object):
    def __init__(self, url, cardQueryUrlTemplate, encoding, sourceSpecificSets):
        self.url = url
        self.cardQueryUrlTemplate = url + cardQueryUrlTemplate
        self.sourceSpecificSets = sourceSpecificSets
        self.encoding = encoding
        self.foundCardsCount = 0
        self.estimatedCardsCount = None
        self.requestCache = {}

    def getTitle(self):
        location = urllib.parse.urlparse(self.url).netloc
        return re.sub(r'^www\.', '', location)

    def getSetAbbrv(self, setId):
        return card.sets.tryGetAbbreviation(self.sourceSpecificSets.get(setId, setId))

    def _escapeQueryText(self, queryText):
        return queryText.replace(u'`', "'").replace(u'’', "'")

    def makeUrl(self, queryText, pageIndex):
        return self.cardQueryUrlTemplate.format(urllib.parse.quote(self._escapeQueryText(queryText)), pageIndex)

    def makeRequest(self, url):
        if url not in self.requestCache:
            self.requestCache[url] = lxml.html.document_fromstring(core.network.getUrl(url).decode(self.encoding))
        return self.requestCache[url]

    def packName(self, caption, description=None):
        result = {'caption': card.utils.escape(card.utils.clean(caption.strip())), 'description': description}
        return result

    def packSource(self, caption, cardUrl=None):
        if cardUrl is not None:
            cardUrl = urllib.parse.urljoin(self.url, cardUrl)
        result = {'caption': caption, 'url': cardUrl or caption}
        return result

    def fillCardInfo(self, cardInfo):
        if not cardInfo.get('language') and cardInfo.get('set'):
            cardInfo['language'] = core.language.getAbbreviation(card.sets.SINGLE_LANGUAGE_SETS.get(cardInfo['set'], ''))
        self.foundCardsCount += 1
        return cardInfo

    def getFoundCardsCount(self):
        return self.foundCardsCount

    def getEstimatedCardsCount(self):
        return self.estimatedCardsCount

    def query(self, queryText):
        html = self.makeRequest(self.makeUrl(queryText, self._makePageIndex(0)))
        pagesCount = max(1, self._estimatePagesCount(html))
        self.estimatedCardsCount = self._getFoundCardsCount(html)
        if self.estimatedCardsCount <= 0:
            self.estimatedCardsCount = self._getCardsPerPageCount(html) * pagesCount
        for i in range(pagesCount):
            resultsUrl = self.makeUrl(queryText, self._makePageIndex(i))
            pageCards = 0
            for cardInfo in self.parse(self.makeRequest(resultsUrl), resultsUrl):
                if cardInfo is not None:
                    pageCards += 1
                yield cardInfo
            if pageCards == 0:
                self.estimatedCardsCount = self.foundCardsCount
                yield None
                break

    def _makePageIndex(self, i):
        return i + 1

    def _refineEstimatedCardsCount(self, html, entriesCount):
        pageCards = self._getCardsPerPageCount(html)
        if entriesCount < pageCards:
            self.estimatedCardsCount -= pageCards - entriesCount
            if self.estimatedCardsCount < 0:
                self.estimatedCardsCount = 0
            return True
        return False

    def _getFoundCardsCount(self, html):
        return 0


class AngryBottleGnome(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'Promo - Special': 'Media Inserts',
            'Prerelease Events': 'Prerelease & Release Cards',
            'Release Events': 'Prerelease & Release Cards',
            'Launch Party': 'Magic: The Gathering Launch Parties',
        }
        super().__init__('http://angrybottlegnome.ru', '/shop/search/{}/filter/instock', 'utf-8', sourceSpecificSets)
        # <div class = "abg-float-left abg-card-margin abg-card-version-instock">Английский, M/NM  (30р., в наличии: 1)</div>
        # <div class = "abg-float-left abg-card-margin abg-card-version-instock">Итальянский, M/NM  Фойл (180р., в наличии: 1)</div>
        self.cardInfoRegexp = re.compile(r'(?P<language>[^,]+),\s*(?P<condition>[\S]+)\s*(?P<foilness>[^\(]+)?\s*\((?P<price>\d+)[^\d]*(?P<count>\d+)\)')

    def _estimatePagesCount(self, html):
        return 1

    def _getCardsPerPageCount(self, html):
        return len(html.cssselect('#search-results tbody tr'))

    def parse(self, html, url):
        '''
        <div id="search-results"><table class="tablesorter sticky-enabled" id="search-list">
         <thead><tr><th>Название</th><th>Сет</th><th>В наличии</th><th>Цена</th> </tr></thead>
        <tbody>
         <tr class="odd"><td><a href="/shop/card/14443" class = "tooltipCard" name = "Sowing+Salt">Sowing Salt</a></td><td><a href="/shop/set/29">Betrayers of Kamigawa</a></td><td>1</td><td>от 150р.</td> </tr>
         <tr class="even"><td><a href="/shop/card/17977" class = "tooltipCard" name = "Sowing+Salt">Sowing Salt</a></td><td><a href="/shop/set/45">Urza's Destiny</a></td><td>8</td><td>от 150р.</td> </tr>
        </tbody>
        </table>
        </div>
        '''
        searchResults = html.cssselect('#search-results tbody tr')
        for resultsEntry in searchResults:
            dataCells = resultsEntry.cssselect('td')
            cardName = dataCells[0].cssselect('a')[0].text
            cardSet = dataCells[1].cssselect('a')[0].text
            cardRelativeUrl = dataCells[0].cssselect('a')[0].attrib['href']
            cardUrl = urllib.parse.urljoin(self.url, cardRelativeUrl)
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
                    'condition': _CONDITIONS[rawInfo['condition']],
                    'foilness': bool(rawInfo['foilness']),
                    'count': int(rawInfo['count']),
                    'price': decimal.Decimal(rawInfo['price']),
                    'currency': core.currency.RUR,
                    'source': self.packSource(self.getTitle(), cardUrl),
                })


class MtgRuShop(CardSource):
    def __init__(self, url):
        super().__init__(url, '/catalog.phtml?Title={}&page={}', 'cp1251', MTG_RU_SPECIFIC_SETS)

    def _estimatePagesCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('.split-pages a')
        if len(pagesLinks) > 0:
            pagesCount = int(re.match(r'.+page=(\d+).*', pagesLinks[-1].attrib['href']).group(1))
        return pagesCount

    def _getCardsPerPageCount(self, html):
        return 25

    def parse(self, html, url):
        '''
        <table id="Catalog">
        <tr class="ui-state-highlight ui-widget" id="2941159-eng-Y">
            <td width="25" align="center" class="Grp"><img src="http://www.mtg.ru/images2/sets/KTK.gif" alt="KTK" title="Khans of Tarkir // Ханы Таркира" style="vertical-align: middle;"></td>
            <td width="25" align="center"><img src="http://www.mtg.ru/images2/icons/en.gif"></td>
            <td width="*"><span class="A CardName" onClick=ShowPic("KTK/AbominationofGudul")>Abomination of Gudul</span><br><span class="SL Zebra">Гудульская Мерзость</span> </td>
            <td width="50" align="center">фойл</td>
            <td width="50" align="center"><img src="http://www.mtg.ru/images2/mana/M.gif" width="17" height="17" alt="Multi-color"></td>
            <td width="50" align="right">1&nbsp;шт.</td>
            <td width="90" align="right">15&nbsp;руб.</td>
            <td width="60" align="center"><button class="BT_to_cart" onClick="Cart('add', '2941159-eng-Y');"></button></td>
        </tr>
        '''
        products = html.cssselect('#Catalog tr')
        if self._refineEstimatedCardsCount(html, len(products)):
            yield None

        for resultsEntry in products:
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
        super().__init__('http://amberson.mtg.ru')


class ManaPoint(MtgRuShop):
    def __init__(self):
        super().__init__('http://manapoint.mtg.ru')


class MagicMaze(MtgRuShop):
    def __init__(self):
        super().__init__('http://magicmaze.mtg.ru')


# class MtgRuPromoShop(CardSource):
#     def __init__(self, siteUrl, promoUrl):
#         super().__init__(siteUrl, promoUrl, 'cp1251', {})
#         self.fullPromoUrl = urllib.parse.urljoin(siteUrl, promoUrl)


# class AmbersonPromo(MtgRuPromoShop):
#     def __init__(self):
#         super().__init__('http://amberson.mtg.ru', '/3.html')
#         self.patterns = [
#             (re.compile(r'Oversized - (?P<name>.+)(, foil)?'), 'Oversized Cards'),
#         ]

#     def query(self, queryText):
#         foundCardsCount = 0
#         self.estimatedCardsCount = 10
#         searchResults = self.makeRequest(queryText)
#         for resultsEntry in searchResults.cssselect('table.Catalog tr'):
#             cells = resultsEntry.cssselect('td')
#             nameString = cells[0].text
#             foundNameKey = card.utils.getNameKey(nameString)
#             queryNameKey = card.utils.getNameKey(queryText)
#             if queryNameKey in foundNameKey:
#                 cardName = nameString
#                 cardSetId = None
#                 foilness = False
#                 for (pattern, patternSetId) in self.patterns:
#                     match = pattern.match(nameString)
#                     if match:
#                         groups = match.groupdict()
#                         print(groups)
#                         cardName = groups['name']
#                         cardSetId = self.getSetAbbrv(patternSetId)
#                         foilness = 'foil' in groups
#                         break
#                 result = {
#                     'name': self.packName(cardName, nameString),
#                     'set': cardSetId,
#                     # 'language': language, TODO
#                     'foilness': foilness,
#                     'count': int(re.match(r'(\d+)', cells[1].text).group(1)),
#                     'price': decimal.Decimal(re.match(r'(\d+)', cells[2].text.replace('`', '')).group(1)),
#                     'currency': core.currency.RUR,
#                     'source': self.packSource(self.getTitle(), self.fullPromoUrl)
#                 }
#                 yield self.fillCardInfo(result)


class MtgSale(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'MI': 'Mirrodin',
            'MR': 'Mirage',
            'TP': 'Tempest',
        }
        super().__init__('http://mtgsale.ru', '/home/search-results?Name={}&Page={}', 'utf-8', sourceSpecificSets)

    def _estimatePagesCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('ul.tabsb li a')
        if len(pagesLinks) > 0:
            pagesCount = int(pagesLinks[-1].text)
        return pagesCount

    def _getFoundCardsCount(self, html):
        return int(re.match(r'\D*(\d+)\D*', html.cssselect('span.search-number')[0].text).group(1))

    def _getCardsPerPageCount(self, html):
        return 25

    def parse(self, html, url):
        for resultsEntry in html.cssselect('.tab_container div.ctclass'):
            count = int(re.match(r'(\d+)', resultsEntry.cssselect('p.colvo')[0].text).group(0))
            if count <= 0:
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

            nameSelector = 'p.tname .tnamec'
            language = core.language.getAbbreviation(resultsEntry.cssselect('p.lang i')[0].attrib['title'])
            if language != 'EN':
                nameSelector = 'p.tname .smallfont'

            yield self.fillCardInfo({
                'name': self.packName(resultsEntry.cssselect(nameSelector)[0].text),
                'set': self.getSetAbbrv(resultsEntry.cssselect('p.nabor span')[0].attrib['title']),
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
        super().__init__('http://cardplace.ru', '/directory/new_search/{}/singlemtg', 'utf-8', sourceSpecificSets)

    def _extractFirstLevelParenthesesContents(self, string):
        # Лес (#246) (Forest (#246))
        contents = []
        current = []
        level = 0
        for c in string:
            if c == '(':
                level += 1
            elif c == ')':
                level -= 1
            if level > 0 and (level != 1 or c != '('):
                current.append(c)
            elif level == 0 and c == ')':
                contents.append(''.join(current))
                current = []
        return contents

    def _estimatePagesCount(self, html):
        return 1

    def _getCardsPerPageCount(self, html):
        return len(html.cssselect('#mtgksingles tbody tr'))

    def parse(self, html, url):
        for resultsEntry in html.cssselect('#mtgksingles tbody tr'):
            dataCells = resultsEntry.cssselect('td')
            language = core.language.getAbbreviation(os.path.basename(urllib.parse.urlparse(self.url + dataCells[3].cssselect('img')[0].attrib['src']).path))
            cardId = None
            cardNameAnchor = dataCells[2].cssselect('a')[0]
            cardName = cardNameAnchor.text
            isSpecialPromo = any(string in cardName for string in ['APAC', 'EURO', 'MPS'])
            if not isSpecialPromo:
                if not language or language != 'EN':
                    prn = self._extractFirstLevelParenthesesContents(cardName)
                    if prn and not prn[-1].strip('#').isdigit():
                        cardName = prn[-1]
                prn = self._extractFirstLevelParenthesesContents(cardName)
                if prn:
                    cardIdCandidate = prn[0].lstrip('#')
                    if cardIdCandidate.isdigit():
                        cardName = cardName[:cardName.index('(')].strip()
                        cardId = cardIdCandidate
            nameImages = dataCells[2].cssselect('img')
            yield self.fillCardInfo({
                'id': int(cardId) if cardId else None,
                'name': self.packName(cardName),
                'foilness': len(nameImages) > 0 and nameImages[0].attrib['title'] == 'FOIL',
                'set': self.getSetAbbrv(dataCells[1].cssselect('b')[0].text.strip("'")),
                'language': language,
                'price': decimal.Decimal(re.match(r'([\d\.]+)', dataCells[6].text.strip()).group(0)),
                'currency': core.currency.RUR,
                'count': int(re.match(r'(\d+)', dataCells[7].text.strip()).group(0)),
                'source': self.packSource(self.getTitle(), cardNameAnchor.attrib['href']),
            })


class MtgRu(CardSource):
    def __init__(self):
        self.sourceSubstringsToExclude = [
            'amberson.mtg.ru',
            'cardplace.ru',
            'centerofhobby.ru',
            'magicmaze.mtg.ru',
            'manapoint.mtg.ru',
            'mckru.mtg.ru',
            'mtgsale.ru',
            'mtgtrade.net',
        ]
        self.knownShopSourceSubstrings = [
            'shop.mymagic.ru',
        ]
        super().__init__('http://mtg.ru', '/exchange/card.phtml?Title={}&Amount=1', 'cp1251', MTG_RU_SPECIFIC_SETS)

    def _estimatePagesCount(self, html):
        return 1

    def _getCardsPerPageCount(self, html):
        return len(html.cssselect('table.NoteDivWidth'))

    def parse(self, html, url):
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


class Untap(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'New Phyrxia': 'New Phyrexia',
        }
        super().__init__('http://untap.ru', '/search?search_query={}&p={}&n=60', 'utf-8', sourceSpecificSets)

    def _estimatePagesCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('ul.pagination li a')
        if len(pagesLinks) > 0:
            pagesCount = int(pagesLinks[-2].cssselect('span')[0].text)
        return pagesCount

    def _getCardsPerPageCount(self, html):
        return 12

    def parse(self, html, url):
        products = html.cssselect('.product-container .right-block')
        if self._refineEstimatedCardsCount(html, len(products)):
            yield None

        for entry in products:
            if len(entry.cssselect('.out-of-stock')) > 0:
                self.estimatedCardsCount -= 1
                yield None
                continue

            nameSource = entry.cssselect('.product-name')[0].text.strip()
            detailsParts = nameSource.strip().split('\t')

            foilness = None
            language = None
            if len(detailsParts) > 1:
                foilness = 'foil' in detailsParts[1].lower()
                language = core.language.getAbbreviation(detailsParts[1].split()[0])

            priceSource = entry.cssselect('.content_price')
            price = None
            priceCurrency = None
            if len(priceSource) > 0:
                priceString = priceSource[0].cssselect('span.price')[0].text
                priceString = priceString.replace(' ', '').replace('\t', '')
                price = decimal.Decimal(re.match(r'[^\d]*(\d+)[^\d]*', priceString).group(1))
                priceCurrency = priceSource[0].cssselect('meta')[0].attrib['content']

            detailsUrl = entry.cssselect('a.product-name')[0].attrib['href']
            detailsHtml = lxml.html.document_fromstring(core.network.getUrl(detailsUrl))
            descriptionBlock = detailsHtml.cssselect('#short_description_content')[0]
            description = descriptionBlock.text
            if description is None:
                paragraph = descriptionBlock.cssselect('p')
                if len(paragraph) > 0:
                    description = paragraph[0].text

            setId = None
            condition = None
            if description:
                match = re.match(r'.+from\s*(?P<set>.+)set\s*in\s*(?P<condition>.+)condition', description)
                if match:
                    groups = match.groupdict()
                    setId = self.getSetAbbrv(groups['set'].strip())
                    condition = groups['condition'].strip()
                else:
                    print(description)

            count = int(detailsHtml.cssselect('#quantityAvailable')[0].text)

            yield self.fillCardInfo({
                'name': self.packName(detailsParts[0]),
                'condition': _CONDITIONS[condition],
                'foilness': foilness,
                'set': setId,
                'language': language,
                'price': price,
                'currency': priceCurrency,
                'count': count,
                'source': self.packSource(self.getTitle(), detailsUrl),
            })


class CenterOfHobby(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'LE': 'Legions',
            'MI': 'Mirrodin',
        }
        super().__init__('http://www.centerofhobby.ru', '/catalog/mtgcards/search/?card_name={}&curPos={}', 'utf-8', sourceSpecificSets)

    def _estimatePagesCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('.nc_pagination')[-1].cssselect('a')
        if len(pagesLinks) > 0 and pagesLinks[-1].text.isdigit():
            pagesCount = int(pagesLinks[-1].text)
        return pagesCount

    def _getCardsPerPageCount(self, html):
        return 100

    def _makePageIndex(self, i):
        return i * self._getCardsPerPageCount('')

    def parse(self, html, url):
        products = html.cssselect('.mtg_table tr')[1:]
        if self._refineEstimatedCardsCount(html, len(products)):
            yield None

        prevResult = None
        for entry in products:
            cells = entry.cssselect('td')

            foil = False
            isChildEntry = len(entry.cssselect('.child_card')) > 0
            if isChildEntry:
                cardId = prevResult['id']
                cardName = cells[2].cssselect('div')[0].text
                foil = cardName.endswith('(foil)')
                cardName = cardName.replace('(foil)', '')
                cardSet = prevResult['set']
                cardUrl = prevResult['url']
            else:
                cardId = cells[0].text
                cardName = cells[2].cssselect('a')[0].cssselect('b')[0].text
                cardSet = re.match(r'r_([^_]+)_.+', os.path.basename(cells[1].cssselect('img')[0].attrib['src'])).group(1)
                cardUrl = cells[2].cssselect('a')[0].attrib['href']

            cardLanguage = re.match(r'^lang_(.+)$', cells[2].attrib['class']).group(1)
            cardCount = int(cells[5].text) if cells[5].text.isdigit() else 0
            cardPrice = None
            if cardCount > 0:
                priceMatch = re.match(r'([\d\s]+).*', cells[6].text)
                if priceMatch:
                    cardPrice = decimal.Decimal(''.join(priceMatch.group(1).split()))

            # Эвристика для обхода бага на сайте.
            if cardLanguage == '$card_lang':
                cardLanguage = guessCardLanguage(cardName)
            if cardLanguage is not None:
                cardLanguage = core.language.getAbbreviation(cardLanguage)

            result = {
                'id': int(cardId),
                'name': self.packName(cardName),
                'foilness': foil,
                'set': self.getSetAbbrv(cardSet.upper()),
                'language': cardLanguage,
                'price': cardPrice,
                'currency': core.currency.RUR,
                'count': cardCount,
                'source': self.packSource(self.getTitle(), cardUrl),
                'url': cardUrl,
            }
            prevResult = result.copy()
            if cardCount > 0:
                yield self.fillCardInfo(result)
            else:
                self.estimatedCardsCount -= 1
                yield None


class TtTopdeck(CardSource):
    def __init__(self):
        super().__init__('http://tt.topdeck.ru', '/?req={}&mode=sell&group=card', 'utf-8', {})
        self.excludedSellers = [
            'angrybottlegnome',
            'mtgsale',
        ]
        self.possiblePriceRegexps = [
            [re.compile(r'.*?(\d+)\s*\$.*'), core.currency.USD, 1],
            [re.compile(r'.*?(\d+)\s*[kк][^t]', re.U | re.I), core.currency.RUR, 1000],
        ]

    def _estimatePagesCount(self, html):
        return 1

    def _getCardsPerPageCount(self, html):
        return len(html.cssselect('table table tr')[1:])

    def parse(self, html, url):
        for entry in html.cssselect('table table tr')[1:]:
            cells = entry.cssselect('td')
            cardName = cells[3].text
            sellerAnchor = cells[5].cssselect('a')[0]
            sellerNickname = sellerAnchor.text
            if cardName and sellerNickname not in self.excludedSellers:

                priceValue = None
                priceCurrency = None
                priceString = cells[1].text
                if priceString.isdigit():
                    priceValue = decimal.Decimal(priceString)
                    priceCurrency = core.currency.RUR

                countValue = None
                countString = cells[2].text
                if countString.isdigit():
                    countValue = int(countString)

                foil = False
                cardSet = None
                cardLanguage = None
                cardCondition = None

                detailsString = cells[6].text
                if detailsString:
                    descriptionString = ' '.join(detailsString.split()).strip()
                    if descriptionString.isdigit():
                        descriptionString = None

                    detailsStringLw = detailsString.lower()

                    for regexp, currency, valueMultiplier in self.possiblePriceRegexps:
                        # я не смог написать нормальную регулярку, чтобы ловила 15k, но не ловила 15 ktk, поэтому так
                        whitespaced = detailsStringLw + ' '
                        match = regexp.match(whitespaced)
                        if match:
                            priceValue = decimal.Decimal(match.group(1)) * valueMultiplier
                            priceCurrency = currency
                            break

                    foil = any(foilString in detailsStringLw for foilString in ['foil', 'фойл', 'фоил'])

                    letterClusters = tools.string.splitByNonLetters(detailsStringLw)

                    for cluster in letterClusters:
                        cardSet = card.sets.tryGetAbbreviation(cluster, quiet=True)
                        if cardSet is not None:
                            break

                    foundLangsCount = 0
                    for cluster in letterClusters:
                        langAbbrv = core.language.tryGetAbbreviation(cluster)
                        if langAbbrv is not None:
                            cardLanguage = langAbbrv
                            foundLangsCount += 1
                    if foundLangsCount > 1:
                        cardLanguage = None

                    foundConditions = set()
                    for cluster in letterClusters:
                        lc = cluster.lower()
                        if lc in _CONDITIONS_CASE_INSENSITIVE:
                            foundConditions.add(_CONDITIONS_CASE_INSENSITIVE[lc])
                    if len(foundConditions) > 0:
                        cardCondition = sorted(foundConditions, key=_CONDITIONS_ORDER.index)[0]

                    countMatch = re.match(r'(\d+)\W.*?{}'.format(cardName), detailsStringLw, re.U | re.I)
                    if countMatch:
                        countValue = int(countMatch.group(1))

                # Если цена и количество перепутаны местами
                if countValue > 50 and priceValue < 50:
                    countValue, priceValue = int(priceValue), decimal.Decimal(countValue)

                yield self.fillCardInfo({
                    'name': self.packName(cells[3].text, descriptionString),
                    'foilness': foil,
                    'set': cardSet,
                    'language': core.language.getAbbreviation(cardLanguage) if cardLanguage else None,
                    'price': priceValue,
                    'currency': priceCurrency,
                    'count': countValue,
                    'condition': cardCondition,
                    'source': self.packSource('topdeck.ru/' + sellerNickname.lower().replace(' ', '_'), sellerAnchor.attrib['href']),
                })
            else:
                self.estimatedCardsCount -= 1
                yield None


class EasyBoosters(CardSource):
    def __init__(self):
        super().__init__('http://easyboosters.com', '/products?keywords={}&page={}', 'utf-8', {})

    def _estimatePagesCount(self, html):
        pagesCount = 1
        pagesLinks = html.cssselect('.pagination li a')
        if len(pagesLinks) > 0:
            pagesCount = int(re.match(r'.+?page=(\d+).*', pagesLinks[-1].attrib['href']).group(1))
        return pagesCount

    def _getCardsPerPageCount(self, html):
        return 12

    def parse(self, html, url):
        products = html.cssselect('#products .product-list-item')

        if len(products) == 0:
            return

        if self._refineEstimatedCardsCount(html, len(products)):
            yield None

        for entry in products:
            cardUrl = entry.cssselect('a')[0].attrib['href']
            if not cardUrl:
                self.estimatedCardsCount -= 1
                yield None
                continue

            itemName = entry.cssselect('.product-name-wrapper a.info')[0].attrib['title']
            if any(substring in itemName.lower() for substring in ['фигурка', 'протекторы', 'кубик', 'альбом']):
                self.estimatedCardsCount -= 1
                yield None
                continue

            cardHtml = lxml.html.document_fromstring(core.network.getUrl(cardUrl))
            itemName = cardHtml.cssselect('#product-description .product-title')[0].text
            cardName = re.match(r'(.+?)\s*(#\d+)?\s\([^\,]+\,\s.+?\)', itemName).group(1)

            condition = None
            foil = False
            language = None
            cardSet = None
            cardId = None
            for row in cardHtml.cssselect('#product-properties tr'):
                caption = row.cssselect('td strong')[0].text
                value = row.cssselect('td')[1].text
                if caption in ('Покрытие', 'Finish'):
                    foil = value != 'Regular'
                elif caption in ('Состояние', 'Condition'):
                    if value in _CONDITIONS:
                        condition = _CONDITIONS[value]
                elif caption in ('Язык', 'Language'):
                    language = core.language.getAbbreviation(value)
                elif caption in ('Сет', 'Set'):
                    cardSet = card.sets.tryGetAbbreviation(value)
                elif caption in ('Номер', 'Number'):
                    cardId = int(value)

            priceBlock = cardHtml.cssselect('#product-price div')[0]
            priceString = priceBlock.cssselect('span.price')[0].text
            priceString = ''.join(priceString.replace('&nbsp;', '').split())
            price = decimal.Decimal(re.match(r'(\d+).*', priceString).group(1))
            currency = None
            currencySpan = priceBlock.cssselect('span')[-1]
            if currencySpan.attrib['itemprop'] == 'priceCurrency' and currencySpan.attrib['content'] == 'RUB':
                currency = core.currency.RUR

            count = 0
            countBlock = cardHtml.cssselect('#product-price div')[1]
            countSpan = countBlock.cssselect('span.lead')[0]
            if countSpan.attrib['itemprop'] == 'totalOnHand':
                count = int(countSpan.text)

            yield self.fillCardInfo({
                'id': cardId,
                'name': self.packName(cardName),
                'foilness': foil,
                'set': cardSet,
                'language': language,
                'price': price,
                'currency': currency,
                'count': count,
                'condition': condition,
                'source': self.packSource(self.getTitle(), cardUrl)
            })


class MtgTrade(CardSource):
    def __init__(self):
        super().__init__('http://mtgtrade.net', '/search/?query={}', 'utf-8', {})
        self.cardSelector = 'table.search-card tbody tr'

    def makeRequest(self, url):
        result = lxml.html.document_fromstring('<html/>')
        try:
            result = super().makeRequest(url)
        except urllib.error.HTTPError as ex:
            if ex.code != http.client.INTERNAL_SERVER_ERROR:
                raise
        return result

    def _estimatePagesCount(self, html):
        return 1

    def _getCardsPerPageCount(self, html):
        return len(html.cssselect(self.cardSelector))

    def parse(self, html, url):
        for resultsEntry in html.cssselect('.search-item'):
            sellerCardsGroups = resultsEntry.cssselect('table.search-card')
            anchor = resultsEntry.cssselect('.search-title')[0]
            if '/single/' not in anchor.attrib['href']:
                self.estimatedCardsCount -= len(resultsEntry.cssselect(self.cardSelector))
                continue

            for cardsGroup in sellerCardsGroups:
                sellerBlock = cardsGroup.cssselect('td.center')[0]
                sellerNickname = sellerBlock.cssselect('a')[0].text.lower()
                sellerUrl = list(sellerBlock.cssselect('a'))[-1].attrib['href']

                for cardEntry in cardsGroup.cssselect('tbody tr'):
                    condition = None
                    conditionBlocks = cardEntry.cssselect('.js-card-quality-tooltip')
                    if len(conditionBlocks) > 0:
                        condition = _CONDITIONS[cardEntry.cssselect('.js-card-quality-tooltip')[0].text]

                    yield self.fillCardInfo({
                        'name': self.packName(' '.join(anchor.text_content().split())),
                        'foilness': len(cardEntry.cssselect('img.foil')) > 0,
                        'set': self.getSetAbbrv(cardEntry.cssselect('.choose-set')[0].attrib['title']),
                        'language': core.language.getAbbreviation(''.join(cardEntry.cssselect('td .card-properties')[0].text.split()).strip('|')),
                        'price': decimal.Decimal(''.join(cardEntry.cssselect('.catalog-rate-price')[0].text.split()).strip('"')),
                        'currency': core.currency.RUR,
                        'count': int(cardEntry.cssselect('td .sale-count')[0].text.strip()),
                        'condition': condition,
                        'source': self.packSource(self.getTitle() + '/' + sellerNickname, sellerUrl)
                    })


class OfflineTestSource(CardSource):
    def __init__(self):
        super().__init__('http://offline.shop', '?query={}', 'utf-8', {})

    def query(self, queryText):
        self.estimatedCardsCount = random.randint(1, 10)
        for _ in range(self.estimatedCardsCount):
            if bool(random.randint(0, 1)):
                time.sleep(random.randint(0, 1))
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
        # AmbersonPromo,
        Amberson,
        AngryBottleGnome,
        CardPlace,
        CenterOfHobby,
        EasyBoosters,
        MagicMaze,
        ManaPoint,
        MtgRu,
        MtgSale,
        MtgTrade,
        TtTopdeck,
        Untap,
    ]
    random.shuffle(classes)
    return classes
