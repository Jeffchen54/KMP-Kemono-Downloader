from multiprocessing import Semaphore
import threading
from urllib.error import HTTPError, URLError
import requests
from bs4 import BeautifulSoup, ResultSet
import os
import re
import queue
import time
import sys
import cfscrape

"""
Simple kemono.party downloader relying on html parsing and download by url
Using multithreading

- Bulk download with file containing all artist main window links
- Robustness upgrades
- Slight memory optimization
- Fixed bug where file names were not being isolated properly
- Switch to cfscrape library to mitigate cloudflare issues
@author Jeff Chen
@version 0.3
@last modified 5/14/2022
"""

# Settings ###################################################
folder = r"D:/User Files/Personal/Cloud Drive/MEGAsync/Nonsensitive/Best/Package/Pixiv/~unsorted/"
CHUNK_SIZE = 1024 * 1024 * 64 # Chunk size of downloads
TIME_BETWEEN_CHUNKS = 2  # Required to not mimic a DDOS attack, DDOS guard may be triggered if you download too many files too quickly
THREADS = 6                # Number of threads
# URL specific variables <MODIFY AT YOUR RISK> ###############
containerPrefix = "https://kemono.party"
##############################################################
kill = False                     # Thread kill switch
download_queue = queue.Queue(-1) # Download task queue
downloadables = Semaphore(0)     # Avalible downloadable resource device

class downThread(threading.Thread):
   """
   Basic threadpool setup where threads fetch download tasks from download_queue
   """
   __name:str
   def __init__(self, id:int):
      """
      Initializes thread with a thread name
      Param: 
         id: thread identifier
      """
      super(downThread, self).__init__()
      self.__name = "Thread #" + str(id)

   def run(self)->None:
      """
      Worker thread job. Blocks until a task is avalable via downloadables
      and retreives the task from download_queue
      """
      while True:
         # Wait until download is available
         print(self.__name + " is ready")
         downloadables.acquire()

         # Check kill signal
         if kill:
            print(self.__name + " has finished")
            return
         
         # Pop queue and download it
         todo = download_queue.get()
         download_file(todo[0], todo[1], self.__name)
         download_queue.task_done()
         time.sleep(TIME_BETWEEN_CHUNKS)
   


def trim_fname(fname:str) -> str:
   """
   Trims fname, returns result. Extensions are kept:
   For example
   "/data/2f/33/2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.txt?f=File.txt"
   -> 2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.txt \n
   Param: 
      fname: file name
   Pre: fname follows above convention
   Return: trimmed filename with extension
   """

   first = fname.split("?")[0].split("?")
   second = first[0].split("/")
   return second[len(second) - 1]

def download_file(src:str, fname:str, tname:str) -> None:
   """
   Downloads file at src. Skips duplicate files
   Param:
      src: src of image to download
      fname: what to name the file to download
      tname: thread name
   """

   try:
      scraper = cfscrape.create_scraper()
      data = scraper.get(src).content
   except (URLError, HTTPError) as e:
      print(tname + ": Download incomplete, trying again for " + src)
      print(e.info)
      exit()
   print(tname + " downloading " + src)
   with open(fname, 'wb') as fd:
      fd.write(data)
   print(tname + " download complete")

def download_all_files(imgLinks:ResultSet, dir:str)->None:
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
      download_queue.put((containerPrefix + download, dir + str(counter) + "." + extension[len(extension) - 1]))
      downloadables.release()
      counter += 1

def process_container(url:str, root:str)->None:
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
      print("500 Server error encountered at " + url + ", retrying...")
      time.sleep(TIME_BETWEEN_CHUNKS)
      reqs = requests.get(url)
      soup = BeautifulSoup(reqs.text, 'html.parser')
   imgLinks = soup.find_all("a", class_="fileThumb")
   titleDir = root + (re.sub(r'[^\w\-_\. ]', '_', soup.find("title").contents[0]).strip()).split("/")[0] + "/"
   if not os.path.isdir(titleDir):
      os.mkdir(titleDir)   # 500 internal system error

   # Download image links
   download_all_files(imgLinks, titleDir)

   # Get post content
   content = soup.find("div", class_="post__content")
   
   if content:
      if(os.path.exists(titleDir + "post__content.txt")):
         print("Skipping duplicate post content")
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
            download_queue.put((containerPrefix + download, titleDir + trim_fname(download)))
            downloadables.release()

def process_window(url:str)->None:
   """
   Processes a single main artist window
   Param: 
      url: url of the main artist window
   """
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
      time.sleep(TIME_BETWEEN_CHUNKS)
      counter += 25
      reqs = requests.get(url + suffix + str(counter))
      soup = BeautifulSoup(reqs.text, 'html.parser')
      contLinks = soup.find_all("div", class_="post-card__link")


def routine(url:str)->None:
   """
   Main routine, processes a main artist window using multithreading
   if url is None, ask for a url
   Param:
      url: url of main artist window or None
   """
   # Get url to download
   if url == None:
      url = input("Input a url> ")

   threads = []
   # Spawn threads 
   for i in range (0, THREADS):
      threads.append(downThread(i))
      threads[i].start()

   process_window(url)

   # Wait until queue is empty
   download_queue.join()

   global kill
   kill = True
   
   for i in range (0, THREADS):
      downloadables.release()
   print("Killing threads")
   for i in threads:
      i.join()
   
   kill = False

def main()->None:
   """
   Program runner
   """
   if len(sys.argv) > 1 and sys.argv[1] == "-f":
      with open(sys.argv[2], "r") as fd:
         url = fd.readline().strip()
         while(len(url) > 0):
            routine(url)
            url = fd.readline().strip()
   else:
      routine(None)

if __name__ == "__main__":
    main()