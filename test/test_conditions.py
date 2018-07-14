# coding: utf-8

import unittest

from card.components import ConditionOracle
from core.utils import DummyLogger


class TestConditionOracle(unittest.TestCase):
    def setUp(self):
        self.oracle = ConditionOracle(DummyLogger(), thorough=True)

    def e(self, abbrv: str, strings: list):
        for s in [abbrv] + strings:
            self.assertEqual(abbrv, self.oracle.get_abbreviation(s), s)

    def test_match(self):
        self.e('HP', ['Heavily Played', 'Hardly Played', 'ХП', 'poor'])
        self.e('MP', ['Moderately Played', 'Played', 'МП', 'f', 'fine'])
        self.e('NM', ['Near Mint', 'M/NM', 'M', 'Mint', 'Excellent', 'great', 'НМ', 'nm', 'nm/m', 'm'])
        self.e('SP', ['Slightly Played', 'СП', 'vf', 'very fine'])

    def test_order(self):
        self.assertEqual(('HP', 'MP', 'SP', 'NM'), ConditionOracle.get_order())
