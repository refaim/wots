import unittest

from card.components import BaseOracle


class OracleTest(unittest.TestCase):
    def setUp(self):
        self.oracle = self.get_oracle()

    def get_oracle(self) -> BaseOracle:
        raise NotImplementedError()

    def e(self, abbrv: str, strings: list):
        for s in [abbrv] + strings:
            self.assertEqual(abbrv, self.oracle.get_abbreviation(s), s)
