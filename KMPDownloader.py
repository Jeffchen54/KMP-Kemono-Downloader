from multiprocessing import Semaphore
import threading
from threading import Lock
import requests
from bs4 import BeautifulSoup, ResultSet
import os
import re
import queue
import time
import sys
import cfscrape
from zipfile import ZipFile
from tqdm import tqdm
import logging
from zipfile import BadZipFile
from HashTable import HashTable
from HashTable import KVPair
from datetime import timedelta

"""
Simple kemono.party downloader relying on html parsing and download by url
Using multithreading
- 
@author Jeff Chen
@version 0.4
@last modified 5/17/2022
"""

# Settings #################################################### True to automatically unzip files or not, unzipped files may have corrupted filenames
TIME_BETWEEN_CHUNKS = 2  # Time between Internet activities

containerPrefix = "https://kemono.party"
# DO NOT EDIT ################################################
# Download task queue, Contains tuples in the structure: (func(),(args1,args2,...))
download_queue = queue.Queue(-1)
downloadables = Semaphore(0)     # Avalible downloadable resource device
# Registers a directory, combats multiple posts using the same name
register = HashTable(10)
fcount = 0
fcount_mutex = Lock()
tname = threading.local()
kill = False


class Error(Exception):
    """Base class for other exceptions"""
    pass


class UnknownURLTypeException(Error):
    """Raised when url type cannot be determined"""
    pass


class UnspecifiedDownloadPathException(Error):
    """Raised when download path is not given"""
    pass


class downThread(threading.Thread):
    """
    Fully generic threadpool where tasks of any kind is stored and retrieved in task_queue,
    threads are daemon threads and can be killed using kill variable. 
    """
    __id: int

    def __init__(self, id: int) -> None:
        """
        Initializes thread with a thread name
        Param: 
        id: thread identifier
        """
        self.__id = id
        super(downThread, self).__init__(daemon=True)

    def run(self) -> None:
        """
        Worker thread job. Blocks until a task is avalable via downloadables
        and retreives the task from download_queue
        """
        tname.name = "Thread #" + str(self.__id)
        while True:
            # Wait until download is available
            downloadables.acquire()

            # Check kill signal
            if kill:
                return

            # Pop queue and download it
            todo = download_queue.get()
            todo[0](*todo[1])
            download_queue.task_done()


class KMP:
    """
    Kemono.party downloader class
    """
    __folder: str
    __unzip: bool
    __tcount: int
    __chunksz: int

    def __init__(self, folder: str, unzip: bool, tcount: int | None, chunksz: int | None) -> None:
        """
        Initializes all variables. Does not run the program

        Param:
            folder: Folder to download to, cannot be None
            uinzip: True to automatically unzip files, false to not
            tcount: Number of threads to use, max thread count is 12, default is 6
            chunksz: Download chunk size, default is 1024 * 1024 * 64
        """
        tname.name = "main"
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

    def __download_file(self, src: str, fname: str) -> None:
        """
        Downloads file at src. Skips duplicate files

        Param:
        src: src of image to download
        fname: what to name the file to download
        """
        logging.debug("Downloading " + fname + " from " + src)
        scraper = cfscrape.create_scraper()
        r = None
        while not r:
            try:
                # Get download size
                r = scraper.request('HEAD', src)
            except(requests.exceptions.ConnectTimeout):
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
                    data = scraper.get(src, stream=True)

                    # Download the file
                    with open(fname, 'wb') as fd, tqdm(
                            desc=fname,
                            total=int(fullsize),
                            unit='iB',
                            unit_scale=True,
                            leave=False,
                            bar_format=tname.name +
                        " (" + str(download_queue.qsize()) + ")->" +
                        f + '[{bar}{r_bar}]',
                            unit_divisor=int(1024)) as bar:
                        for chunk in data.iter_content(chunk_size=self.__chunksz):
                            sz = fd.write(chunk)
                            fd.flush()
                            bar.update(sz)
                            downloaded += sz
                        time.sleep(TIME_BETWEEN_CHUNKS)
                        bar.clear()

                        fcount_mutex.acquire()
                        global fcount
                        fcount += 1
                        fcount_mutex.release()
                        if(os.stat(fname).st_size == int(fullsize)):
                            done = True
                except requests.exceptions.ChunkedEncodingError:
                    logging.debug(
                        "Chunked encoding error has occured, server has likely disconnected, download has restarted")
                scraper.close()

        # Unzip file if specified
        if self.__unzip and 'zip' in fname:
            self.__extract_zip(fname, fname.rpartition('/')[0] + '/')

    def __extract_zip(self, zippath: str, destpath: str) -> None:
        """
        Extracts a zip file to a destination. Does nothing if file
        is password protected.

        Param:
        unzip: full path to zip file included zip file itself
        destpath: full path to destination
        """
        try:
            with ZipFile(zippath, 'r') as zip:
                zip.extractall(destpath)
            os.remove(zippath)
        except BadZipFile:
            logging.critical("Unzipping a non zip file has occured, please check if file has been downloaded properly" +
                             "\n + ""File name: " + zippath + "\n" + "File size: " + str(os.stat(zippath).st_size))
        except RuntimeError:
            logging.debug("File name: " + zippath + "\n" +
                          "File size: " + str(os.stat(zippath).st_size))

    def __trim_fname(self, fname: str) -> str:
        """
        Trims fname, returns result. Extensions are kept:
        For example
        "/data/2f/33/2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.txt?f=File.txt"
        -> 2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.txt 

        Param: 
        fname: file name
        Pre: fname follows above convention
        Return: trimmed filename with extension
        """

        first = fname.split("?")[0].split("?")
        second = first[0].split("/")
        return second[len(second) - 1]

    def __download_all_files(self, imgLinks: ResultSet, dir: str) -> None:
        """
        Puts all urls in imgLinks into download queue

        Param:
        imgLinks: all image links within a container
        dir: where to save the images
        """
        counter = 0
        for link in imgLinks:
            download = link.get('href')
            extension = (self.__trim_fname(download).split('.'))
            # download_queue.put((containerPrefix + download, dir +
            #                str(counter) + "." + extension[len(extension) - 1]))
            src = containerPrefix + download
            fname = dir + str(counter) + "." + extension[len(extension) - 1]
            download_queue.put((self.__download_file, (src, fname)))
            downloadables.release()
            counter += 1

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
        """
        # Get HTML request and parse the HTML for image links and title
        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, 'html.parser')
        while "500 Internal Server Error" in soup.find("title"):
            logging.error("500 Server error encountered at " +
                          url + ", retrying...")
            time.sleep(TIME_BETWEEN_CHUNKS)
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'html.parser')
        imgLinks = soup.find_all("a", class_="fileThumb")
        titleDir = root + \
            (re.sub(r'[^\w\-_\. ]', '_', soup.find("title").text.strip())
             ).split("/")[0] + "/"
        # Check if directory has been registered
        value = register.hashtable_lookup_value(titleDir)
        if value != None:  # If register, update titleDir and increment value
            register.hashtable_edit_value(titleDir, value + 1)
            titleDir = titleDir[:len(titleDir) - 1] + "(" + str(value) + ")/"
        else:   # If not registered, add to register at value 1
            register.hashtable_add(KVPair[str, int](titleDir, 1))

        # Add to directory
        if not os.path.isdir(titleDir):
            os.makedirs(titleDir)
        reqs.close()
        # Download image links
        self.__download_all_files(imgLinks, titleDir)

        # Get post content
        content = soup.find("div", class_="post__content")

        if content:
            if(os.path.exists(titleDir + "post__content.txt")):
                logging.debug("Skipping duplicate post_content download")
            else:
                with open(titleDir + "post__content.txt", "w", encoding="utf-8") as fd:
                    fd.write(content.text)
                    links = content.find_all("a")
                    for link in links:
                        url = link.get('href')
                        fd.write("\n" + url)

        # Download post attachments
        attachments = soup.find_all("a", class_="post__attachment-link")
        if attachments:
            for attachment in attachments:
                download = attachment.get('href')
                # download_queue.put((containerPrefix + download,
                #               titleDir + self.__trim_fname(download)))
                src = containerPrefix + download
                fname = titleDir + self.__trim_fname(download)
                download_queue.put((self.__download_file, (src, fname)))
                downloadables.release()

    def __process_window(self, url: str, continuous: bool) -> None:
        """
        Processes a single main artist window
        Param: 
            url: url of the main artist window
            continuous: True to attempt to visit next pages of content, False to not 
        """
        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, 'html.parser')
        reqs.close()
        # Create directory
        artist = soup.find("meta", attrs={'name': 'artist_name'})
        titleDir = self.__folder + re.sub(r'[^\w\-_\. ]', '_',
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
                    containerPrefix + content.get('href'), titleDir)

            if continuous:
                # Move to next window
                # time.sleep(TIME_BETWEEN_CHUNKS)
                counter += 25
                reqs = requests.get(url + suffix + str(counter))
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
            #download_queue.put((self.__process_window, (url, False)))
            self.__process_window(url, False)
        elif "post" in url:
            # Build directory
            reqs = requests.get(url)
            if(reqs.status_code >= 400):
                logging.error("Status code " + str(reqs.status_code))
            soup = BeautifulSoup(reqs.text, 'html.parser')
            artist = soup.find("a", attrs={'class': 'post__user-name'})
            titleDir = self.__folder + \
                re.sub(r'[^\w\-_\. ]', '_', artist.text.strip()) + "/"
            if not os.path.isdir(titleDir):
                os.makedirs(titleDir)
            reqs.close()

            # Process container
            #download_queue.put((self.__process_container, (url, titleDir)))
            self.__process_container(url, titleDir)
        elif 'user' in url:
            #download_queue.put((self.__process_window, (url, True)))
            self.__process_window(url, True)
        else:
            raise UnknownURLTypeException

    def __create_threads(self, count: int) -> list:
        """
        Creates count number of downThreads

        Param:
        count: how many threads to create
        """
        threads = []
        # Spawn threads
        for i in range(0, count):
            threads.append(downThread(i))
            threads[i].start()
        return threads

    def __kill_threads(self, threads: list) -> None:
        """
        Kills all threads in threads

        Param:
        threads: threads to kill
        """
        global kill
        kill = True

        for i in range(0, len(threads)):
            downloadables.release()

        for i in threads:
            i.join()

        kill = False
        logging.info(str(len(threads)) + " threads have been terminated")

    def routine(self, url: str | list[str] | None) -> None:
        """
        Main routine, processes an 3 kinds of artist links specified in the project spec.
        if url is None, ask for a url.

        Param:
        url: supported url(s), if single string, process single url, if list, process multiple
            urls. If None, ask user for a url
        """

        # Generate threads #########################
        threads = self.__create_threads(self.__tcount)

        # Get url to download ######################
        # List type url
        if isinstance(url, list):
            with open(url, "r") as fd:
                for line in fd:
                    line = line.strip()
                    if len(line) > 0:
                        self.__call_and_interpret_url(line)

        else:
            while not url or "https://kemono.party" not in url:
                url = input("Input a url, or type 'quit' to exit> ")

                if(url == 'quit'):
                    self.__kill_threads(threads)
                    return

            self.__call_and_interpret_url(url)
        # Close threads ###########################
        download_queue.join()
        self.__kill_threads(threads)
        logging.info("Files downloaded: " + str(fcount))


def help() -> None:
    logging.info(
        "Switches: Can be combined in any order!")
    logging.info("No switch : Prompts user with download url")
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
                urls = sys.argv[pointer + 1], "r"
                pointer += 2
            elif sys.argv[pointer] == '-v':
                unzip = True
                pointer += 1
                logging.info("UNZIP -> " + str(unzip))
            elif sys.argv[pointer] == '-d' and len(sys.argv) >= pointer:
                folder = sys.argv[pointer + 1]
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

    if folder:
        downloader = KMP(folder, unzip, tcount, chunksz)
        downloader.routine(urls)
    else:
        help()
    end_time = time.monotonic()
    logging.info(timedelta(seconds=end_time - start_time))


if __name__ == "__main__":
    main()
