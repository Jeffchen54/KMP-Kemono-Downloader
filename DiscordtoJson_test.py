import unittest
from DiscordtoJson import DiscordToJson
import requests.adapters
import cfscrape
import json
import logging


class DiscordtoJsonTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """
        Creates a session
        """
        logging.basicConfig(level=logging.DEBUG)
        self.scraper = cfscrape.create_scraper(requests.Session())
        adapter = requests.adapters.HTTPAdapter(pool_connections=6, pool_maxsize=6, max_retries=0, pool_block=True)
        self.scraper.mount('http://', adapter)
        self.js = DiscordToJson()

    def test_discord_lookup(self):
        """
        Tests discord lookup
        """
        # No channels

        # One channel
        js = self.js.discord_lookup("https://kemono.party/discord/server/344748294372720643".rpartition('/')[2], self.scraper)
        self.assertEqual(json.dumps(js), '[{"id": "344748969991340033", "name": "tiffys-drawings"}]')

        # Multi channels
        js = self.js.discord_lookup("https://kemono.party/discord/server/634594002624184360".rpartition('/')[2], self.scraper)
        self.assertEqual(json.dumps(js), r'[{"id": "652592122951630850", "name": "100\u5186_100yen"}, {"id": "652563554108571650", "name": "100\u5186_100yen"}, {"id": "652592073785999369", "name": "300\u30d3\u30fc\u30eb_beer"}, {"id": "652551798472835072", "name": "300\u30d3\u30fc\u30eb_beer"}, {"id": "634659046678593536", "name": "\u4f5c\u696d\u4e2d_wip"}]')

    def test_channel_lookup(self):
        """
        Tests discord channel lookup
        """
        # Get first 25
        # 634659046678593536
        js = self.js.discord_channel_lookup("634659046678593536", self.scraper)
        before = json.dumps(js)

        # Get next 25 using None
        js = self.js.discord_channel_lookup(None, self.scraper)
        after = json.dumps(js)
        self.assertNotEqual(before, after)

        # Get next 25 using channel name
        js = self.js.discord_channel_lookup("634659046678593536", self.scraper)
        last = json.dumps(js)
        self.assertNotEqual(last, before)
        self.assertNotEqual(last, after)

        # Switch to another channel 
        js = self.js.discord_channel_lookup("652563554108571650", self.scraper)
        logging.info("first" + str(js[len(js) - 1].get('content')))
        self.assertEqual(str(js[0].get('content')), r'**6月の$1GoogleDriveリンク June $1 Google Drive link: **https://drive.google.com/drive/folders/1nXscFvaEiLRVLf0d7di6ti1iH-7MdZ9F?usp=sharing @everyone')
        self.assertEqual(str(str(js[len(js) - 1].get('content'))), r'> > **6月の$1 MEGA リンク June $1 MEGA link:  **https://mega.nz/folder/z4dk3AhK#0L7XjaYUbH3iffrVpkLIeQ @everyone')
        # End of channel
        js = self.js.discord_channel_lookup(None, self.scraper)
        self.assertEqual(len(js), 0)


    def tearDown(self) -> None:
        """
        Deconstructs session
        """
        self.scraper.close()

if __name__ == '__main__':
    unittest.main()