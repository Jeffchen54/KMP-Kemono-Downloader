from tkinter import N
import unittest
from KMPDownloader import KMP
import dirs
import os
import shutil
from KMPDownloader import DeadThreadPoolException
import logging
"""
Tests KMPDownloader.py, tests utilize safe works only

Author: Jeff Chen
Last modified: 6/5/2022
"""


# Constants
TESTING_PATH = dirs.replace_dots_to_py_path("./temp/")

class KMPTestCase(unittest.TestCase):

    def setUp(self) -> None:
        """
        Sets up an Null KMP since tests require different paramaters
        """
        logging.basicConfig(level=logging.DEBUG)
        self.KMP = None
    
    @classmethod
    def setUpClass(cls):
        """
        Create temporary testing directory
        """
        # If directory already exists, delete it
        if os.path.exists(TESTING_PATH):
            shutil.rmtree(TESTING_PATH, ignore_errors=True)

        # Create a new temp directory
        os.mkdir(TESTING_PATH)

    def test_start_kill_threads(self) -> None:
        """
        Tests the starting and killing of threads
        """
        self.KMP = KMP(TESTING_PATH, False, tcount=None, chunksz=None)

        # Single thread
        self.KMP._KMP__threads = self.KMP._KMP__create_threads(1)
        self.KMP._KMP__kill_threads(self.KMP._KMP__threads)
        self.assertRaises(DeadThreadPoolException, self.KMP._KMP__call_and_interpret_url, "https://kemono.party/gumroad/user/9222612694494/post/AizNy")

        # 3 Threads
        self.KMP._KMP__threads = self.KMP._KMP__create_threads(3)
        self.KMP._KMP__kill_threads(self.KMP._KMP__threads)
        self.assertRaises(DeadThreadPoolException, self.KMP._KMP__call_and_interpret_url, "https://kemono.party/gumroad/user/9222612694494/post/AizNy")

    def test_trim_fname(self) -> None:
        """
        Tests __trim_fname
        """
        self.KMP = KMP(TESTING_PATH, False, tcount=None, chunksz=None)
        # <a class="post__attachment-link" href="/data/ac/95/ac95d0d22d3bf2b76e66305ba8b45e573d08980419f7aca786e11945f53342c4.zip?f=%E3%81%BE%E3%81%A8%E3%82%81DL%E7%94%A8.zip">
        #    Download まとめDL用.zip
        #  </a>
        self.assertEqual(self.KMP._KMP__trim_fname("Download まとめDL用.zip"), "まとめDL用.zip")
      
    def test_download_static_files(self) -> None:
        """
        Tests downloading files under different circumstances
        """
        
        # Single thread no image
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/33271853/post/36694748")


        # 3 Thread no image
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=3, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/33271853/post/47946953")

        # Single Thread, 2 image
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/33271853/post/36001529")

        # 3 Threads, 2 image
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=3, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/33271853/post/47255266")

        # 1 Thread, multi images
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/33271853/post/65647736")

        # 16 Thread multi images
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=16, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/33271853/post/52792630")

        # Verify content:
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/0.png").st_size, 3692609)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/1.png").st_size, 3692609)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/2.png").st_size, 2752125)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/3.png").st_size, 3262789)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/4.png").st_size, 2392221)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/5.png").st_size, 2349839)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/6.png").st_size, 5652120)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/7.png").st_size, 1825005)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/8.png").st_size, 3002485)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/9.png").st_size, 4467542)

        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/0.png").st_size, 13444381)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/1.png").st_size, 13444381)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/2.png").st_size, 13854733)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/3.png").st_size, 13702259)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/4.png").st_size, 13802523)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/5.png").st_size, 13040955)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/6.png").st_size, 13911132)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/7.png").st_size, 13524999)
        self.assertEqual(os.stat(TESTING_PATH + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/8.png").st_size, 12743876)

    def test_download_static_attachments(self) -> None:
        """
        Tests downloading static attachments
        """
        # Single .pdf
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/gumroad/user/5563321775917/post/wSIJ")
        

        # Single .cvf
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/gumroad/user/5563321775917/post/mRSH")

        self.assertEqual(os.stat(TESTING_PATH + "Gumroad Help Center/New Creator FAQ - All the Basics in One Place by Gumroad Help Center from Gumroad  Kemono/Creatorpedia.pdf").st_size, 14704)
        self.assertEqual(os.stat(TESTING_PATH + "Gumroad Help Center/An Example CSV of Exported Sales Data by Gumroad Help Center from Gumroad  Kemono/Sales_CSV_Example.csv").st_size, 2933)
    
    
    def test_download_animated_attachments(self) -> None:
        """
        Tests downloaded animated gif files
        """
        # 2 Threads, 2 gifs
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=2, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/523894/post/66527944")


        # Single .mp4 
        self.KMP.routine("https://kemono.party/gumroad/user/5563321775917/post/jnBuO")

        # .mov 
        self.KMP.routine("https://kemono.party/gumroad/user/8844596389936/post/WBlK")

        self.assertEqual(os.stat(TESTING_PATH + "Jasonafex/New Playable Build 0.6.6 by Jasonafex from Patreon  Kemono/1.gif").st_size, 1930242)
        self.assertEqual(os.stat(TESTING_PATH + "Jasonafex/New Playable Build 0.6.6 by Jasonafex from Patreon  Kemono/0.gif").st_size, 1930242)
        self.assertEqual(os.stat(TESTING_PATH + "Gumroad Help Center/Creating a Product - A Streaming Video Experience by Gumroad Help Center from Gumroad  Kemono/Product_Creation_-_Export_1015.mp4").st_size, 58934883)
        self.assertEqual(os.stat(TESTING_PATH + "Katon Callaway/Topology Tips  by Katon Callaway from Gumroad  Kemono/topoJoints.mov").st_size, 448251813)

        
    def test_download_audio_attachments(self) -> None:
        """
        Tests downloading audio files
        """
        # 3 mp3
        self.KMP = KMP(TESTING_PATH, unzip=False, tcount=3, chunksz=None)
        self.KMP.routine("https://kemono.party/gumroad/user/5563321775917/post/moNG")

        # .sf2, .wav
        self.KMP.routine("https://kemono.party/gumroad/user/3915675902935/post/NTJQZ")

        self.assertEqual(os.stat(TESTING_PATH + "Truebones Motions Animation Studios/FREE STAR TREK SOUND FX INCLUDES SOUND FONT and .WAV file formats. by Truebones Motions Animation Studios from Gumroad  Kemono/HS_StarTrekFX.sf2").st_size, 807090)
        self.assertEqual(os.stat(TESTING_PATH + "Truebones Motions Animation Studios/FREE STAR TREK SOUND FX INCLUDES SOUND FONT and .WAV file formats. by Truebones Motions Animation Studios from Gumroad  Kemono/sf2_smpl.wav").st_size, 806998)
        self.assertEqual(os.stat(TESTING_PATH + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/BONUS_TRACK_Cant_Tail_Me_Nothing.mp3").st_size, 6541049)
        self.assertEqual(os.stat(TESTING_PATH + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/Tribute_to_1776.mp3").st_size, 6244398)
        self.assertEqual(os.stat(TESTING_PATH + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/Why_Am_I_Michael_Bluth.mp3").st_size, 1746643)

    def test_download_zip_attachments(self) -> None:
        """
        Tests downloading of a zip file and unzipping of zip files
        """
        # Single zip file
        self.KMP = KMP(TESTING_PATH, unzip=True, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/gumroad/user/samplescience/post/YeLB")

        size = 0 
        for dirpath, dirnames, filenames in os.walk(TESTING_PATH + "/SampleScience Plugins  Samples/SampleScience TR-626 HD by SampleScience Plugins  Samples. from Gumroad  Kemono/SampleScience_TR626_HD"):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    size += os.path.getsize(fp)

        self.assertEqual(size, 4509259)
    
    def test_download_alternate_zip_attachments(self) -> None:
        """
        Tests downloading of alternate zip files (7z...) and unzipping
        """

        self.KMP = KMP(TESTING_PATH, unzip=True, tcount=1, chunksz=None)
        # Single 7z file & .zxp
    
        # Single .rar file 
        self.KMP.routine("https://kemono.party/gumroad/user/6075196025658/post/lWrr")
    
    def test_uncommon_download_attachments(self) -> None:
        """
        Tests uncommon download formats in Download segment
        """
        # .Blend
        # https://kemono.party/gumroad/user/6755479123415/post/EheuMP

        # .abr
        # https://kemono.party/gumroad/user/5239319884170/post/fMclB

        # .tpl
        # https://kemono.party/gumroad/user/5239319884170/post/azNaf

        # .sut, .lip, .avi, .txt
        # https://kemono.party/gumroad/user/6558176578190/post/vnhy

        # .ma
        # https://kemono.party/gumroad/user/6075196025658/post/ftVdI

        # .rtf
        # https://kemono.party/gumroad/user/3934485177949/post/VYvWE

        # .obj
        # https://kemono.party/gumroad/user/1004191806794/post/NYsAA

        # .psd
        # https://kemono.party/gumroad/user/1863527794546/post/GSSm

        # .zid
        # https://kemono.party/gumroad/user/4529734555365/post/evvI

        # .brushset
        # https://kemono.party/gumroad/user/672140562092/post/sydbc

        # .brush
        # https://kemono.party/gumroad/user/672140562092/post/rFOBg

        # .procreate
        # https://kemono.party/gumroad/user/672140562092/post/dISIQ

        # .fbx
        # https://kemono.party/gumroad/user/5906818079786/post/BpmcW

        # .atn
        # https://kemono.party/gumroad/user/2186669714551/post/zjvDS

        # .csv
        # https://kemono.party/gumroad/user/3915675902935/post/XbrSX

        # .hda
        # https://kemono.party/gumroad/user/6760011976630/post/UrQub

        # .otf, .ttf
        # https://kemono.party/gumroad/user/879565995783/post/MdMYl

        # .hipnc
        # https://kemono.party/gumroad/user/9990773486171/post/xahaX

        # .ai
        # https://kemono.party/gumroad/user/4153645696389/post/hbgPnL
        
        # .html
        # https://kemono.party/gumroad/user/4488028154834/post/WGERs

        # .mfg
        # https://kemono.party/gumroad/user/5468065099305/post/KZKbe
    
    def test_download_bulk(self) -> None:
        """
        Tests downloading bulk files
        """
        # Single url, all works
        # https://kemono.party/gumroad/user/5352387105120

        # Single url, single work
        # https://kemono.party/gumroad/user/650894809818/post/HskiT

        # Multi url, all works
        # https://kemono.party/gumroad/user/5252246151109
        # https://kemono.party/gumroad/user/6100863138065

        # Multi url, works only
        # https://kemono.party/gumroad/user/5428435542017/post/wEhslZ
        # https://kemono.party/gumroad/user/863606373292/post/FyiUu

        # Multi url, mix of works
        # https://kemono.party/gumroad/user/7331928256471/post/yPvnb
        # https://kemono.party/gumroad/user/3340403173434
        # https://kemono.party/gumroad/user/7331928256471/post/iMbJe

    def test_download_different_services(self):
        """
        Tests downloading of difference services. Downloads single work 
        only since some services feature only NSFW artists with some safe works 

        """

        # Fantia
        # https://kemono.party/fantia/user/5755/post/777242

        # Discord <UNSUPPORTED>

        # DLSite
        # https://kemono.party/dlsite/user/RG44418/post/RE276179

        # SubscribeStar
        # https://kemono.party/subscribestar/user/furronika/post/470586

        # Gumroad
        # https://kemono.party/gumroad/user/2180412408086/post/nskyv

        # Fanbox
        # https://kemono.party/fanbox/user/49260/post/1564117

        # Patreon
        # https://kemono.party/patreon/user/16097004/post/48090388

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete temporary testing directory
        """
        # If the directory exists, delete it
        if os.path.exists(TESTING_PATH):
            shutil.rmtree(TESTING_PATH, ignore_errors=True)
if __name__ == '__main__':
    unittest.main()