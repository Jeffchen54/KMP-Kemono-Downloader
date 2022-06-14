import shutil
from tempfile import tempdir
import tempfile
from threading import Lock
from numpy import full
import requests
from bs4 import BeautifulSoup, ResultSet
import os
import re
import time
import sys
import cfscrape
from tqdm import tqdm
import logging
import patoolib
from patoolib import util
import requests.adapters
import json
import io

from DiscordtoJson import DiscordToJson
from HashTable import HashTable
from HashTable import KVPair
from datetime import timedelta
from Threadpool import ThreadPool

"""
Simple kemono.party downloader relying on html parsing and download by url
Using multithreading
- Significantly improved cases where multiple zip files unzip to the exact same destination, creates second
    directory instead of overwritting existing files
- Fix file_text.txt issue where random numbers are scraped up
- Emoji support added
- Fixed case where post__content.txt was created even though work does not contain any post content
- No longer downloads patreon url file links in downloads segment
- Adjust numbering algorithm to prevent overwriting, note that bad img links will not be downloaded, leaving gaps in the naming
- Fixed bug where post comments not downloaded if downloading of images occurred
- Limited discord functionality added, downloads every image, and all text. Hyperlinks are recorded as well
@author Jeff Chen
@version 0.5
@last modified 6/11/2022
"""

counter = 0

class Error(Exception):
    """Base class for other exceptions"""
    pass


class UnknownURLTypeException(Error):
    """Raised when url type cannot be determined"""
    pass


class UnspecifiedDownloadPathException(Error):
    """Raised when download path is not given"""
    pass

class DeadThreadPoolException(Error):
    """Raised when download threads are nonexistant or dead"""
    pass


class KMP:
    """
    Kemono.party downloader class
    """
    __folder: str
    __unzip: bool
    __tcount: int
    __chunksz: int
    __threads:ThreadPool
    __session:requests.Session

    # DO NOT EDIT ################################################
    __CONTAINER_PREFIX = "https://kemono.party"
    __register = HashTable(10)    # Registers a directory, combats multiple posts using the same name
    __fcount = 0  # Number of downloaded files
    __fcount_mutex = Lock()   # Mutex for fcount 

    def __init__(self, folder: str, unzip: bool, tcount: int | None, chunksz: int | None) -> None:
        """
        Initializes all variables. Does not run the program

        Param:
            folder: Folder to download to, cannot be None
            uinzip: True to automatically unzip files, false to not
            tcount: Number of threads to use, max thread count is 12, default is 6
            chunksz: Download chunk size, default is 1024 * 1024 * 64
        """
        if folder:
            self.__folder = folder
        else:
            raise UnspecifiedDownloadPathException

        self.__unzip = unzip

        if tcount and tcount > 0:
            self.__tcount = tcount
        else:
            self.__tcount = 6

        if chunksz and chunksz > 0 and chunksz <= 12:
            self.__chunksz = chunksz
        else:
            self.__chunksz = 1024 * 1024 * 64

        # Create session ###########################
        self.__session = cfscrape.create_scraper(requests.Session())
        adapter = requests.adapters.HTTPAdapter(pool_connections=self.__tcount, pool_maxsize=self.__tcount, max_retries=0, pool_block=True)
        self.__session.mount('http://', adapter)

    def reset(self):
        """
        Resets register and download count
        """
        self. __register = HashTable(10)
        self.__fcount = 0
    def close(self):
        """
        Closes KMP download session, cannot be reopened 
        """
        self.__session.close()

    def __download_file(self, src: str, fname: str) -> None:
        """
        Downloads file at src. Skips duplicate files
        Param:
            src: src of image to download
            fname: what to name the file to download, with extensions
        """
        logging.debug("Downloading " + fname + " from " + src)
        r = None
        while not r:
            try:
                # Get download size
                r = self.__session.request('HEAD', src, timeout=5)

                if r.status_code >= 400:
                    logging.critical("Link provided cannot be downloaded from, possibly a dead third party link: " + src)
                    return

            except(requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                logging.debug("Connection request unanswered, retrying")
        fullsize = r.headers.get('Content-Length')
        downloaded = 0
        f = fname.split('/')[len(fname.split('/')) - 1]
        # If file cannot be downloaded, it is most likely an invalid file
        if fullsize == None:
            logging.critical("Download was attempted on an undownloadable file, details described")
            logging.critical("src: " + src + "\npath: " + fname)
        # Download and skip duplicate file
        elif not os.path.exists(fname) or os.stat(fname).st_size != int(fullsize): 
            done = False
            while(not done):
                try:
                    # Download file to memory
                    data = None
                    while not data:
                        try:
                            data = self.__session.get(src, stream=True, timeout=5, headers={'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36'})
                        except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                             logging.debug("Connection timeout")
                            
                    # Download the file
                    with open(fname, 'wb') as fd, tqdm(
                            desc=fname,
                            total=int(fullsize),
                            unit='iB',
                            unit_scale=True,
                            leave=False,
                            bar_format= "(" + str(self.__threads.get_qsize()) + ")->" + f + '[{bar}{r_bar}]',
                            unit_divisor=int(1024)) as bar:
                        for chunk in data.iter_content(chunk_size=self.__chunksz):
                            sz = fd.write(chunk)
                            fd.flush()
                            bar.update(sz)
                            downloaded += sz
                        time.sleep(1)
                        bar.clear()

                    self.__fcount_mutex.acquire()
                    self.__fcount += 1
                    self.__fcount_mutex.release()
                    if(os.stat(fname).st_size == int(fullsize)):
                        done = True
                        logging.debug("Downloaded Size (" + fname + ") -> " + fullsize)
                except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError):
                    logging.debug("Chunked encoding error has occured, server has likely disconnected, download has restarted")
                except FileNotFoundError:
                    logging.debug("Cannot be downloaded, file likely a link, not a file ->" + fname)
                    done = True



            # Unzip file if specified
            if self.__unzip and self.__supported_zip_type(fname):
                self.__extract_zip(fname, fname.rpartition('/')[0] + '/')

    def __supported_zip_type(self, fname:str) -> bool:
        """
        Checks if a file is a zip file (7z, zip, rar)

        Param:
            fname: zip file name or path
        Return True if zip file, false if not
        """
        extension = fname.rpartition('/')[2]

        return 'zip' in extension or 'rar' in extension or '7z' in extension
        
    def __extract_zip(self, zippath: str, destpath: str) -> None:
        """
        Extracts a zip file to a destination. Does nothing if file
        is password protected. Zipfile is deleted if extraction is 
        successfiul

        Param:
        unzip: full path to zip file included zip file itself
        destpath: full path to destination
        """

        # A tempdir is used to bypass Window's 255 char limit when unzipping files
        with tempfile.TemporaryDirectory(prefix="temp") as dirpath:
            try:
                patoolib.extract_archive(zippath, outdir=dirpath + '/', verbosity=-1, interactive=False)

                for f in os.listdir(dirpath):
                    if os.path.isdir(os.path.abspath(dirpath + "/" + f)):
                        downloaded = False
                        destpath += '/'
                        while not downloaded:
                            try:
                                shutil.copytree(os.path.abspath(dirpath + "/" + f), os.path.abspath(destpath + f), dirs_exist_ok=False)
                                downloaded = True
                            except FileExistsError as e:
                                # If duplicate file/dir is found, it will be stashed in the same dir but with (n) prepended 
                                counter = 1
                                nextName = e.filename
                                currSz = self.__getDirSz(os.path.abspath(dirpath + "/" + f))
                                # Check directory size of dirpath vs destpath, if same size, we are done
                                done = False
                                while(not done):
                                    # If the next directory does not exists, change destpath to that directory
                                    if not os.path.exists(nextName):
                                        destpath = nextName
                                        done = True
                                    else:
                                        # If directory with same size is found, we are done
                                        dirsize = self.__getDirSz(nextName)
                                        if dirsize == currSz:
                                            done = True
                                            downloaded = True
                                    
                                    # Adjust path for next iteration
                                    if not done:
                                        nextName = destpath + '(' + str(counter) + ')'
                                        counter += 1

                                # Move files from dupe directory to new directory
                        shutil.rmtree(os.path.abspath(dirpath + "/" + f), ignore_errors=True)
                    else:
                        shutil.copy(os.path.abspath(dirpath + "/" + f), os.path.abspath(destpath + "/" + f))
                        os.remove(os.path.abspath(dirpath + "/" + f))

                os.remove(zippath)
            except util.PatoolError as e:
                logging.critical("Unzipping a non zip file has occured or character limit for path has been reached or zip is password protected" +
                                "\n + ""File name: " + zippath + "\n" + "File size: " + str(os.stat(zippath).st_size))
                logging.critical(e)
            except RuntimeError:
                logging.debug("File name: " + zippath + "\n" +
                            "File size: " + str(os.stat(zippath).st_size))



    def __getDirSz(self, dir: str) -> int:
        """
        Returns directory and its content size

        Return directory and its content size
        """
        size = 0
        for dirpath, dirname, filenames in os.walk(dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    size += os.path.getsize(fp)
        return size

    def __trim_fname(self, fname: str) -> str:
        """
        Trims fname, returns result. Extensions are kept:
        For example
        
        When extension length of ?... token is <= 10:
        "/data/2f/33/2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.txt?f=File.txt"
        -> File.txt

        Or

        When extension length of ?... token is > 10:
        "/data/2f/33/2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.jpg?f=File.jpe%3Ftoken-time%3D1570752000..."
        ->2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.jpg

        Or

        When ' ' exists
        'Download まとめDL用.zip'
        -> まとめDL用.zip

        Param: 
        fname: file name
        Pre: fname follows above convention
        Return: trimmed filename with extension
        """
        # Case 3, space
        case3 = fname.partition(' ')[2]
        if case3 != fname and len(case3) > 0:
            return case3

        case1 = fname.rpartition('=')[2]
        # Case 2, bad extension provided
        if len(case1.rpartition('.')[2]) > 6:
            first = fname.rpartition('?')[0]
            return first.rpartition('/')[2]
        
        # Case 1, good extension
        return case1

    def __download_all_files(self, imgLinks: ResultSet, dir: str) -> None:
        """
        Puts all urls in imgLinks into download queue

        Param:
        imgLinks: all image links within a container
        dir: where to save the images
        
        Raise: DeadThreadPoolException when no download threads are available
        """
        if not self.__threads.get_status():
            raise DeadThreadPoolException
        
        global counter
        for link in imgLinks:
            href = link.get('href')
            # Type 1 image - Image in Files section
            if href:
                src = self.__CONTAINER_PREFIX + href
            # Type 2 image - Image in Content section
            else:
                
                target = link.get('src')
               # Polluted link check, Fanbox is notorious for this
                if "downloads.fanbox" not in target:
                     # Hosted on non KMP server
                    if 'http' in target:
                        src = target
                    # Hosted on KMP server
                    else:
                        src = self.__CONTAINER_PREFIX + target
                else:
                    src = None
                
            if src:
                logging.debug("Extracted content link: " + src)
                fname = dir + str(counter) + '.' + self.__trim_fname(src).rpartition('.')[2]

                # Check if the post attachment shares the same name as another post attachemnt
                # Adjust filename if found
                value = self.__register.hashtable_lookup_value(fname)
                if value != None:  # If register, update titleDir and increment value
                    self.__register.hashtable_edit_value(fname, value + 1)
                    split = fname.partition('.')
                    fname = split[0] + "(" + str(value) + ")." + split[2]
                else:   # If not registered, add to register at value 1
                    self.__register.hashtable_add(KVPair[str, int](fname, 1))
                
                self.__threads.enqueue((self.__download_file, (src, fname)))
                counter += 1

    def __download_file_text(self, textLinks:ResultSet, dir:str) -> None:
        """
        Scrapes all text and their links in textLink and saves it to 
        in dir

        Param:
            textLink: Set of links and their text in Files segment
            dir: Where to save the text and links to. Must be a .txt file
        """
        frontOffset = 5
        endOffset = 4
        currOffset = 0
        listSz = len(textLinks)
        strBuilder = []
        # No work to be done if the file already exists
        if os.path.exists(dir) or listSz <= 9:
            return
        
        # Record data
        for txtlink in textLinks:
            if frontOffset > 0:
                frontOffset -= 1
            elif(endOffset < listSz - currOffset):
                text = txtlink.get('href').strip()
                if not text.isnumeric():
                    strBuilder.append(txtlink.text.strip() + '\n')
                    strBuilder.append(text + '\n')
                    strBuilder.append("____________________________________________________________\n")
            currOffset += 1
        
        # Write to file if data exists
        if len(strBuilder) > 0:
            self.__write_utf8("".join(strBuilder), dir, 'w')


            

    def __process_container(self, url: str, root: str) -> None:
        """
        Processes a container which is the page used to store post content

        Supports
        - downloading all visable images
        - content divider (BUG other urls are included)
        - download divider

        Param:
        url: url of the container
        root: directory to store the content
        
        Raise: DeadThreadPoolException when no download threads are available
        """
        logging.debug("Processing: " + url + " to be stored in " + root)
        if not self.__threads.get_status():
            raise DeadThreadPoolException

        # Get HTML request and parse the HTML for image links and title ############
        reqs = None
        while not reqs:
            try:
                reqs = self.__session.get(url, timeout=5)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                 logging.debug("Connection timeout")
        soup = BeautifulSoup(reqs.text, 'html.parser')
        while "500 Internal Server Error" in soup.find("title"):
            logging.error("500 Server error encountered at " +
                          url + ", retrying...")
            time.sleep(2)
            reqs = None
            while not reqs:
                try:
                    reqs = self.__session.get(url, timeout=5)
                except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                    logging.debug("Connection timeout")
            soup = BeautifulSoup(reqs.text, 'html.parser')
        imgLinks = soup.find_all("a", {'class':'fileThumb'})
        titleDir = os.path.join(root, \
            (re.sub(r'[^\w\-_\. ]|[\.]$', '', soup.find("title").text.strip())
             ).split("/")[0] + "/")


        # Check if directory has been registered ###################################
        value = self.__register.hashtable_lookup_value(titleDir)
        if value != None:  # If register, update titleDir and increment value
            self.__register.hashtable_edit_value(titleDir, value + 1)
            titleDir = titleDir[:len(titleDir) - 1] + "(" + str(value) + ")/"
        else:   # If not registered, add to register at value 1
            self.__register.hashtable_add(KVPair[str, int](titleDir, 1))

        # Create directory if not registered
        if not os.path.isdir(titleDir):
            os.makedirs(titleDir)
        reqs.close()

        # Download all 'files' #####################################################
        # Image type
        self.__download_all_files(imgLinks, titleDir)

        # Link type
        self.__download_file_text(soup.find_all('a', {'target':'_blank'}), titleDir + "file__text.txt")

        # Scrape post content ######################################################
        content = soup.find("div", class_="post__content")

        if content:
            if(os.path.exists(titleDir + "post__content.txt")):
                logging.debug("Skipping duplicate post_content download")
            else:
                text = content.getText(separator='\n', strip=True)
                if len(text) > 0:
                    # Text section
                    with open(titleDir + "post__content.txt", "w", encoding="utf-8") as fd:
                        fd.write(text)
                        links = content.find_all("a")
                        for link in links:
                            hr = link.get('href')
                            fd.write("\n" + hr)
                
            # Image Section
            self.__download_all_files(content.find_all('img'), titleDir)

        # Download post attachments ##############################################
        attachments = soup.find_all("a", class_="post__attachment-link")
        if attachments:
            for attachment in attachments:
                download = attachment.get('href')
                # Confirm that attachment not from patreon 
                if 'patreon' not in download:
                    src = self.__CONTAINER_PREFIX + download
                    fname = os.path.join(titleDir, self.__trim_fname(attachment.text.strip()))
                    
                    # Check if the post attachment shares the same name as another post attachemnt
                    # Adjust filename if found
                    value = self.__register.hashtable_lookup_value(fname)
                    if value != None:  # If register, update titleDir and increment value
                        self.__register.hashtable_edit_value(fname, value + 1)
                        split = fname.partition('.')
                        fname = split[0] + "(" + str(value) + ")." + split[2]
                    else:   # If not registered, add to register at value 1
                        self.__register.hashtable_add(KVPair[str, int](fname, 1))

                    self.__threads.enqueue((self.__download_file, (src, fname)))
        
        global counter
        counter = 0

        # Download post comments ################################################
        if(os.path.exists(titleDir + "post__comments.txt")):
                logging.debug("Skipping duplicate post comments")
        elif "patreon" in url or "fanbox" in url:
            comments = soup.find("div", class_="post__comments")
            if comments and len(comments.getText(strip=True)) > 0:
                text = comments.getText(separator='\n', strip=True)
                if(text and text != "No comments found for this post." and len(text) > 0):
                    self.__write_utf8(comments.getText(separator='\n', strip=True), titleDir + "post__comments.txt", 'w')
                   
    def __process_window(self, url: str, continuous: bool) -> None:
        """
        Processes a single main artist window

        Param: 
            url: url of the main artist window
            continuous: True to attempt to visit next pages of content, False to not 
        """
        reqs = None
        while not reqs:
            try:
                reqs = self.__session.get(url, timeout=5)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                 logging.debug("Connection timeout")
        soup = BeautifulSoup(reqs.text, 'html.parser')
        reqs.close()
        # Create directory
        artist = soup.find("meta", attrs={'name': 'artist_name'})
        titleDir = self.__folder + re.sub(r'[^\w\-_\. ]|[\.]$', '',
                                          artist.get('content')) + "/"
        if not os.path.isdir(titleDir):
            os.makedirs(titleDir)

        contLinks = soup.find_all("div", class_="post-card__link")
        suffix = "?o="
        counter = 0

        # Process each window
        while contLinks:
            # Process all links on page
            for link in contLinks:
                content = link.find("a")
                self.__process_container(
                    self.__CONTAINER_PREFIX + content.get('href'), titleDir)

            if continuous:
                # Move to next window
                counter += 25
                reqs = None
                while not reqs:
                    try:
                        reqs = self.__session.get(url + suffix + str(counter), timeout=5)
                    except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                         logging.debug("Connection timeout")
                soup = BeautifulSoup(reqs.text, 'html.parser')
                reqs.close()
                contLinks = soup.find_all("div", class_="post-card__link")
            else:
                contLinks = None

    def __write_utf8(self, text:str, path:str, mode:str) -> None:
        """
        Writes utf-8 text to a file at path

        Param:
            text: text to write
            path: where file to write to is located including file name
            mode: mode to set FIle IO
        """
        with io.open(path, mode=mode,  encoding='utf-8') as fd:
            fd.write(text)

    def __download_discord_js(self, jsList:dict, titleDir:str) -> list[str]:
        """
        Downloads any file found in js and returns text data

        Param:
            jsList: Kemono discord server json to download
            titleDir: Where to save data
        Pre: text_file does not have data from previous runs. Data is appended so old data
                will persist.
        Pre: titleDir exists
        Return: Buffer containing text data
        """
        imageDir = titleDir + "images/"

        # make dir
        if not os.path.isdir(imageDir):
            os.mkdir(imageDir)
        
        stringBuilder = []
        global counter
        # Process each json individually
        for js in reversed(jsList):
            # Add buffer
            stringBuilder.append('_____________________________________________________\n')

            # Process name 
            stringBuilder.append(js.get('author').get('username'))
            stringBuilder.append('\t')

            # Process date
            stringBuilder.append(js.get('published'))
            stringBuilder.append('\n')

            # Process content
            stringBuilder.append(js.get('content'))
            stringBuilder.append('\n')

            # Process embeds
            for e in js.get('embeds'):

                if e.get('type') == "link":
                    stringBuilder.append(e.get('title') + " -> " + e.get('url') + '\n')


            # Add attachments
            for i in js.get('attachments'):
                url = self.__CONTAINER_PREFIX + i.get('path')
                stringBuilder.append(url + '\n\n')
                
                # Check if the attachment is dupe
                value = self.__register.hashtable_lookup_value(url)
                if value == None:   # If not registered, add to register at value 1
                    self.__register.hashtable_add(KVPair[str, int](url, 1))
                
                    # Download the attachment
                    self.__threads.enqueue((self.__download_file, (url, imageDir + str(counter) + '.' + url.rpartition('.')[2])))
                    counter += 1
                # If is on the register, do not download the attachment

        # Write to file
        return stringBuilder

    def __process_discord_server(self, serverJs:dict, titleDir:str) -> None:
        """
        Process a discord server

        Param:
            serverJS: discord server json token, in format {"id":xxx,"name":xxx}
            titleDir: Where to store discord content
        """
        dir = titleDir + serverJs.get('name') + '/'

        # Make sure a dupe directory does not exists, if so, adjust dir name
        value = self.__register.hashtable_lookup_value(dir)
        if value != None:  # If register, update titleDir and increment value
            self.__register.hashtable_edit_value(dir, value + 1)
            dir = dir[0:len(dir) - 1] + "(" + str(value) + ")/"
        else:   # If not registered, add to register at value 1
            self.__register.hashtable_add(KVPair[str, int](dir, 1))

        text_file = "discord__content.txt"
        # makedir
        if not os.path.isdir(dir):
            os.mkdir(dir)

        # clear data
        elif os.path.exists(dir + text_file):
            os.remove(dir + text_file)
        
        # Read every json on the server and put it into queue
        discordScraper = DiscordToJson()

        js = discordScraper.discord_channel_lookup(serverJs.get("id"), self.__session)
        buffer = []
        while len(js) > 0:
            buffer.insert(0, "".join(self.__download_discord_js(js, dir)))
            js = discordScraper.discord_channel_lookup(None, self.__session)
        
        # Write buffered discord text content to file
        self.__write_utf8("".join(buffer), dir + 'discord__content.txt', 'a')
        global counter
        counter = 0


    def __process_discord(self, url:str, titleDir:str) -> None:
        """ 
        Process discord kemono links using multithreading

        Param:
            url: discord url
            titleDir: directory to store discord content
        """
        discordScraper = DiscordToJson()
        dir = titleDir

        # Makedir
        if not os.path.isdir(dir):
            os.makedirs(dir)

        # Get server ID(s)
        servers = discordScraper.discord_lookup(url.rpartition('/')[2], self.__session)
        
        if len(servers) == 0:
            return
        
        # Process each server
        for s in servers:
            # Process server
            self.__process_discord_server(s, dir)

    def __call_and_interpret_url(self, url: str) -> None:
        """
        Calls a function based on url type
        https://kemono.party/fanbox/user/xxxx -> process_window()
        https://kemono.party/fanbox/user/xxxx?o=xx -> process_window() one page only
        https://kemono.party/fanbox/user/xxxx/post/xxxx -> process_container()
        https://kemono.party/discord/server/xxxx -> process_discord()

        Anything else -> UnknownURLTypeException

        Param:
        url: url to process
        Raise:
        UnknownURLTypeException when url type cannot be determined
        """
        if '?' in url:
            self.__process_window(url, False)
        elif "post" in url:
            # Build directory
            reqs = None
            while not reqs:
                try:
                    reqs = self.__session.get(url, timeout=5)
                except(requests.exceptions.ConnectionError ,requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                     logging.debug("Connection timeout")
            if(reqs.status_code >= 400):
                logging.error("Status code " + str(reqs.status_code))
            soup = BeautifulSoup(reqs.text, 'html.parser')
            artist = soup.find("a", attrs={'class': 'post__user-name'})
            titleDir = self.__folder + \
                re.sub(r'[^\w\-_\. ]|[\.]$', '', artist.text.strip()) + "/"
            if not os.path.isdir(titleDir):
                os.makedirs(titleDir)
            reqs.close()
            # Process container
            self.__process_container(url, titleDir)

        elif 'discord' in url:
            self.__process_discord(url, self.__folder + url.rpartition('/')[2] + "/")


        elif 'user' in url:
            self.__process_window(url, True)
        else:
            raise UnknownURLTypeException

    def __create_threads(self, count: int) -> ThreadPool:
        """
        Creates count number of downThreads and starts it

        Param:
            count: how many threads to create
        Return: Threads
        """
        threads = ThreadPool(count)
        threads.start_threads()
        return threads

    def __kill_threads(self, threads: ThreadPool) -> None:
        """
        Kills all threads in threads. Threads are restarted and killed using a
        switch, deadlocked or infinitely running threads cannot be killed using
        this function.

        Param:
        threads: threads to kill
        """
        threads.join_queue()
        threads.kill_threads()

    def routine(self, url: str | list[str] | None) -> None:
        """
        Main routine, processes an 3 kinds of artist links specified in the project spec.
        if url is None, ask for a url.

        Param:
        url: supported url(s), if single string, process single url, if list, process multiple
            urls. If None, ask user for a url
        """
        # Generate threads #########################
        self.__threads = self.__create_threads(self.__tcount)


        # Get url to download ######################
        # List type url
        if isinstance(url, list):
            for line in url:
                line = line.strip()
                if len(line) > 0:
                    self.__call_and_interpret_url(line)

        # User input url
        else:
            while not url or "https://kemono.party" not in url:
                url = input("Input a url, or type 'quit' to exit> ")

                if(url == 'quit'):
                    self.__kill_threads(self.__threads)
                    return

            self.__call_and_interpret_url(url)
        # Close threads ###########################
        self.__kill_threads(self.__threads)
        logging.info("Files downloaded: " + str(self.__fcount))


def help() -> None:
    """
    Displays help information on invocating this program
    """
    logging.info(
        "Switches: Can be combined in any order!")
    logging.info(
        "-f <textfile.txt> : Download from text file containing links")
    logging.info(
        "-d <path> : REQUIRED - Set download path for single instance, must use '/'")
    logging.info("-v : Enables unzipping of files automatically")
    logging.info(
        "-c <#> : Adjust download chunk size in bytes (Default is 64M)")
    logging.info("-h : Help")
    logging.info("-t <#> : Change download thread count (default is 6)")


def main() -> None:
    """
    Program runner
    """
    #logging.basicConfig(level=logging.DEBUG)
    start_time = time.monotonic()
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG, filename='log.txt', filemode='w')
    folder = False
    urls = False
    unzip = False
    tcount = -1
    chunksz = -1
    if len(sys.argv) > 1:
        pointer = 1
        while(len(sys.argv) > pointer):
            if sys.argv[pointer] == '-f' and len(sys.argv) >= pointer:
                with open(sys.argv[pointer + 1], "r") as fd:
                    urls = fd.readlines()
                pointer += 2
            elif sys.argv[pointer] == '-v':
                unzip = True
                pointer += 1
                logging.info("UNZIP -> " + str(unzip))
            elif sys.argv[pointer] == '-d' and len(sys.argv) >= pointer:
                #folder = dirs.convert_win_to_py_path(dirs.replace_dots_to_py_path(sys.argv[pointer + 1]))
                folder = os.path.abspath(sys.argv[pointer + 1])
                if not folder[len(folder) - 1] == '\\':
                    folder += '\\'
                pointer += 2
                logging.info("FOLDER -> " + folder)
            elif sys.argv[pointer] == '-t' and len(sys.argv) >= pointer:
                tcount = int(sys.argv[pointer + 1])
                pointer += 2
                logging.info("THREAD_COUNT -> " + str(tcount))
            elif sys.argv[pointer] == '-c' and len(sys.argv) >= pointer:
                chunksz = int(sys.argv[pointer + 1])
                pointer += 2
                logging.info("CHUNKSZ -> " + str(chunksz))
            else:
                pointer = len(sys.argv)

    # Run the downloader
    if folder:
        downloader = KMP(folder, unzip, tcount, chunksz)
        downloader.routine(urls)
        downloader.close()
    else:
        help()

    # Report time
    end_time = time.monotonic()
    logging.info(timedelta(seconds=end_time - start_time))


if __name__ == "__main__":
    main()
