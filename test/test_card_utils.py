import unittest

from card.utils import CardUtils


class TestCardUtils(unittest.TestCase):
    def test_make_key(self):
        cases = {
            '': '',
            'Mountain': 'mountain',
            'The Rack': 'therack',
            'Ætherling': 'aetherling',
            '“Ach! Hans, Run!”': 'achhansrun',
            'Лилиана с Завесой': 'лилианасзавесой',
        }
        for t, e in cases.items():
            self.assertEqual(e, CardUtils.make_key(t))

    def test_utf2std(self):
        cases = {
            '': '',
            'Mountain': 'Mountain',
            'The Rack': 'The Rack',
            'Ætherling': 'AEtherling',
            'Лилиана с Завесой': 'Лилиана с Завесой',
            'Ajani’s Last Stand': "Ajani's Last Stand",
            '“Ach! Hans, Run!”': '"Ach! Hans, Run!"',
            'Флагман «Небесный Владыка»': 'Флагман "Небесный Владыка"',
        }
        for t, e in cases.items():
            self.assertEqual(e, CardUtils.utf2std(t))

    def test_std2utf(self):
        cases = {
            '': '',
            'Mountain': 'Mountain',
            'The Rack': 'The Rack',
            'AEtherling': 'Ætherling',
            'Лилиана с Завесой': 'Лилиана с Завесой',
            "Ajani's Last Stand": "Ajani’s Last Stand",
            '"Ach! Hans, Run!"': '“Ach! Hans, Run!”',
            'Флагман "Небесный Владыка"': 'Флагман «Небесный Владыка»',
        }
        for t, e in cases.items():
            self.assertEqual(e, CardUtils.std2utf(t))

    def test_get_primary_name(self):
        cases = {
            '': '',
            'Mountain': 'Mountain',
            'Nicol Bolas, the Ravager|Nicol Bolas, the Arisen': 'Nicol Bolas, the Ravager',
            'Nicol Bolas, the Ravager│Nicol Bolas, the Arisen': 'Nicol Bolas, the Ravager',
            'Fire│Ice': 'Fire',
            'Fire // Ice': 'Fire',
            'Fire / Ice': 'Fire',
        }
        for t, e in cases.items():
            self.assertEqual(e, CardUtils.get_primary_name(t))

    def test_split_name(self):
        cases = {
            '': [''],
            'Mountain': ['Mountain'],
            'Nicol Bolas, the Ravager|Nicol Bolas, the Arisen': ['Nicol Bolas, the Ravager', 'Nicol Bolas, the Arisen'],
            'Nicol Bolas, the Ravager│Nicol Bolas, the Arisen': ['Nicol Bolas, the Ravager', 'Nicol Bolas, the Arisen'],
            'Fire│Ice': ['Fire', 'Ice'],
            'Fire // Ice': ['Fire', 'Ice'],
            'Fire / Ice': ['Fire', 'Ice'],
            'Who│What│When│Where│Why': ['Who', 'What', 'When', 'Where', 'Why'],
        }
        for t, e in cases.items():
            self.assertEqual(e, CardUtils.split_name(t))
