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

- Returned chunked download to save memory and progress indicator
@author Jeff Chen
@version 0.3.1
@last modified 5/14/2022
"""

# Settings ###################################################
folder = r"D:/User Files/Personal/Cloud Drive/MEGAsync/Nonsensitive/Best/Package/Pixiv/~unsorted/"
CHUNK_SIZE = 1024 * 1024 * 64 # Higher chunk size gives speed bonus at high memory cost
TIME_BETWEEN_CHUNKS = 2  # Time between Internet activities
THREADS = 6                # Number of threads, note that download size is bottleneck by numerous factors
                           # More threads boost speed of downlaoding many small files but will not if
                           # downloading a single large file caps download limit
                           # Larger files may timeout, resulting in incomplete upgrades, if this occurs, decrease 
                           # the number of threads or decrease the number of downloads
# URL specific variables <MODIFY AT YOUR RISK> ###############
containerPrefix = "https://kemono.party"
# DO NOT EDIT ################################################
kill = False                     # Thread kill switch
download_queue = queue.Queue(-1) # Download task queue
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
         downloadables.acquire()

         # Check kill signal
         if kill:
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
   -> 2f33425e67b99de681eb7638ef2c7ca133d7377641cff1c14ba4c4f133b9f4d6.txt 

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

      # Get download size
      r = scraper.request('HEAD', src)
      fullsize = r.headers.get('Content-Length')

      # Download file to memory
      print(tname + " downloading " + src, flush=True)
      data = scraper.get(src, stream=True)

      # Loop until download size matches real size
      print(tname + ": Downloaded -> Real: " + fullsize + " Actual: " + data.headers.get('Content-Length'), flush=True)
      while(data.headers.get('Content-Length') != fullsize):
         print("Restarting download", flush=True)
         data = scraper.get(src)

      # Download the file
      downloaded = 0
      with open(fname, 'wb') as fd:
         for chunk in data.iter_content(chunk_size=CHUNK_SIZE):
            downloaded += len(chunk)
            fd.write(chunk)
            fd.flush()
            print(tname + ": Downloaded " + str(downloaded) + " / " + fullsize + " (" + str(int((downloaded/int(fullsize) * 100))) + "%)", flush=True)  
      print(tname + " download complete", flush=True)
      scraper.close()

   except (URLError, HTTPError) as e:
      print(tname + ": Download could not be completed for " + src, flush=True)
      exit()

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
      print("500 Server error encountered at " + url + ", retrying...", flush=True)
      time.sleep(TIME_BETWEEN_CHUNKS)
      reqs = requests.get(url)
      soup = BeautifulSoup(reqs.text, 'html.parser')
   imgLinks = soup.find_all("a", class_="fileThumb")
   titleDir = root + (re.sub(r'[^\w\-_\. ]', '_', soup.find("title").text.strip())).split("/")[0] + "/"
   if not os.path.isdir(titleDir):
      os.makedirs(titleDir) 

   reqs.close()
   # Download image links
   download_all_files(imgLinks, titleDir)

   # Get post content
   content = soup.find("div", class_="post__content")
   
   if content:
      if(os.path.exists(titleDir + "post__content.txt")):
         print("Skipping duplicate post content", flush=True)
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

def process_window(url:str, continuous:bool)->None:
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


def call_and_interpret_url(url:str)->None:
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
      if(reqs.status_code  >= 400):
         print("Status code " + str(reqs.status_code), flush=True)
      soup = BeautifulSoup(reqs.text, 'html.parser')
      artist = soup.find("a", attrs={'class': 'post__user-name'})
      titleDir = folder + re.sub(r'[^\w\-_\. ]', '_', artist.text.strip()) + "/"
      if not os.path.isdir(titleDir):
         os.makedirs(titleDir)
      reqs.close()

      # Process container
      process_container(url, titleDir)
   elif 'user' in url:
      process_window(url, True)
   else:
      raise UnknownURLTypeException

def create_threads(count:int)->list:
   """
   Creates count number of downThreads

   Param:
      count: how many threads to create
   """
   print("Creating threads", flush=True)
   threads = []
   # Spawn threads 
   for i in range (0, count):
      threads.append(downThread(i))
      threads[i].start()
   return threads

def kill_threads(threads:list)->None:
   """
   Kills all threads in threads

   Param:
      threads: threads to kill
   """
   global kill
   kill = True
   
   for i in range (0, len(threads)):
      downloadables.release()

   print("Killing threads", flush=True)
   for i in threads:
      i.join()
   
   kill = False

def routine(url:str)->None:
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


def main()->None:
   """
   Program runner
   """
   global folder
   threads = None
   if len(sys.argv) > 1:
      pointer = 1
      while(len(sys.argv) > pointer):
         if sys.argv[pointer] == '-f' and len(sys.argv) >= pointer:
            threads = create_threads(THREADS)
            with open(sys.argv[pointer + 1], "r") as fd:
               for line in fd:
                  line = line.strip()
                  if len(line) > 0:
                     routine(line)
            pointer += 2
         elif sys.argv[pointer] == '-d' and len(sys.argv) >= pointer:
            folder = sys.argv[pointer + 1]
            pointer += 2
         else:
            print("Switches")
            print("No switch : Prompts user with download url")
            print("-f <textfile.txt> : Download from text file containing links")
            print("-d <path> : Set download path for single instance, must use '/'")
            print("-d <path> -f <textfile.txt> : Combine -d and -f")
            print("-h : Help")
            exit()
         
      if not threads:
         threads = create_threads(THREADS)
         routine(None)
      
         
   else:
      threads = create_threads(THREADS)
      routine(None)

   download_queue.join()
   kill_threads(threads)
if __name__ == "__main__":
    main()