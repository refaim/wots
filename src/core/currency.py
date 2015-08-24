# coding: utf-8

import decimal
import lxml
import threading

import core.network

EUR = 'EUR'
RUR = 'RUR'
USD = 'USD'

FORMAT_STRINGS = {
    RUR: u'{}₽',
    EUR: u'€{}',
    USD: u'${}',
}


class Converter(object):
    def __init__(self):
        self.readyEvent = threading.Event()
        self.updateThread = None
        self.exchangeRates = {}

    def update(self):
        if self.updateThread is None or not self.updateThread.is_alive():
            self.updateThread = threading.Thread(name='Currency', target=self._update, args=(self.exchangeRates, self.readyEvent,))
            self.updateThread.daemon = True
            self.updateThread.start()

    def _update(self, results, readyEvent):
        tree = lxml.etree.fromstring(core.network.getUrl('http://www.cbr.ru/scripts/XML_daily.asp'))
        for currency in tree.xpath('/ValCurs/Valute'):
            code = currency.xpath('CharCode')[0].text
            nominal = decimal.Decimal(currency.xpath('Nominal')[0].text.replace(',', '.'))
            value = decimal.Decimal(currency.xpath('Value')[0].text.replace(',', '.'))
            results[code] = (nominal, value,)
        results[RUR] = (1, 1,)
        readyEvent.set()

    def convert(self, srcCurrencyCode, dstCurrencyCode, amount):
        srcNominal, srcNominalValueInRoubles = self.exchangeRates[srcCurrencyCode]
        dstNominal, dstNominalValueInRoubles = self.exchangeRates[dstCurrencyCode]
        return decimal.Decimal(amount) / srcNominal * srcNominalValueInRoubles / dstNominalValueInRoubles * dstNominal

    def isReady(self):
        return self.readyEvent.isSet()


def roundPrice(price):
    return int(price)


def formatPrice(price, currency):
    return FORMAT_STRINGS[currency].format(price)
