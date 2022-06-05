from tkinter import N
import unittest
from KMPDownloader import KMP
import dirs
import os
import shutil
from KMPDownloader import DeadThreadPoolException
"""
Tests KMPDownloader.py, tests utilize safe works only

Author: Jeff Chen
Last modified: 6/5/2022
"""


# Constants
TESTING_PATH = dirs.replace_dots_to_py_path("./")

class KMPTestCase(unittest.TestCase):

    def setUp(self) -> None:
        """
        Sets up an Null KMP since tests require different paramaters
        """
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
        Tests the starting and killing of threadss
        """
        self.KMP.__KMP__folder = TESTING_PATH

        # Single thread
        self.KMP.__KMP.__threads = self.KMP.__KMP.__create_threads(1)
        self.KMP.__KMP.__kill_threads(self.KMP.__KMP.__threads)
        self.assertRaises(DeadThreadPoolException, self.KMP.__KMP.__call_and_interpret_url("https://kemono.party/gumroad/user/9222612694494/post/AizNy"))

        # 3 Threads
        self.KMP.__KMP.__threads = self.KMP.__KMP.__create_threads(3)
        self.KMP.__KMP.__kill_threads(self.KMP.__KMP.__threads)
        self.assertRaises(DeadThreadPoolException, self.KMP.__KMP.__call_and_interpret_url("https://kemono.party/gumroad/user/9222612694494/post/AizNy"))

    def test_trim_fname() -> None:
        """
        Tests __trim_fname
        """
        # Matching extensions
        # href="/data/5d/72/5d72201f60ad8927300dd5de1324fe3100a0876c67a394df71db242ba2b8e27a.zip?f=%5B19.01%5D%20KDA%202%20%26%20Bea%20Gui%20%26%20Lt%20a%20%5BGumroad%5D.zip"

        # Mismatched extension
        # href = "/data/0f/a8/0fa896658a877e98812f24da58b19fdf0b2db1220587639f614cafcce34b59f8.bin?f=kre_l.mp4
    def test_download_static_files(self) -> None:
        """
        Tests downloading files under different circumstances
        """
        # https://kemono.party/patreon/user/33271853?o=0
        # Single Thread, single image

        # 3 Threads, single image

        # 1 Thread, multi images

        # 3 cores multi images

        # Single .pdf
        # https://kemono.party/gumroad/user/5563321775917/post/wSIJ

        # Single .cvf
        # https://kemono.party/gumroad/user/5563321775917/post/mRSH

    def test_download_animated_files(self) -> None:
        """
        Tests downloaded animated gif files
        """
        # 2 Threads, 2 gifs
        # https://kemono.party/patreon/user/523894/post/66527944

        # Single .mp4 
        # https://kemono.party/gumroad/user/5563321775917/post/jnBuO

        # .mov 
        # https://kemono.party/gumroad/user/8844596389936/post/WBlK

    def test_download_audio_files(self) -> None:
        """
        Tests downloading audio files
        """
        # 3 mp3
        # https://kemono.party/gumroad/user/5563321775917/post/moNG

        # .sf2, .wav
        # https://kemono.party/gumroad/user/3915675902935/post/NTJQZ

    def test_download_zip_files(self) -> None:
        """
        Tests downloading of a zip file and unzipping of zip files
        """
        # Single zip file
        # https://kemono.party/gumroad/user/samplescience/post/YeLB


        # 
    
    def test_download_alternate_zip_files(self) -> None:
        """
        Tests downloading of alternate zip files (7z...) and unzipping
        """
        # Single 7z file & .zxp

        # Single .rar file 
        # https://kemono.party/gumroad/user/6075196025658/post/lWrr
    
    def test_uncommon_download_types(self) -> None:
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