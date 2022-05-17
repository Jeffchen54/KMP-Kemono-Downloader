# KMPDownloader
Simple Kemono.party downloader
Ran and built in Windows 10 with Visual Studios on Python 3.10
Functionality not guaranteed until 1.0, There are known bugs!

![Screenshot 2022-05-17 114434 PNG](https://user-images.githubusercontent.com/78765964/168853513-b5b14b98-430f-4437-b63b-08ea93ddf014.jpg)

## Instructions:
- Download all required dependencies
- Edit Settings near the top of KMPDownloader.py. folder is the only required setting
- Run in your favorite command line software
- Enter in a url of an artist home page (Follows this format: https://kemono.party/fanbox/user/xxxxxxxx)
- Enjoy!

## Command line arguments:
KMPDownloader.py -f <.txt> : Bulk downloads all links in .txt file, must be last switch used if used

KMPDownloader.py -d <path> : Sets download path for a single download instance, must use /
  
  KMPDownloader.py -v : Enables unzipping of files automatically
  
  KMPDownloader.py -c <#> : Adjust download chunk size in bytes (Default is 64M)
  
  KMPDownloader.py -t <#> : Change download thread count (default is 6)
 
KMPDownloader.py -h : Help
  
KMPDownloader.py : Prompts user to enter a url

## Bulk file
  An example bulk file has been included "examples.txt"
  
  You can run using: KMPDownloader.py -d C:/Users/chenj/Downloads/KMPDownloader/ -f C:/Users/chenj/Downloads/KMPDownloader/example.txt
  
  Replace the path to file before running. Bulk file downloads safe content only. Check KMPDownloader folder after download is completed. 
  
## Supported URL formats:

https://kemono.party/service/user/xxxxxx: Downloads all artist works
  
https://kemono.party/service/user/xxxxxx?o=25: Downloads all artist works on that specific page
  
https://kemono.party/service/user/xxxxxx/post/xxx: Downloads specific artist work

## Download information:
- There is currently no way to change download options without changing the code directly
- All files will be downloaded in dynamically generated paths from a given download path

### Example
1) User wants to download https://kemono.party/service/user/xxxxxx/post/xxx in path C:/user/contents/
2) System derives data from link (artist name, post name, post content, downloads, and files)
3) Downloads to C:/user/contents/artist/postname/
- Post content saved to post_content.txt
- downloads saved using default name
- Files downloaded with a counter 0..n where 0 is the first file on the page and n is the last file on the page

## Known bugs:
- post_content.txt may contain garbage data at times

## Possible bugs:
These bugs were accounted for but not enough testing has been conducted
  
None
  
 
 ## Changelog 0.3.4
  - Various bug fixes
  - Fix issue where multiple posts exists sharing the same name, causing infinite download loop
  - Improved dialouge
  
 ## Changelog 0.3.3
  - Added a more robust fix to file not being downloaded fully bug
  - Skip duplicate file based on file name and size
  - Removed time between download chunks due to pdf requests chunks being limited to <8KBs in some instances
  
 ## Changelog 0.3.2
- Vastly improve graphical aspect and progress bar
- Added many more command line switches
- Fixed incomplete download issues
  
 ## Changelog 0.3.1
  - Fixed bug where certain downloads crashed threads when they do not have Contain-Length header
  - Returned chunked download to save memory and progress indicator
  - Add setting to automatically unzip files if they are not password protected
  
## Changelog 0.3:
- Bulk download support of urls for all artist work, single page of artist work, or a single artist work
- Multithreading optimization where all urls in bulk download file can be loaded up into a queue instead of having to wait for a url to finish downloading
- Several robust upgrades
- Slight memory optimization
- Fixed bug where certain files names were not being trimmed properly
- Switch to cfscrape library instead of requests for Kemono's ddos protection
- Removed chunk download support and visable download process temporarily, download process can be monitored in task manager perforance tab in network section
- Disposal of most invalid urls and option to quit ran with no input url
- Removed duplicate file check temporarily
- Added command line switches -f and -d
- Fixed bug where downloading large files would timeout before they were completed.

## Changelog 0.2:
- Multithreading support

## Changelog 0.1:
- Downloads image(s) from a post
- Orders downloads in numerical order shown on post
- Puts creates a post directory at selected download folder
- Visable progress when downloading
- Supports zip downloads
- Saves post text content
- Works with gifs
- Works with mp4s 
- Support downloading all sections from artist home page

## Future features:
- User friendly upgrades
- GUI
- Command line argument support for more settings
- Automatic Gdrive and Mega download from links <unlikely>
