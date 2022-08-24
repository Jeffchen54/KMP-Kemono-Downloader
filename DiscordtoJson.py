"""
Simple JSON scraper for Kemono.party discord content.

@author: Jeff Chen
@last modified: 6/12/2022
"""
from cfscrape import CloudflareScraper
import logging
import requests.adapters
from Threadpool import ThreadPool
from threading import Semaphore, Thread
from threading import Lock
import cfscrape



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

    def discord_lookup_all(self, channelID:str|None, threads:int=6)->dict|list:
        """
        Similar to discord_channel_lookup() but processes everything, not just in segments
        
        Param:
            threads: Number of threads to use while looking up js
        """
        # Grab data
        js_buff = []

        # Generate threads and threading vars
        pool = ThreadPool(threads)
        pool.start_threads()
        js_buff_lock = Lock()
        main_sem = Semaphore(0)
        
        # Generate sessions for each thread
        sessions = []
        for i in range(0, threads):
            session = cfscrape.create_scraper(requests.Session())
            adapter = requests.adapters.HTTPAdapter(pool_connections=threads, pool_maxsize=threads, max_retries=0, pool_block=True)
            session.mount('http://', adapter)
            sessions.append(session)
        
        
        # Loop until no more data left
        for i in range(0, threads):
            pool.enqueue((self.discord_lookup_thread_job, (threads, DISCORD_CHANNEL_CONTENT_SKIP_INCRE, i * DISCORD_CHANNEL_CONTENT_SKIP_INCRE, channelID, sessions[i], main_sem, js_buff, js_buff_lock, pool)))

        # Sleep until done
        main_sem.acquire()
        
        # Kill threads
        pool.join_queue()
        pool.kill_threads()
        
        # Kill all adapters
        for session in sessions:
            session.close()
        
        # Return json
        return js_buff
    
    def discord_lookup_thread_job(self, tcount:int, skip:int, curr:int, channelID:str, scraper:CloudflareScraper, main_sem:Semaphore, js_buff:list, js_buff_lock:Lock, pool:ThreadPool) -> None:
        """
        Thread job for worker threads in discord_lookup_all. Processes a segment of 
        data then sends its next segment into thread queue
        
        Param:
            tcount: number of threads used within threadpool. 
            main_sem: Semaphore used to wake up main thread
            skip: skip amount to access next page of content, will be the same for all threads
            curr: current skip number
            channelID: Discord channel id
            scraper: scraper to be used to scrape js
            js_buff: list used to store stuff
            js_buff_lock: lock for js_buff
            pool: Threadpool used for this function
        Pre: main_sem begins on zero
        Pre: tcount number of tasks were/is going to be submitted into threadpool 
        """
        """ Note that cond isn't used because there is a situation where broadcast may be 
        called before calling thread goes to sleep"""
        data = None
        # Process current task
        url = DISCORD_CHANNEL_CONTENT_PRE_API + channelID + DISCORD_CHANNEL_CONTENT_SUF_API + str(curr)
        while not data:
            try:
                data = scraper.get(url, timeout=5, headers=HEADERS)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                logging.info("Connection error, retrying -> url: {s}".format(s=url))
                
        if not data:
            logging.critical("Invalid data scraped -> url: {S}".format(s=url))
        
        # Convert data
        js = data.json()    
            
        
        # Add data to js_buff
        if len(js) > 0:
            js_buff_lock.acquire()
            # If js_buff is too small, extend it
            insert_pos = curr/skip
            space_diff = self.__calculate_additional_list_slots(js_buff, insert_pos)
            
            if(space_diff > 0): 
                addon = [None] * int(space_diff)
                js_buff += addon

            # Add into js buff
            js_buff[int(insert_pos)] = js
            logging.debug("Received " + str(js) + " from " + url)
            js_buff_lock.release()
            
            # Create and add task back into threadpool
            pool.enqueue((self.discord_lookup_thread_job, (tcount, DISCORD_CHANNEL_CONTENT_SKIP_INCRE, curr + tcount * DISCORD_CHANNEL_CONTENT_SKIP_INCRE, channelID, scraper, main_sem, js_buff, js_buff_lock, pool)))
       
        # If is done, broadcast to main thread
        else:
            main_sem.release()

    def __calculate_additional_list_slots(self, l:list, p:int)->int:
        """
        Given the list l and position to insert element p, returns how many more list slots are 
        needed in l to meet p

        Args:
            l (list): list
            p (int): position to insert element

        
        Returns:
            int: how many more list slots needed in l to meet p, if is <=0, no additional slots are needed
        """
        return p - (len(l) - 1)
    
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

    

