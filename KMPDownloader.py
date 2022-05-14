from concurrent.futures import process
import requests
from bs4 import BeautifulSoup, ResultSet
import urllib.request
import os
import re

"""
Simple kemono.party downloader relying on html parsing and download by url
@author Jeff Che1
@version 0.1
@last modified 5/13/2022
"""

# Settings ###################################################
folder = r"C:/Users/chenj/Downloads/Fun2/samples/"
CHUNK_SIZE = 1024 * 1024 * 64
# URL specific variables <MODIFY AT YOUR RISK> ###############
dataPrefix = "https://data10.kemono.party"
containerPrefix = "https://kemono.party"
delimiter = "#"
##############################################################
def trim_fname(fname:str) -> str:
   """
   Trims fname, returns result. Extensions are kept
   """
   first = fname.split("?")
   second = first[0].split("/")
   return second[len(second) - 1]

def download_file(src:str, fname:str) -> None:
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
         print("Progress: " + str(downloaded) + " / " + str(fsize) + " (" + str(int((downloaded/fsize) * 100)) + "%)")
         chunk = resp.read(CHUNK_SIZE)

def download_all_files(imgLinks:ResultSet, dir:str)->None:
   counter = 0
   for link in imgLinks:
      download = link.get('href')
      extension = (download.split('.'))
      download_file(dataPrefix + download,  dir + str(counter) + "." + extension[len(extension) - 1])
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
            download_file(dataPrefix + download, titleDir + trim_fname(download))
   print("Wrote post contents to file")

def process_window(url:str)->None:
   reqs = requests.get(url)
   soup = BeautifulSoup(reqs.text, 'html.parser')

   # Create directory
   artist = soup.find("meta", attrs={'name': 'artist_name'})
   titleDir = folder + re.sub(r'[^\w\-_\. ]', '_', artist.get('content')) + "/"
   if not os.path.isdir(titleDir):
      os.mkdir(titleDir)

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
   # Get url to download
   url = input("Input a url> ")
   process_window(url)


if __name__ == "__main__":
    main()