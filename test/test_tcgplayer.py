import os
import unittest
from datetime import datetime

import dotenv

from price.tcgplayer.communicator import TcgPlayerCommunicator


class TestCommunicator(unittest.TestCase):
    def setUp(self):
        dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        self.communicator = TcgPlayerCommunicator(os.getenv('TCG_SECRET_KEY'), os.getenv('TCG_PUBLIC_KEY'), os.getenv('TCG_TOKEN'))

    def tearDown(self):
        token = self.communicator.get_token()
        if token is not None:
            os.putenv('TCG_TOKEN', token)

    def testListGroups(self):
        battlebond = None
        for group in self.communicator.list_groups(TcgPlayerCommunicator.MTG_CATEGORY_ID):
            if group.name == 'Battlebond':
                battlebond = group
                break
        self.assertIsNotNone(battlebond)
        self.assertEqual(battlebond.id, 2245)
        self.assertEqual(battlebond.abbreviation, 'BBD')
        self.assertEqual(battlebond.supplemental, False)
        self.assertEqual(battlebond.published_at, datetime(2018, 6, 8, 0, 0))

    def testListProducts(self):
        for card in self.communicator.list_cards(TcgPlayerCommunicator.MTG_CATEGORY_ID, 2245):
            self.assertEqual(card.id, 166659)
            self.assertEqual(card.category_id, TcgPlayerCommunicator.MTG_CATEGORY_ID)
            self.assertEqual(card.group_id, 2245)
            self.assertEqual(card.name, 'Spire Garden')
            self.assertTrue(card.url.startswith('http'))
            self.assertTrue(card.image_url.startswith('http') and card.image_url.endswith('.jpg'))
            break


if __name__ == '__main__':
    unittest.main()
