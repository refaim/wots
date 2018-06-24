# coding: utf-8

import decimal
import json
import sys
import threading

import lxml

import core.network
from core.logger import WotsLogger

RUR = 'RUR'
USD = 'USD'
EUR = 'EUR'

FORMAT_STRINGS = {
    RUR: '{}₽',
    EUR: '€{}',
    USD: '${}',
}
# noinspection PyUnresolvedReferences
if sys.platform.startswith('win32') and sys.getwindowsversion().major <= 5:
    FORMAT_STRINGS[RUR] = '{}р.'

class Converter(object):
    def __init__(self, logger: WotsLogger):
        self.logger = logger
        self.readyEvent = threading.Event()
        self.updateThread = None
        self.exchangeRates = {}

    def update(self):
        if self.updateThread is None or not self.updateThread.is_alive():
            self.updateThread = threading.Thread(name='Currency', target=self._update, args=(self.exchangeRates, self.readyEvent,))
            self.updateThread.daemon = True
            self.updateThread.start()

    def _update(self, results, readyEvent):
        # noinspection PyBroadException
        try:
            tree = lxml.etree.fromstring(core.network.getUrl('http://www.cbr.ru/scripts/XML_daily.asp', self.logger))
            for currency in tree.xpath('/ValCurs/Valute'):
                code = currency.xpath('CharCode')[0].text
                nominal = decimal.Decimal(currency.xpath('Nominal')[0].text.replace(',', '.'))
                value = decimal.Decimal(currency.xpath('Value')[0].text.replace(',', '.'))
                results[code] = (nominal, value,)
            results[RUR] = (1, 1,)
        except:
            # TODO sentry !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.logger.warning('Unable to obtain actual information')
        finally:
            readyEvent.set()

    def convert(self, srcCurrencyCode, dstCurrencyCode, amount):
        result = None
        if srcCurrencyCode in self.exchangeRates and dstCurrencyCode in self.exchangeRates:
            srcNominal, srcNominalValueInRoubles = self.exchangeRates[srcCurrencyCode]
            dstNominal, dstNominalValueInRoubles = self.exchangeRates[dstCurrencyCode]
            result = decimal.Decimal(amount) / srcNominal * srcNominalValueInRoubles / dstNominalValueInRoubles * dstNominal
        return result

    def isReady(self):
        return self.readyEvent.isSet()


def roundPrice(price):
    return int(price)


__formatPriceCache = {}
def formatPrice(amount, currency):
    if amount not in __formatPriceCache:
        __formatPriceCache[amount] = {}
    if currency not in __formatPriceCache[amount]:
        __formatPriceCache[amount][currency] = FORMAT_STRINGS[currency].format(amount)
    return __formatPriceCache[amount][currency]


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)
