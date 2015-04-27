# coding: utf-8

import decimal
import lxml
import os
import re
import urllib
import urlparse

import card.sets
import core.currency
import core.language
import core.network
import tools.dict
import tools.string

_CONDITIONS_SOURCE = {
    'NM': ('M/NM', 'Mint', 'Near Mint', 'Excellent', u'НМ'),
    'SP': ('Slightly Played', u'СП'),
    'HP': ('Heavily Played', 'Hardly Played',),
    'MP': ('Played', 'Moderately Played', u'МП')
}
_CONDITIONS_ORDER = ('HP', 'MP', 'SP', 'NM')
_CONDITIONS = tools.dict.expandMapping(_CONDITIONS_SOURCE)
_CONDITIONS_CASE_INSENSITIVE = {}
for k, v in _CONDITIONS.iteritems():
    _CONDITIONS_CASE_INSENSITIVE[k.lower()] = v

MTG_RU_SPECIFIC_SETS = {
    'LE': 'Legions',
    'LG': 'Legends',
    'MI': 'Mirage',
    'MR': 'Mirrodin',
    'P1': 'Portal',
    'P2': 'Portal: Second Age',
    'P3': 'Portal: Three Kingdoms',
    'ST': 'Starter 1999',
}


def guessCardLanguage(cardName):
    language = None
    nameLetters = re.sub(r'\W', '', cardName.lower())
    for abbrv, letters in core.language.LANGUAGES_TO_LOWERCASE_LETTERS.iteritems():
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

    def getTitle(self):
        location = urlparse.urlparse(self.url).netloc
        return re.sub(r'^www\.', '', location)

    def getSetAbbrv(self, setId):
        return card.sets.getAbbreviation(self.sourceSpecificSets.get(setId, setId))

    def makeRequest(self, queryText):
        queryText = queryText.replace(u'`', "'").replace(u'’', "'")
        return lxml.html.document_fromstring(core.network.getUrl(self.cardQueryUrlTemplate.format(urllib.quote(queryText))).decode(self.encoding))


class AngryBottleGnome(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'Promo - Special': 'Media Inserts',
            'Prerelease Events': 'Prerelease & Release Cards',
            'Release Events': 'Prerelease & Release Cards',
            'Launch Party': 'Magic: The Gathering Launch Parties',
        }
        super(AngryBottleGnome, self).__init__('http://angrybottlegnome.ru', '/shop/search/{}/filter/instock', 'utf-8', sourceSpecificSets)
        # <div class = "abg-float-left abg-card-margin abg-card-version-instock">Английский, M/NM  (30р., в наличии: 1)</div>
        # <div class = "abg-float-left abg-card-margin abg-card-version-instock">Итальянский, M/NM  Фойл (180р., в наличии: 1)</div>
        self.cardInfoRegexp = re.compile(r'(?P<language>[^,]+),\s*(?P<condition>[\S]+)\s*(?P<foilness>[^\(]+)?\s*\((?P<price>\d+)[^\d]*(?P<count>\d+)\)')

    def query(self, queryText):
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
        searchResults = self.makeRequest(queryText)
        for resultsEntry in searchResults.cssselect('#search-results tbody tr'):
            dataCells = resultsEntry.cssselect('td')
            cardName = dataCells[0].cssselect('a')[0].text
            cardSet = dataCells[1].cssselect('a')[0].text
            cardRelativeUrl = dataCells[0].cssselect('a')[0].attrib['href']
            cardVersions = lxml.html.document_fromstring(core.network.getUrl(urlparse.urljoin(self.url, cardRelativeUrl)))
            for cardVersion in cardVersions.cssselect('.abg-card-version-instock'):
                rawInfo = self.cardInfoRegexp.match(cardVersion.text).groupdict()
                #print(rawInfo['language'].encode('cp866'))
                yield {
                    'name': cardName,
                    'set': self.getSetAbbrv(cardSet),
                    'language': core.language.getAbbreviation(rawInfo['language']),
                    'condition': _CONDITIONS[rawInfo['condition']],
                    'foilness': bool(rawInfo['foilness']),
                    'count': int(rawInfo['count']),
                    'price': decimal.Decimal(rawInfo['price']),
                    'currency': core.currency.RUR,
                    'source': self.getTitle(),
                }


class MtgRuShop(CardSource):
    def __init__(self, url):
        super(MtgRuShop, self).__init__(url, '/catalog.phtml?Title={}', 'cp1251', MTG_RU_SPECIFIC_SETS)

    def query(self, queryText):
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
        searchResults = self.makeRequest(queryText)
        for resultsEntry in searchResults.cssselect('#Catalog tr'):
            dataCells = resultsEntry.cssselect('td')
            language = core.language.getAbbreviation(os.path.basename(urlparse.urlparse(dataCells[1].cssselect('img')[0].attrib['src']).path))
            nameSelector = 'span.CardName' if language == 'EN' else 'span.Zebra'
            yield {
                'name': dataCells[2].cssselect(nameSelector)[0].text,
                'set': self.getSetAbbrv(dataCells[0].cssselect('img')[0].attrib['alt']),
                'language': language,
                'foilness': bool(dataCells[3].text),
                'count': int(re.match(r'(\d+)', dataCells[5].text).group(0)),
                'price': decimal.Decimal(re.match(r'(\d+)', dataCells[6].text.replace('`', '')).group(0)),
                'currency': core.currency.RUR,
                'source': self.getTitle(),
            }


class Amberson(MtgRuShop):
    def __init__(self):
        super(Amberson, self).__init__('http://amberson.mtg.ru')


class ManaPoint(MtgRuShop):
    def __init__(self):
        super(ManaPoint, self).__init__('http://manapoint.mtg.ru')


class MagicMaze(MtgRuShop):
    def __init__(self):
        super(MagicMaze, self).__init__('http://magicmaze.mtg.ru')


class MtgSale(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'MI': 'Mirrodin',
            'MR': 'Mirage',
            'TP': 'Tempest',
        }
        super(MtgSale, self).__init__('http://mtgsale.ru', '?Name={}', 'utf-8', sourceSpecificSets)

    def query(self, queryText):
        searchResults = self.makeRequest(queryText)
        for resultsEntry in searchResults.cssselect('.goodstable tr')[1:]:
            #print(resultsEntry.cssselect('.tablelanguage img')[0].attrib['title'].lower().encode('cp866'))
            language = core.language.getAbbreviation(resultsEntry.cssselect('.tablelanguage img')[0].attrib['title'])
            nameSelector = '.tablename a' if language == 'EN' else '.tablename .tabletranslation'
            yield {
                'name': resultsEntry.cssselect(nameSelector)[0].text,
                'set': self.getSetAbbrv(resultsEntry.cssselect('.tableset')[0].text),
                'language': language,
                'condition': _CONDITIONS[resultsEntry.cssselect('.tablecondition')[0].text],
                'foilness': bool(resultsEntry.cssselect('.tablekind')[0].text.replace(u'\xa0', u'')),
                'count': int(re.match(r'(\d+)', resultsEntry.cssselect('.tablestock')[0].text).group(0)),
                'price': decimal.Decimal(re.match(r'(\d+)', resultsEntry.cssselect('.tableprice')[0].text.strip()).group(0)),
                'currency': core.currency.RUR,
                'source': self.getTitle(),
            }


class CardPlace(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'DCI Legends': 'Media Inserts',
            'Starter': 'Starter 1999',
            "OverSize Cards": 'Oversized Cards',
            'Premium deck: Graveborn': 'Premium Deck Series: Graveborn',
            'Release & Prerelease cards': 'Prerelease & Release Cards',
        }
        super(CardPlace, self).__init__('http://cardplace.ru', '/directory/new_search/{}/singlemtg', 'utf-8', sourceSpecificSets)

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

    def query(self, queryText):
        searchResults = self.makeRequest(queryText)
        for resultsEntry in searchResults.cssselect('#mtgksingles tbody tr'):
            dataCells = resultsEntry.cssselect('td')
            language = core.language.getAbbreviation(os.path.basename(urlparse.urlparse(self.url + dataCells[3].cssselect('img')[0].attrib['src']).path))
            cardId = None
            cardName = dataCells[2].cssselect('a')[0].text
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
            yield {
                'id': int(cardId) if cardId else None,
                'name': cardName,
                'foilness': len(nameImages) > 0 and nameImages[0].attrib['title'] == 'FOIL',
                'set': self.getSetAbbrv(dataCells[1].cssselect('b')[0].text.strip("'")),
                'language': language,
                'price': decimal.Decimal(re.match(r'([\d\.]+)', dataCells[6].text.strip()).group(0)),
                'currency': core.currency.RUR,
                'count': int(re.match(r'(\d+)', dataCells[7].text.strip()).group(0)),
                'source': self.getTitle(),
            }


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
            'shuma0963',  # shame on you!
        ]
        self.knownShopSourceSubstrings = [
            'shop.mymagic.ru',
        ]
        super(MtgRu, self).__init__('http://mtg.ru', '/exchange/card.phtml?Title={}&Amount=1', 'cp1251', MTG_RU_SPECIFIC_SETS)

    def query(self, queryText):
        searchResults = self.makeRequest(queryText)
        for userEntry in searchResults.cssselect('table.NoteDivWidth'):
            userInfo = userEntry.cssselect('tr table')[0]
            nickname = userInfo.cssselect('tr th')[0].text
            exchangeUrl = userInfo.cssselect('tr td')[-1].cssselect('a')[0].attrib['href']
            if not any(source in exchangeUrl for source in self.sourceSubstringsToExclude):

                cardSource = self.getTitle() + '/' + nickname.lower().replace(' ', '_')
                if any(substring in exchangeUrl for substring in self.knownShopSourceSubstrings):
                    cardSource = urlparse.urlparse(exchangeUrl).netloc
                elif not exchangeUrl.endswith('.html'):
                    cardSource = exchangeUrl
                    print('Shop found: {}'.format(exchangeUrl))

                for cardInfo in userEntry.cssselect('table.CardInfo'):

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

                    yield {
                        'id': cardId,
                        'name': cardInfo.cssselect('th.txt0')[0].text,
                        'foilness': foilness,
                        'set': self.getSetAbbrv(setSource),
                        'language': language,
                        'price': price,
                        'currency': core.currency.RUR,
                        'count': int(cardInfo.cssselect('td.txt15 b')[0].text.split()[0]),
                        'source': cardSource,
                        'url': urlparse.urljoin(self.url, exchangeUrl),
                    }


class Untap(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'New Phyrxia': 'New Phyrexia',
        }
        super(Untap, self).__init__('http://untap.ru', '/search?controller=search&search_query={}', 'utf-8', sourceSpecificSets)

    def query(self, queryText):
        searchResults = self.makeRequest(queryText)
        for entry in searchResults.cssselect('.product-container .right-block'):
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

            yield {
                'name': detailsParts[0],
                'condition': _CONDITIONS[condition],
                'foilness': foilness,
                'set': setId,
                'language': language,
                'price': price,
                'currency': priceCurrency,
                'count': count,
                'source': self.getTitle(),
                'url': detailsUrl,
            }


class CenterOfHobby(CardSource):
    def __init__(self):
        sourceSpecificSets = {
            'LE': 'Legions',
        }
        super(CenterOfHobby, self).__init__('http://www.centerofhobby.ru', '/catalog/mtgcards/search/?card_name={}', 'utf-8', sourceSpecificSets)

    def query(self, queryText):
        searchResults = self.makeRequest(queryText)
        prevResult = None
        for entry in searchResults.cssselect('.mtg_table tr')[1:]:
            cells = entry.cssselect('td')

            isChildEntry = len(entry.cssselect('.child_card')) > 0
            if isChildEntry:
                cardName = cells[2].cssselect('div')[0].text
                cardSet = prevResult['set']
                cardUrl = prevResult['url']
            else:
                cardName = cells[2].cssselect('a')[0].cssselect('b')[0].text
                cardSet = re.match(r'r_([^_]+)_.+', os.path.basename(cells[1].cssselect('img')[0].attrib['src'])).group(1)
                cardUrl = cells[2].cssselect('a')[0].attrib['href']

            cardLanguage = re.match(r'^lang_(.+)$', cells[2].attrib['class']).group(1)
            cardCount = int(cells[5].text) if cells[5].text.isdigit() else 0
            cardPrice = None
            if cardCount > 0:
                cardPrice = decimal.Decimal(''.join(re.match(r'([\d\s]+).*', cells[6].text).group(1).split()))

            # Эвристика для обхода бага на сайте.
            if cardLanguage == '$card_lang':
                cardLanguage = guessCardLanguage(cardName)
            if cardLanguage is not None:
                cardLanguage = core.language.getAbbreviation(cardLanguage)

            result = {
                'id': cells[0].text,
                'name': cardName,
                # 'foilness': foilness, TODO
                'set': self.getSetAbbrv(cardSet.upper()),
                'language': cardLanguage,
                'price': cardPrice,
                'currency': core.currency.RUR,
                'count': cardCount,
                'source': self.getTitle(),
                'url': cardUrl,
            }
            prevResult = result.copy()
            if cardCount > 0:
                yield result


class TtTopdeck(CardSource):
    def __init__(self):
        self.excludedSellers = [
            'angrybottlegnome',
            'mtgsale',
            'shuma0963',  # shame on you!
        ]
        super(TtTopdeck, self).__init__('http://tt.topdeck.ru', '/?req={}&mode=sell&group=card', 'utf-8', {})

    def query(self, queryText):
        searchResults = self.makeRequest(queryText)
        for entry in searchResults.cssselect('table table tr')[1:]:
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
                    detailsString = detailsString

                    dollarPriceMatch = re.match(r'.*(\d+)\s*\$.*', detailsString)
                    if dollarPriceMatch:
                        priceValue = decimal.Decimal(dollarPriceMatch.group(1))
                        priceCurrency = core.currency.USD

                    foil = any(foilString in detailsString for foilString in ['foil', u'фойл', u'фоил'])

                    letterClusters = tools.string.splitByNonLetters(detailsString)

                    for cluster in letterClusters:
                        cardSet = card.sets.tryGetAbbreviationCaseInsensitive(cluster)
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

                # Если цена и количество перепутаны местами
                if countValue > 50 and priceValue < 50:
                    countValue, priceValue = int(priceValue), decimal.Decimal(countValue)

                result = {
                    'name': cells[3].text,
                    'foilness': foil,
                    'set': cardSet,
                    'language': core.language.getAbbreviation(cardLanguage) if cardLanguage else None,
                    'price': priceValue,
                    'currency': priceCurrency,
                    'count': countValue,
                    'condition': cardCondition,
                    'source': 'topdeck.ru/' + sellerNickname.lower().replace(' ', '_'),
                    'url': sellerAnchor.attrib['href'],
                }
                yield result


def getCardSourceClasses():
    return [
        Amberson,
        AngryBottleGnome,
        CardPlace,
        ManaPoint,
        MagicMaze,
        MtgSale,
        MtgRu,
        Untap,
        CenterOfHobby,
        TtTopdeck
    ]
