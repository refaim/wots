import unittest
from decimal import Decimal

import raven

from core.components.cbr import CentralBankApiClient
from core.utils import Currency, StderrLogger


class TestCentralBankApiClient(unittest.TestCase):
    CURRENCIES = [Currency.EUR, Currency.RUR, Currency.USD]

    @classmethod
    def get_client(cls) -> CentralBankApiClient:
        return CentralBankApiClient(StderrLogger('cbr'), raven.Client())

    def test_empty_client(self):
        client = self.get_client()
        for a in self.CURRENCIES:
            for b in self.CURRENCIES:
                self.assertIsNone(client.exchange(Decimal(100), a, b))

    def test_exchange(self):
        client = self.get_client()
        self.assertTrue(client.update_rates())
        for a in self.CURRENCIES:
            for b in self.CURRENCIES:
                self.assertGreater(client.exchange(Decimal(100), a, b), 0)
