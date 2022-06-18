"""
Simple JSON scraper for Kemono.party discord content.

@author: Jeff Chen
@last modified: 6/12/2022
"""
from cfscrape import CloudflareScraper
import logging
import requests.adapters



DISCORD_LOOKUP_API = "https://kemono.party/api/discord/channels/lookup?q="
DISCORD_CHANNEL_CONTENT_PRE_API = "https://kemono.party/api/discord/channel/"
DISCORD_CHANNEL_CONTENT_SUF_API = "?skip="
DISCORD_CHANNEL_CONTENT_SKIP_INCRE = 25
HEADERS={'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36'}


class DiscordToJson():
    recent:dict = None
    def discord_lookup(self, discordID:str, scraper:CloudflareScraper) -> dict:
        """
        Looks up a discord id using Kemono.party's API and returns 
        the result in JSON format

        Param: 
            discordID: ID of discord channel to grab channel IDs from
            scraper: Scraper to use while scraping kemono 
        Return: channelIDs in JSON format
        """
        # Link URL
        url = DISCORD_LOOKUP_API + discordID
        
        # Grab data
        data = None
        while not data:
            try:
                data = scraper.get(url, timeout=5, headers=HEADERS)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                logging.debug("Connection error, retrying")

        # Convert data
        js = data.json()
        logging.debug("Received " + str(js) + " from " + url)

        # Return json
        return js

    def discord_lookup_all(self, channelID:str|None, scraper:CloudflareScraper)->dict|list:
        """
        Similar to discord_channel_lookup() but processes everything, not just in segments
        """
         # Grab data
        data = None
        skip = 0
        done = False
        js_buff = []

        # Loop until no more data left
        while not done:
            url = DISCORD_CHANNEL_CONTENT_PRE_API + channelID + DISCORD_CHANNEL_CONTENT_SUF_API + str(skip)
            while not data:
                try:
                    data = scraper.get(url, timeout=5, headers=HEADERS)
                except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                    logging.debug("Connection error, retrying")
            
            # Convert data
            js = data.json()
            if len(js) > 0:
                js_buff += js
                logging.debug("Received " + str(js) + " from " + url)
                skip += DISCORD_CHANNEL_CONTENT_SKIP_INCRE
                data = None
            else:
                done = True

        # Return json
        return js_buff

    def discord_channel_lookup(self, channelID:str|None, scraper:CloudflareScraper)->dict|list:
        """
        Looks up a channel's content and returns it. Content is returned in 
        chunks and not all content is returned; however, subsequent calls will
        return results that will always be different.

        Param:
            channelID: 
                channelID of channel to scrape. 
                If is None, scrape starting at the endpoint of the previous scrape
                If is not None, scrape starting the end of the channel
            scarper:
                Scraper: scaraper to use while scraping kemono

        Return: JSON object containing data from the file
        """
        # If None sent but no history, quit
        if not channelID:
            assert(self.recent)

        # If no history, create initial history
        if not self.recent:
            self.recent = {"channelID" : channelID, "skip" : 0}  # it doesn't exist yet, so initialize it
        
        # If history exists and matches, use old data
        if(not channelID or channelID == self.recent.get("channelID")):
            skip = self.recent.get("skip")
            self.recent = {"channelID" : self.recent.get("channelID"), "skip" : skip + DISCORD_CHANNEL_CONTENT_SKIP_INCRE}
            channelID = self.recent.get("channelID")

        # If history exists but does not match, start from beginning
        else:
            skip = 0
            self.recent = {"channelID" : channelID, "skip" : skip + DISCORD_CHANNEL_CONTENT_SKIP_INCRE}
        
        # Grab data
        data = None
        url = DISCORD_CHANNEL_CONTENT_PRE_API + channelID + DISCORD_CHANNEL_CONTENT_SUF_API + str(skip)
        while not data:
            try:
                data = scraper.get(url, timeout=5, headers=HEADERS)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                logging.debug("Connection error, retrying")
        
        # Convert data
        js = data.json()
        logging.debug("Received " + str(js) + " from " + url)

        # Return json
        return js

    

