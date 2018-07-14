import unittest

from core.utils import StringUtils


class TestStringUtils(unittest.TestCase):
    def test_letters(self):
        self.assertEqual('', StringUtils.letters(''))
        self.assertEqual('', StringUtils.letters('123!#$#()%*)#$(*%'))
        self.assertEqual('aaa', StringUtils.letters('a1a a!'))
        self.assertEqual('aaa', StringUtils.letters('aaa'))

    def test_letter_clusters(self):
        self.assertEqual(['aaa'], StringUtils.letter_clusters('aaa'))
        self.assertEqual(['aa', 'bb', 'cc', 'dd'], StringUtils.letter_clusters('aa|bb cc ^^^ dd'))
        self.assertEqual([], StringUtils.letter_clusters(''))
        self.assertEqual([], StringUtils.letter_clusters('!!! !!!'))
        self.assertEqual([], StringUtils.letter_clusters('123'))
        self.assertEqual(['aa', 'bb'], StringUtils.letter_clusters('aa123__bb'))
