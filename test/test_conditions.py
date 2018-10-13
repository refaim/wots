# coding: utf-8

from OracleTest import OracleTest
from card.components import ConditionOracle
from tcomponents import DummyLogger


class TestConditionOracle(OracleTest):
    def get_oracle(self):
        return ConditionOracle(DummyLogger(), thorough=True)

    def test_match(self):
        self.e('HP', ['Heavily Played', 'Hardly Played', 'ХП', 'poor'])
        self.e('MP', ['Moderately Played', 'Played', 'МП', 'f', 'fine'])
        self.e('NM', ['Near Mint', 'M/NM', 'M', 'Mint', 'Excellent', 'great', 'НМ', 'nm', 'nm/m', 'm'])
        self.e('SP', ['Slightly Played', 'СП', 'vf', 'very fine'])

    def test_order(self):
        self.assertEqual(('HP', 'MP', 'SP', 'NM'), ConditionOracle.get_order())
