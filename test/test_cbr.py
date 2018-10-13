import unittest
from decimal import Decimal

import raven

from core.components.cbr import CentralBankApiClient
from core.utils import Currency
from tcomponents import DummyLogger


class TestCentralBankApiClient(unittest.TestCase):
    CURRENCIES = [Currency.EUR, Currency.RUR, Currency.USD]

    def test_exchange(self):
        client = CentralBankApiClient(DummyLogger(), raven.Client())
        client.update_rates()
        for a in self.CURRENCIES:
            for b in self.CURRENCIES:
                self.assertGreater(client.exchange(Decimal(100), a, b), 0)
