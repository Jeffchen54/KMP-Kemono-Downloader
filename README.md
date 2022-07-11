# KMPDownloader
Simple Kemono.party downloader
Ran and built in Windows 10 with Visual Studios on Python 3.10
Functionality not guaranteed until 1.0, There are known bugs!
Can download everything from Files, save text and links in Content, and everything in Downloads. Can be set to automatically unzip files if they contain no password.

*For version 0.4 and onward, downloaded files names will be different. Files from 0.3.5 and prior will be considered different files
and will not be skipped on duplication checks.

![Screenshot 2022-05-17 114434 PNG](https://user-images.githubusercontent.com/78765964/168853513-b5b14b98-430f-4437-b63b-08ea93ddf014.jpg)

## Current Features
View changelog for more details on features not included here.
- All services supported (Patreon, Pixiv Fanbox, Gumroad, SubscribeStar, DLSite, Fantia, Discord).
- Can download a single artist work, all artist works, or a single page of artist works.
- Download all files and any downloads in high resolution and correct extension.
- Automatic file unzipping for .7z, .zip, and .rar files. 
- Extraction of a work's content and comments*.
- Queuing system, download multiple URLs without user input
- Multhreading support, significant download speed bonus.

*Extraction is content is limited to text only. Hyperlinks will have their target url extracted for post content.

## Instructions:
**Need in depth details? Go to the latest release and read the powerpoint there!**

- Download all required dependencies

    pip install requests
    
    pip install bs4
    
    pip install cfscrape 
    
    pip install tqdm
    
    pip install patool
- Install 7z and add it to your Window's Path. Line should be in the format "C:\Users\chenj\Downloads\7-Zip"
- Copy and paste the files in patch for patoolib into your patoolib library. You can also grab the patched files from https://github.com/wummel/patool/pull/83/commits/c5282e30e1b3448081d74a0b8a86c7c9ecaaebbf. On my computer, the directory
is "C:\Users\chenj\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\patoolib\programs".
The directory to paste the files will contain files with the same name as what has been provided in the patch folder. This patches the issue where
the program will hang when prompted with a password. You do not need to follow this step if you are not going to set automatic
file unzipping or are not going to unzip password protected zip files.
- Run in your favorite command line software
- Read the command line arguments for instructions on how to run.
- Enjoy!

## Command line arguments:
-f <textfile.txt> : Download from text file containing links

-d <path> : REQUIRED - Set download path for single instance, must use '\'
    
-c <#> : Adjust download chunk size in bytes (Default is 64M)
    
-x "txt, zip, ..., png" : Exclude files with listed extensions, NO '.'s
    
-s : If a artist work is text only, do not create a dedicated directory for it, partially unpacks files
    
-t <#> : Change download thread count (default is 6)
    
-u : Enable unpacked file organization, all works will not have their own folder, overrides partial unpack

-r <#> : Maximum number of retries for HTTP 429 error, default is infinite
    
-h : Help

 Default file organization is packed, all works will have their own folder within an artist folder.
    
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

## Troubleshooting
  ### Password protected directory:
    atool: ... cmdlist_func = <function extract_7z at 0x000001DB5A894700> 
    patool: ... kwargs={'password': None} args=('C:/Users/chenj/Downloads/KMPDownloader/pass_2.7z', None, 'C:\\7-Zip\\7z.EXE', -1, False,       'C:\\Users\\chenj\\Downloads\\KMPDownloader')
    ERROR: Data Error in encrypted file. Wrong password? : pass.7z
  
  Zip is password protected. The file will be skipped and will have to be manually extracted.
  Note that the top 2 lines are normal, only the 'ERROR' line needs attention.
  ***Hint - look at post_comments.txt or post_content.txt to see if the password is there 
 
  ### Path too long:
    ERROR: Can not open output file : The system cannot find the path specified. : c:/Users/chenj/Downloads/KMPDownloader/Northlandscapes Photography/FREE Astro  Night Sky Photography Lightroom Presets Pay-What-You-Want by Northlandscapes Photography from Gumroad  Kemono/Lightroom 4-6 and Classic CC before Apr 2018 (.lrtemplate)\Northlandscapes - Astrophotography\Virgo.lrtemplate
  
   Extract file length is too long and zip file could not be extracted. Extraction is done on your computer's temp directory. More information about temp
  directory can be found here: http://sales.commence.com/commencekb/Article.aspx?id=10068. Adjust the temp path directory to be shorter or you can extract
  the file manually.
  
  ### File does not exists:
    CRITICAL:root:(404)Link provided cannot be downloaded from, possibly a dead third party link: https://kemono.party/attachments/discord/634594002624184360/634659046678593536/772072375331717131/-10.png
    
File could not be downloaded due to HTML error. Can be caused by many cases. In this example, the file provided by Kemono's API does not exists and was probably deleted.
  
 ### Corrupted Japanese Zip Contents:
 Files look like this?
 
 ![image](https://user-images.githubusercontent.com/78765964/175039979-1dc7b2b9-ac4b-461e-b0dc-587ada9bb473.png)
    
 Follow instructions in the video here -> https://www.youtube.com/watch?v=bo52rBmTiT8
 ### Specific Discord Issues:
- Root directory of downloaded discord files are all numbers, cannot be fixed easily since the home page of a discord artist does not contain their name. Number is associated with the the Xs in https://kemono.party/discord/server/xxxxxxxxxxxxxxxx.
    
    
## Known bugs:
- post_content.txt may contain garbage data at times

## Possible bugs:
These bugs were accounted for but not enough testing has been conducted
  
None

## Changelog 0.5.3:
- Pre existing download folder check
- Better logging filename reflecting human readable UTC time
- Fixed issues where zip file check checked more than the extension
- Post file check for partial unpack
- Set HTTP codes to retry
- Extracted files now saved to their own file (similar to extract file option in 7z), prevents certain file overwrite situations
- Extracted dupe file handling made much more robust
- Now deletes empty extracted folder if an error occured while extracting a zip
- post name based exclusion
- Link exclusion
- maintain server fname switch
- Organized switches and made logging prefix more useful

## Changelog 0.5.2:
- HTML 429 retry and config timeout
- Improved error messages
- Error logging    
 
 ## Changelog 0.5.1:
- Vastly improved code organization
- Fixed possible bug where file download count not accurate if file was not downloaded entirely
- Added unpacked download mode, each work will not be placed in their own folder and will instead
    be placed in a main folder
- Now downloads Discord content in the correct order!!!!!
- Fixed an uncommon bug where an exception could occur due to extracting files of same name by chance
- Fixed issues where an undefined char in a filename results in an nonexistant directory being accessed.
- Removed inconsistency where / is used instead of \\ in file paths
- Removed shared resource leak between KMP instances
- File extension exclusion
- Contentless file switch
 
    
 ## Changelog 0.5
- Significantly improved cases where multiple zip files unzip to the exact same destination, creates second directory instead of
overwritting existing files
- Fix file_text.txt issue where random numbers are scraped up
- Emoji support added
- Fixed case where post__content.txt was created even though work does not contain any post content
- No longer downloads patreon url file links in downloads segment
- Adjust numbering algorithm to prevent overwriting, note that bad img links will not be downloaded, leaving gaps in the naming
- Fixed bug where post comments not downloaded if downloading of images occurred
- Limited discord functionality added, downloads every image, and all text. Hyperlinks are recorded as well
    
 ## Changelog 0.4.2
  - Added connectivity protocol where program will attempt to reconnect forever until a connection is made
    
 ## Changelog 0.4.1 
  - Images in Content section downloaded
  - Fixed extremely rare bug where human readable download file name is corrupted on server so hashed file name will be scraped instead
  - Links and text in file segment now saved to file__text.txt
  - Patch cases where Fanbox works have polluted links which cause errors if download is attempted on them
  - Patch case where an artist work has multiple zip files containing the same directory
  - Fixed bug where file name was not being trimmed enough
    
 ## Changelog 0.4
  - Post comments are now downloadable
  - Reports program running time
  - Pre emptive server disconnect is fixed 
  - Fixed issue where non zip files was unzipped.
  - Downloads the human readable filename displayed on Kemono itself for attachments instead of the scrambled text
  - Fixed issue where certain file types were downloaded as .bin instead of the correct extension
  - Expanded automatic unzipping to .zip, .7z, and .rar.
  - Replaced illegal file characters with "" instead of "_"
  - Japanese and other unusual file names now show proper names instead of corrupted characters
  - Fixed issue where post content was generated when no text is present
  - Supports Linux style file paths containing './' and '../'
  
 ## Changelog 0.3.5
  - Some edits made to be compatible with Windows
  - Program configured to be runnable using command line arguments only
  - Now outputs total downloaded files
  - Slight boost to url scraping speed
  
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
- Automatic Gdrive and Mega download from links (Unlikely)
