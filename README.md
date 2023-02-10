# KMPDownloader
Simple Kemono.party downloader

Ran and built in Windows 10 with Visual Studios on Python 3.10 and 3.11
Functionality not guaranteed until 1.0, There are known bugs!
Can download everything from Files, save text and links in Content, and everything in Downloads. Can be set to automatically unzip files if they contain no password.

![Screenshot 2022-05-17 114434 PNG](https://user-images.githubusercontent.com/78765964/168853513-b5b14b98-430f-4437-b63b-08ea93ddf014.jpg)

## Current Features
View changelog for more details on features not included here.
- All services supported (Patreon, Pixiv Fanbox, Gumroad, SubscribeStar, DLSite, Fantia, Discord).
- Can download a single artist work, all artist works, or a single page of artist works.
- Download all files and any downloads in high resolution and correct extension.
- Automatic file unzipping for .7z, .zip, and .rar files. 
- Extraction of a work's content and comments.
- High degree of control over downloads. Includes blacklisting file extensions, posts with certain keywords, omittion of certain download items, and much more!
- Queuing system, download multiple URLs without user input
- Multhreading support, significant download speed bonus.
- Ease of use, cookies are for eating only!  
- Automatically artist work updates**.

**New feature which is still in development

## Instructions:
**Need in depth details? Please visit the [wiki](https://github.com/Jeffchen54/KMP-Kemono-Downloader/wiki)!**

Download Python >=3.10

- Download all required dependencies

    pip install requests
    
    pip install bs4
    
    pip install cfscrape 
    
    pip install tqdm
    
    pip install patool

    pip install alive_progress

- Install 7z and add it to your Window's Path. Line should be in the format "C:\Users\chenj\Downloads\7-Zip"
- Copy and paste the files in patch for patoolib into your patoolib library. You can also grab the patched files from https://github.com/wummel/patool/pull/83/commits/c5282e30e1b3448081d74a0b8a86c7c9ecaaebbf. On my computer, the directory
is "C:\Users\chenj\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\patoolib\programs".
The directory to paste the files will contain files with the same name as what has been provided in the patch folder. This patches the issue where
the program will hang when prompted with a password. You do not need to follow this step if you are not going to set automatic
file unzipping or are not going to unzip password protected zip files.
- Run in your favorite command line software
- Read the command line arguments for instructions on how to run.
- Enjoy!
