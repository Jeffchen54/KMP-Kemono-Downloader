import shutil
from tempfile import tempdir
import tempfile
import threading
from threading import Lock
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

from HashTable import HashTable
from HashTable import KVPair
from datetime import timedelta
from Threadpool import ThreadPool

"""
Simple kemono.party downloader relying on html parsing and download by url
Using multithreading
- Automatic connection retry when connection is lost with Kemono server
@author Jeff Chen
@version 0.4.2
@last modified 6/11/2022
"""


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
            fname: what to name the file to download
        """
        logging.debug("Downloading " + fname + " from " + src)
        r = None
        while not r:
            try:
                # Get download size
                r = self.__session.request('HEAD', src, timeout=5)
            except(requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                logging.debug("Connection request unanswered, retrying")
        fullsize = r.headers.get('Content-Length')
        downloaded = 0
        f = fname.split('/')[len(fname.split('/')) - 1]
        # Download file, skip duplicate files
        
        if not os.path.exists(fname) or os.stat(fname).st_size != int(fullsize): 
            done = False
            while(not done):
                try:
                    # Download file to memory
                    data = None
                    while not data:
                        try:
                            data = self.__session.get(src, stream=True, timeout=5, headers={'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36', 'cookie':'__ddg1_=uckPSs0T21TEh1iAB4I5; _pk_id.1.5bc1=0767e09d7dfb4923.1652546737.; session=eyJfcGVybWFuZW50Ijp0cnVlLCJhY2NvdW50X2lkIjoxMTg1NTF9.Yn_ctw.BR10xbr1QVttkUyF2PEmolEkvDo; _pk_ref.1.5bc1=["","",1652718344,"https://www.google.com/"]; _pk_ses.1.5bc1=1'})
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
                        shutil.copytree(os.path.abspath(dirpath + "/" + f), os.path.abspath(destpath + "/" + f), dirs_exist_ok=True)
                        shutil.rmtree(os.path.abspath(dirpath + "/" + f), ignore_errors=True)
                    else:
                        shutil.copy(os.path.abspath(dirpath + "/" + f), os.path.abspath(destpath + "/" + f))
                        os.remove(os.path.abspath(dirpath + "/" + f))

                os.remove(zippath)
            except util.PatoolError:
                logging.critical("Unzipping a non zip file has occured or character limit for path has been reached or zip is password protected" +
                                "\n + ""File name: " + zippath + "\n" + "File size: " + str(os.stat(zippath).st_size))
            except RuntimeError:
                logging.debug("File name: " + zippath + "\n" +
                            "File size: " + str(os.stat(zippath).st_size))

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
        if len(case1.rpartition('.')[2]) > 10:
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

        counter = 0
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
                strBuilder.append(txtlink.text.strip() + '\n')
                strBuilder.append(txtlink.get('href') + '\n')
                strBuilder.append("____________________________________________________________\n")
            currOffset += 1
        
        # Write to file if data exists
        if len(strBuilder) > 0:
            with open(dir, 'w') as fd:
                for line in strBuilder:
                    fd.write(line)

            

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
                # Text section
                with open(titleDir + "post__content.txt", "w", encoding="utf-8") as fd:
                    fd.write(content.getText(separator='\n', strip=True))
                    links = content.find_all("a")
                    for link in links:
                        url = link.get('href')
                        fd.write("\n" + url)
                
            # Image Section
            self.__download_all_files(content.find_all('img'), titleDir)

        # Download post attachments ##############################################
        attachments = soup.find_all("a", class_="post__attachment-link")
        if attachments:
            for attachment in attachments:
                download = attachment.get('href')
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


        # Download post comments ################################################
        if(os.path.exists(titleDir + "post__comments.txt")):
                logging.debug("Skipping duplicate post comments")
        elif "patreon" in url or "fanbox" in url:
            comments = soup.find("div", class_="post__comments")
            if comments and len(comments.getText(strip=True)) > 0:
                text = comments.getText(separator='\n', strip=True)
                if(text and text != "No comments found for this post."):
                    with open(titleDir + "post__comments.txt", "w", encoding="utf-8") as fd:
                        fd.write(comments.getText(separator='\n', strip=True))

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

    def __call_and_interpret_url(self, url: str) -> None:
        """
        Calls a function based on url type
        https://kemono.party/fanbox/user/xxxx -> process_window()
        https://kemono.party/fanbox/user/xxxx?o=xx -> process_window() one page only
        https://kemono.party/fanbox/user/xxxx/post/xxxx -> process_container()

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
