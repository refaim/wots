# coding: utf-8

from decimal import Decimal
from typing import Dict, Optional, Tuple

import lxml.etree
import raven

import core.network
from core.utils import Currency, ILogger, DictUtils


class CentralBankApiClient(object):
    __CURRENCY_CODES = {
        Currency.EUR: 'EUR',
        Currency.RUR: 'RUR',
        Currency.USD: 'USD',
    }

    def __init__(self, logger: ILogger, sentry: raven.Client):
        self.__logger = logger
        self.__sentry = sentry
        self.__currency_ids = DictUtils.flip(self.__CURRENCY_CODES)
        self.__rates: Dict[Currency, Tuple[Decimal, Decimal]] = None

    def exchange(self, amount: Decimal, src_currency: Currency, dst_currency: Currency) -> Optional[Decimal]:
        if self.__rates is None:
            return None
        src_nominal, src_in_roubles = self.__rates[src_currency]
        dst_nominal, dst_in_roubles = self.__rates[dst_currency]
        return amount / src_nominal * src_in_roubles / dst_in_roubles * dst_nominal

    def update_rates(self) -> None:
        self.__rates = {}
        try:
            tree = lxml.etree.fromstring(core.network.getUrl('http://www.cbr.ru/scripts/XML_daily.asp', self.__logger))
            for currency in tree.xpath('/ValCurs/Valute'):
                currency_id = self.__currency_ids.get(self.__tag_text(currency, 'CharCode'))
                if currency_id is not None:
                    self.__rates[currency_id] = (
                        self.__str_to_decimal(self.__tag_text(currency, 'Nominal')),
                        self.__str_to_decimal(self.__tag_text(currency, 'Value')),
                    )
            self.__rates[Currency.RUR] = (Decimal(1), Decimal(1))
        except Exception:
            self.__sentry.captureException()
            self.__rates = None

    @classmethod
    def __tag_text(cls, dom, key: str) -> str:
        return dom.xpath(key)[0].text

    @classmethod
    def __str_to_decimal(cls, value: str) -> Decimal:
        return Decimal(value.replace(',', '.'))
