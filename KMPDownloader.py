from multiprocessing import Semaphore
import threading
import requests
from bs4 import BeautifulSoup, ResultSet
import urllib.request
import os
import re
import queue
from typing import TypeVar, Generic
import time

"""
Simple kemono.party downloader relying on html parsing and download by url
Using multithreading
@author Jeff Che1
@version 0.2
@last modified 5/13/2022
"""

# Settings ###################################################
folder = r"C:/Users/chenj/Downloads/KMPDownloader/content/"
CHUNK_SIZE = 1024 * 1024 * 64
THREADS = 6
# URL specific variables <MODIFY AT YOUR RISK> ###############
dataPrefix = "https://data10.kemono.party"
containerPrefix = "https://kemono.party"
delimiter = "#"
##############################################################
kill = False
download_queue = queue.Queue(-1)
downloadables = Semaphore(0)
T = TypeVar('T')
V = TypeVar('V')

class Error(Exception):
    """Base class for other exceptions"""
    pass

class MismatchTypeException(Error):
    """Raised when a comparison is made on 2 different types"""
    pass

class KVPair (Generic[T,V]):
    """
    Generic KVPair structure where:
        Key is generic V
        Value is generic T
        Tombstone is bool & optional
    Upon initiailization, data becomes read-only
    """
    __key: V
    __value: T
    __tombstone: bool

    def __init__(self, key: V, value: T) -> None:
        """
        Initializes KVPair. Tombstone is disabled by default.

        Param
            key: key (use to sort)
            value: value (data)

        """
        self.__value = value
        self.__key = key
        self.__tombstone = False

    def getKey(self) -> V:
        """
        Returns key
        Return: key
        """
        return self.__key

    def getValue(self) -> T:
        """
        Returns value
        Return: value
        """
        return self.__value

    def compareTo(self, other) -> int:
        """
        Compares self and other key value. Ignores generic typing

        Raise: MismatchTypeException if other is not a KVPair\n
        Return:
            self.getKey() > other.getKey() -> 1\n
            self.getKey() == other.getKey() -> 0\n
            self.getKey() < other.getKey() -> -1\n

        """
        if other == None or not isinstance(other, KVPair):
            raise MismatchTypeException("other is not of type KVPair(V,T)")

        if self.__key > other.getKey():
            return 1
        if self.__key == other.getKey():
            return 0
        return -1

    def __str__(self) -> str:
        """
        toString function which returns KVPair in json style formatting
        {key:<keyval>, value:<val>, Tomb:<val>}

        value relies on T's __str__ function

        Return: KVPair in json style format
        """
        return "{key:" + str(self.__key) + ", value:" + str(self.__value) + ", Tomb:" + ("T" if self.__tombstone else "F") + "}"

    def setTombstone(self) -> None:
        """
        Turns on tombstone
        """
        self.__tombstone = True

    def disableTombstone(self) -> None:
        """
        Turns off tombstone
        """
        self.__tombstone = False

    def isTombstone(self) -> bool:
        """
        Returns tombstone status

        Return true if set, false if disabled
        """
        return self.__tombstone

class downThread(threading.Thread):
   __name:str
   def __init__(self, id:int):
      super(downThread, self).__init__()
      self.__name = "Thread #" + str(id)

   def run(self):
      while True:
         # Wait until download is available
         downloadables.acquire()

         # Check kill signal
         if kill:
            print(self.__name + " has finished")
            return
         
         # Pop queue and download it
         todo:KVPair[str,str] = download_queue.get()
         download_file(todo.getKey(), todo.getValue(), self.__name)
         download_queue.task_done()
   


def trim_fname(fname:str) -> str:
   """
   Trims fname, returns result. Extensions are kept
   """
   first = fname.split("?")
   second = first[0].split("/")
   return second[len(second) - 1]

def download_file(src:str, fname:str, tname:str) -> None:
   """
   Downloads file at src
   """
   print("Downloading ", src)
   resp = urllib.request.urlopen(src) 
   fsize = int(resp.headers.get('Content-Length').strip())
   downloaded = 0
   chunk = resp.read(CHUNK_SIZE)
   with open(fname, 'wb') as fd:
      while chunk:
         downloaded += len(chunk)
         fd.write(chunk)
         print(tname + " Progress: " + str(downloaded) + " / " + str(fsize) + " (" + str(int((downloaded/fsize) * 100)) + "%)")
         chunk = resp.read(CHUNK_SIZE)

def download_all_files(imgLinks:ResultSet, dir:str)->None:
   """
   Puts all urls in imgLinks into download queue
   """
   counter = 0
   for link in imgLinks:
      download = link.get('href')
      extension = (download.split('.'))
      download_queue.put(KVPair[str,str](dataPrefix + download, dir + str(counter) + "." + extension[len(extension) - 1]))
      downloadables.release()
      counter += 1

def process_container(url:str, root:str)->None:
   # Get HTML request and parse the HTML for image links and title
   reqs = requests.get(url)
   soup = BeautifulSoup(reqs.text, 'html.parser')
   imgLinks = soup.find_all("a", class_="fileThumb")
   titleDir = root + re.sub(r'[^\w\-_\. ]', '_', soup.find("title").contents[0].strip()) + "/"
   if not os.path.isdir(titleDir):
      os.mkdir(titleDir)

   # Download image links
   download_all_files(imgLinks, titleDir)

   # Get post content
   content = soup.find("div", class_="post__content")
   if content:
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
            download_queue.put(KVPair[str,str](dataPrefix + download, titleDir + trim_fname(download)))
            downloadables.release()
   print("Wrote post contents to file")

def process_window(url:str)->None:
   reqs = requests.get(url)
   soup = BeautifulSoup(reqs.text, 'html.parser')

   # Create directory
   artist = soup.find("meta", attrs={'name': 'artist_name'})
   titleDir = folder + re.sub(r'[^\w\-_\. ]', '_', artist.get('content')) + "/"
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
      
      # Move to next window
      counter += 25
      reqs = requests.get(url + suffix + str(counter))
      soup = BeautifulSoup(reqs.text, 'html.parser')
      contLinks = soup.find_all("div", class_="post-card__link")

   print("Download completed")

def main():
   threads = []
   # Spawn threads 
   for i in range (0, THREADS):
      threads.append(downThread(i))
      threads[i].start()

   # Get url to download
   url = input("Input a url> ")
   process_window(url)

   # Wait until queue is empty
   download_queue.join()

   global kill
   kill = True
   
   for i in range (0, THREADS):
      downloadables.release()

   for i in threads:
      i.join()

if __name__ == "__main__":
    main()