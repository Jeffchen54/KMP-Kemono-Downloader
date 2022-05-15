# KMPDownloader
Simple Kemono.party downloader
Ran and built in Windows 10 with Visual Studios on Python 3.10
Functionality not guaranteed until 1.0, There are known bugs!

Instructions:
- Download all required dependencies
- Edit Settings near the top of KMPDownloader.py. folder is the only required setting
- Run in your favoriate command line software
- Enter in a url of an artist home page (Follows this format: https://kemono.party/fanbox/user/xxxxxxxx)
- Enjoy!

Known bugs:
- No DDOS guard countermeasures, leading to 404 errors (solution is to use a VPN for now and decreasing download rate)
- post_content.txt may contain garbage data at times

Changelog 0.2:
- Multithreading support

Changelog 0.1:
- Downloads image(s) from a post
- Orders downloads in numerical order shown on post
- Puts creates a post directory at selected download folder
- Visable progress when downloading
- Supports zip downloads
- Saves post text content
- Works with gifs
- Works with mp4s 
- Support downloading all sections from artist home page

Future features:
- User friendly upgrades
- GUI
- Command line argument support
- Automatic Gdrive and Mega download from links
- DDOS solution (headless selenium?)
