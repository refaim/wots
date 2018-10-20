# coding: utf-8

from OracleTest import OracleTest
from card.components import LanguageOracle
from core.utils import StderrLogger


class TestLanguageOracle(OracleTest):
    def get_oracle(self):
        return LanguageOracle(StderrLogger('language_oracle'), thorough=True)

    def test_match(self):
        self.e('CN', ['китайский', 'кит', 'chinese', 'chi', 'kit'])
        self.e('DE', ['немецкий', 'нем', 'deutch', 'nem'])
        self.e('EN', ['английский', 'англ', 'анг', 'english', 'eng'])
        self.e('ES', ['испанский', 'исп', 'isp', 'esp', 'spa'])
        self.e('FR', ['французский', 'франц', 'french', 'fre'])
        self.e('IT', ['итальянский', 'итал', 'ita', 'ital'])
        self.e('JP', ['японский', 'яп', 'japanese', 'jap'])
        self.e('KO', ['корейский', 'кор', 'korean', 'kor'])
        self.e('PT', ['португальский', 'пор', 'portuguese', 'por', 'port'])
        self.e('RU', ['русский', 'рус', 'russian', 'rus'])
        self.e('TW', ['тайваньский', 'taiwanese', 'tw'])
        self.e('??', ['other', 'неведомый'])
