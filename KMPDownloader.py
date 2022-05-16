from multiprocessing import Semaphore
import threading
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

"""
Simple kemono.party downloader relying on html parsing and download by url
Using multithreading

- Added more robust fix to file not being downloaded fully bug
- Skip duplicate files based on file size
- Removed time between download chunks due to pdf requests chunks being limited to <8KBs in some instances
@author Jeff Chen
@version 0.3.3
@last modified 5/16/2022
"""

# Settings ###################################################
folder = r"D:/User Files/Personal/Cloud Drive/MEGAsync/Nonsensitive/Best/Package/Pixiv/~unsorted/"
unzip = False     # True to automatically unzip files or not, unzipped files may have corrupted filenames
# Higher chunk size gives speed bonus at high memory cost
chunksz = 1024 * 1024 * 64
TIME_BETWEEN_CHUNKS = 2  # Time between Internet activities
# Number of threads, note that download size is bottleneck by numerous factors
tcount = 6
# More threads boost speed of downlaoding many small files but will not if
# downloading a single large file caps download limit
# Larger files may timeout, resulting in incomplete downloads, if this occurs, decrease
# the number of threads or decrease the number of downloads
# URL specific variables <MODIFY AT YOUR RISK> ###############
containerPrefix = "https://kemono.party"
# DO NOT EDIT ################################################
kill = False                     # Thread kill switch
download_queue = queue.Queue(-1)  # Download task queue
downloadables = Semaphore(0)     # Avalible downloadable resource device


class Error(Exception):
    """Base class for other exceptions"""
    pass


class UnknownURLTypeException(Error):
    """Raised when url type cannot be determined"""
    pass


class downThread(threading.Thread):
    """
    Basic threadpool setup where threads fetch download tasks from download_queue
    """
    __name: str

    def __init__(self, id: int) -> None:
        """
        Initializes thread with a thread name
        Param: 
           id: thread identifier
        """
        super(downThread, self).__init__()
        self.__name = "Thread #" + str(id)

    def run(self) -> None:
        """
        Worker thread job. Blocks until a task is avalable via downloadables
        and retreives the task from download_queue
        """
        while True:
            # Wait until download is available
            downloadables.acquire()

            # Check kill signal
            if kill:
                return

            # Pop queue and download it
            todo = download_queue.get()
            download_file(todo[0], todo[1], self.__name)
            download_queue.task_done()

            # Unzip file if specified
            if unzip and 'zip' in todo[0]:
                extract_zip(todo[1], todo[1].rsplit('/', 1)[0])
            time.sleep(TIME_BETWEEN_CHUNKS)


def extract_zip(zippath: str, destpath: str) -> None:
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
    except BadZipFile as e:
        logging.critical("Unzipping a non zip file has occured, please check if file has been downloaded properly")
        logging.critical("File name: " + zippath)
        logging.critical("File size: " +  str(os.stat(zippath).st_size))
        logging.critical(e)


def trim_fname(fname: str) -> str:
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


def download_file(src: str, fname: str, tname: str) -> None:
    """
    Downloads file at src. Skips duplicate files

    Param:
       src: src of image to download
       fname: what to name the file to download
       tname: thread name
    """
    
    scraper = cfscrape.create_scraper()

    # Get download size
    r = scraper.request('HEAD', src)
    fullsize = r.headers.get('Content-Length')
    downloaded = 0
    f = fname.split('/')[len(fname.split('/')) - 1]
    # Download file, skip duplicate files
    if not os.path.exists(fname) or os.stat(fname).st_size != int(fullsize): 
        done = False
        while(not done):
            try:
                # Download file to memory
                data = scraper.get(src, stream=True, headers={'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36', 'cookie':'__ddg1_=uckPSs0T21TEh1iAB4I5; _pk_id.1.5bc1=0767e09d7dfb4923.1652546737.; session=eyJfcGVybWFuZW50Ijp0cnVlLCJhY2NvdW50X2lkIjoxMTg1NTF9.Yn_ctw.BR10xbr1QVttkUyF2PEmolEkvDo; _pk_ref.1.5bc1=["","",1652718344,"https://www.google.com/"]; _pk_ses.1.5bc1=1'})

                # Download the file
                with open(fname, 'wb') as fd, tqdm(
                        desc=fname,
                        total=int(fullsize),
                        unit='iB',
                        unit_scale=True,
                        leave=False,
                        bar_format= tname + "->" + f + '[{bar}{r_bar}]',
                        unit_divisor=1024,) as bar:
                    for chunk in data.iter_content(chunk_size=chunksz):
                        sz = fd.write(chunk)
                        fd.flush()
                        bar.update(sz)
                        downloaded += sz
                    bar.clear()

                if(os.stat(fname).st_size == int(fullsize)):
                    done = True
            except requests.exceptions.ChunkedEncodingError:
                logging.warning(tname + ": Chunked encoding error has occured, server has likely disconnected, download has restarted")
                pass
            scraper.close()


def download_all_files(imgLinks: ResultSet, dir: str) -> None:
    """
    Puts all urls in imgLinks into download queue

    Param:
       imgLinks: all image links within a container
       dir: where to save the images
    """
    counter = 0
    for link in imgLinks:
        download = link.get('href')
        extension = (trim_fname(download).split('.'))
        download_queue.put((containerPrefix + download, dir +
                           str(counter) + "." + extension[len(extension) - 1]))
        downloadables.release()
        counter += 1


def process_container(url: str, root: str) -> None:
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
    if not os.path.isdir(titleDir):
        os.makedirs(titleDir)

    reqs.close()
    # Download image links
    download_all_files(imgLinks, titleDir)

    # Get post content
    content = soup.find("div", class_="post__content")

    if content:
        if(os.path.exists(titleDir + "post__content.txt")):
            pass
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
            download_queue.put((containerPrefix + download,
                               titleDir + trim_fname(download)))
            downloadables.release()


def process_window(url: str, continuous: bool) -> None:
    """
    Processes a single main artist window
    Param: 
       url: url of the main artist window
    """
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')
    reqs.close()
    # Create directory
    artist = soup.find("meta", attrs={'name': 'artist_name'})
    titleDir = folder + re.sub(r'[^\w\-_\. ]', '_',
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
            process_container(containerPrefix + content.get('href'), titleDir)

        if continuous:
            # Move to next window
            time.sleep(TIME_BETWEEN_CHUNKS)
            counter += 25
            reqs = requests.get(url + suffix + str(counter))
            soup = BeautifulSoup(reqs.text, 'html.parser')
            reqs.close()
            contLinks = soup.find_all("div", class_="post-card__link")
        else:
            contLinks = None


def call_and_interpret_url(url: str) -> None:
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
        process_window(url, False)
    elif "post" in url:
        # Build directory
        reqs = requests.get(url)
        if(reqs.status_code >= 400):
            logging.error("Status code " + str(reqs.status_code))
        soup = BeautifulSoup(reqs.text, 'html.parser')
        artist = soup.find("a", attrs={'class': 'post__user-name'})
        titleDir = folder + \
            re.sub(r'[^\w\-_\. ]', '_', artist.text.strip()) + "/"
        if not os.path.isdir(titleDir):
            os.makedirs(titleDir)
        reqs.close()

        # Process container
        process_container(url, titleDir)
    elif 'user' in url:
        process_window(url, True)
    else:
        raise UnknownURLTypeException


def create_threads(count: int) -> list:
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


def kill_threads(threads: list) -> None:
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


def routine(url: str) -> None:
    """
    Main routine, processes a main artist window using multithreading
    if url is None, ask for a url.
    Threads must be started and ended outside of routine and download queue
    may still contain items
    Param:
       url: url of main artist window or None
    """
    # Get url to download
    while url == None or "https://kemono.party" not in url:
        url = input("Input a url, or type 'quit' to exit> ")

        if(url == 'quit'):
            return

    # Interpret the url
    call_and_interpret_url(url)


def main() -> None:
    """
    Program runner
    """
    global folder
    global unzip
    global tcount
    global chunksz
    logging.basicConfig(level=logging.INFO)
    threads = None
    if len(sys.argv) > 1:
        pointer = 1
        while(len(sys.argv) > pointer):
            if sys.argv[pointer] == '-f' and len(sys.argv) >= pointer:
                threads = create_threads(tcount)
                with open(sys.argv[pointer + 1], "r") as fd:
                    for line in fd:
                        line = line.strip()
                        if len(line) > 0:
                            routine(line)
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
                logging.info("Switches: Can be combined but -f ,must be at the end if used")
                logging.info("No switch : Prompts user with download url")
                logging.info("-f <textfile.txt> : Download from text file containing links")
                logging.info("-d <path> : Set download path for single instance, must use '/'")
                logging.info("-v : Enables unzipping of files automatically")
                logging.info("-c <#> : Adjust download chunk size in bytes (Default is 64M)")
                logging.info("-h : Help")
                logging.info("-t <#> : Change download thread count (default is 6)")
                exit()


    if not threads:
        threads = create_threads(tcount)
        routine(None)

    download_queue.join()
    kill_threads(threads)


if __name__ == "__main__":
    main()
