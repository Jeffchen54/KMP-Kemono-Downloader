from re import T
import shutil
from tkinter import N
import unittest
from KMPDownloader import KMP
import os
from KMPDownloader import DeadThreadPoolException
import logging
"""
Tests KMPDownloader.py, tests utilize safe works only
All downloaded files are automatically wiped

Author: Jeff Chen
Last modified: 6/6/2022
"""


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
        cls.tempdir = os.path.abspath('./') + '/temp/'
        print(cls.tempdir)
        if os.path.exists(cls.tempdir):
            shutil.rmtree(cls.tempdir)

    def test_start_kill_threads(self) -> None:
        """
        Tests the starting and killing of threads
        """
        self.KMP = KMP(self.tempdir, False, tcount=None, chunksz=None)
        
        # Single thread
        self.KMP._KMP__threads = self.KMP._KMP__create_threads(1)
        self.KMP._KMP__kill_threads(self.KMP._KMP__threads)
        self.assertRaises(DeadThreadPoolException, self.KMP._KMP__call_and_interpret_url,
                          "https://kemono.party/gumroad/user/9222612694494/post/AizNy")

        # 3 Threads
        self.KMP._KMP__threads = self.KMP._KMP__create_threads(3)
        self.KMP._KMP__kill_threads(self.KMP._KMP__threads)
        self.assertRaises(DeadThreadPoolException, self.KMP._KMP__call_and_interpret_url,
                          "https://kemono.party/gumroad/user/9222612694494/post/AizNy")

    def test_trim_fname(self) -> None:
        """
        Tests __trim_fname
        """
        self.KMP = KMP(self.tempdir, False, tcount=None, chunksz=None)
        # <a class="post__attachment-link" href="/data/ac/95/ac95d0d22d3bf2b76e66305ba8b45e573d08980419f7aca786e11945f53342c4.zip?f=%E3%81%BE%E3%81%A8%E3%82%81DL%E7%94%A8.zip">
        #    Download まとめDL用.zip
        #  </a>
        self.assertEqual(self.KMP._KMP__trim_fname(
            "Download まとめDL用.zip"), "まとめDL用.zip")

    def test_download_static_files(self) -> None:
        """
        Tests downloading files under different circumstances
        """

        # Single thread no image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/33271853/post/36694748")

        # 3 Thread no image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/33271853/post/47946953")

        # Single Thread, 2 image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/33271853/post/36001529")

        # 3 Threads, 2 image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/33271853/post/47255266")

        # 1 Thread, multi images
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/33271853/post/65647736")

        # 16 Thread multi images
        self.KMP = KMP(self.tempdir, unzip=False, tcount=16, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/33271853/post/52792630")

        # Verify content:
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/0.png").st_size, 3692609)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/1.png").st_size, 3692609)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/2.png").st_size, 2752125)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/3.png").st_size, 3262789)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/4.png").st_size, 2392221)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/5.png").st_size, 2349839)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/6.png").st_size, 5652120)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/7.png").st_size, 1825005)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/8.png").st_size, 3002485)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/NAPP 3.0 PREVIEW by delcieno from Patreon  Kemono/9.png").st_size, 4467542)

        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/0.png").st_size, 13444381)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/1.png").st_size, 13444381)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/2.png").st_size, 13854733)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/3.png").st_size, 13702259)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/4.png").st_size, 13802523)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/5.png").st_size, 13040955)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/6.png").st_size, 13911132)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/7.png").st_size, 13524999)
        self.assertEqual(os.stat(
            self.tempdir + "delcieno/ARMORS and NAPP status by delcieno from Patreon  Kemono/8.png").st_size, 12743876)

    def test_download_static_attachments(self) -> None:
        """
        Tests downloading static attachments
        """
        # Single .pdf
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/gumroad/user/5563321775917/post/wSIJ")

        # Single .cvf
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/gumroad/user/5563321775917/post/mRSH")

        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/New Creator FAQ - All the Basics in One Place by Gumroad Help Center from Gumroad  Kemono/Creatorpedia.pdf").st_size, 14704)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/An Example CSV of Exported Sales Data by Gumroad Help Center from Gumroad  Kemono/Sales_CSV_Example.csv").st_size, 2933)

    def test_download_animated_attachments(self) -> None:
        """
        Tests downloaded animated gif files
        """
        # 2 Threads, 2 gifs
        self.KMP = KMP(self.tempdir, unzip=False, tcount=2, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/patreon/user/523894/post/66527944")

        # Single .mp4
        self.KMP.routine(
            "https://kemono.party/gumroad/user/5563321775917/post/jnBuO")

        # .mov
        self.KMP.routine(
            "https://kemono.party/gumroad/user/8844596389936/post/WBlK")

        self.assertEqual(os.stat(
            self.tempdir + "Jasonafex/New Playable Build 0.6.6 by Jasonafex from Patreon  Kemono/1.gif").st_size, 1930242)
        self.assertEqual(os.stat(
            self.tempdir + "Jasonafex/New Playable Build 0.6.6 by Jasonafex from Patreon  Kemono/0.gif").st_size, 1930242)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/Creating a Product - A Streaming Video Experience by Gumroad Help Center from Gumroad  Kemono/Product_Creation_-_Export_1015.mp4").st_size, 58934883)
        self.assertEqual(os.stat(
            self.tempdir + "Katon Callaway/Topology Tips  by Katon Callaway from Gumroad  Kemono/topoJoints.mov").st_size, 448251813)

    def test_download_audio_attachments(self) -> None:
        """
        Tests downloading audio files
        """
        # 3 mp3
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/gumroad/user/5563321775917/post/moNG")

        # .sf2, .wav
        self.KMP.routine(
            "https://kemono.party/gumroad/user/3915675902935/post/NTJQZ")

        self.assertEqual(os.stat(self.tempdir + "Truebones Motions Animation Studios/FREE STAR TREK SOUND FX INCLUDES SOUND FONT and .WAV file formats. by Truebones Motions Animation Studios from Gumroad  Kemono/HS_StarTrekFX.sf2").st_size, 807090)
        self.assertEqual(os.stat(self.tempdir + "Truebones Motions Animation Studios/FREE STAR TREK SOUND FX INCLUDES SOUND FONT and .WAV file formats. by Truebones Motions Animation Studios from Gumroad  Kemono/sf2_smpl.wav").st_size, 806998)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/BONUS_TRACK_Cant_Tail_Me_Nothing.mp3").st_size, 6541049)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/Tribute_to_1776.mp3").st_size, 6244398)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/Why_Am_I_Michael_Bluth.mp3").st_size, 1746643)

    def test_download_zip_attachments(self) -> None:
        """
        Tests downloading of a zip file and unzipping of zip files
        """
        # Single zip file
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None)
        self.KMP.routine(
            "https://kemono.party/gumroad/user/samplescience/post/YeLB")

        size = self.getDirSz(self.tempdir + (
            r"SampleScience Plugins  Samples/SampleScience TR-626 HD by SampleScience Plugins  Samples. from Gumroad  Kemono/SampleScience_TR626_HD"))
        self.assertEqual(size, 4509259)

    def test_download_alternate_zip_attachments(self) -> None:
        """
        Tests downloading of alternate zip files (7z...) and unzipping
        """

        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None)
        # Single 7z file
        # TODO NEEDS A LINK!!!

        # Single .rar file
        self.KMP.routine(
            "https://kemono.party/gumroad/user/6075196025658/post/lWrr")
        size = self.getDirSz(self.tempdir + (
            r"Joe Daniels/jd Flour Sack rig for Maya by Joe Daniels from Gumroad  Kemono/jd_floursack"))
        self.assertEqual(size, 4878146)

    def test_download_non_file(self) -> None:
        """
        Tests downloading an invalid file
        """
        # If it don't crash, it pass
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None)
        self.KMP.routine("https://kemono.party/patreon/user/8296916/post/59821763")
    
    def test_download_empty_window(self) -> None:
        """
        Tests downloading am artist with no works
        """

    def test_download_bulk(self) -> None:
        """
        Tests downloading bulk files
        """
        temp = os.path.join(self.tempdir, "temp.txt")
        self.KMP = KMP(self.tempdir, unzip=True, tcount=6, chunksz=None)
        if os.path.exists(temp):
            os.remove(temp)


        # Single url, all works
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/5352387105120\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(fd.readlines())

        # Single url, single work
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/650894809818/post/HskiT\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(fd.readlines())

        # Multi url, all works
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/5252246151109\n")
            fd.write("https://kemono.party/gumroad/user/6100863138065\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(fd.readlines())

        # Multi url, works only
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/5428435542017/post/wEhslZ\n")
            fd.write("https://kemono.party/gumroad/user/863606373292/post/FyiUu\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(fd.readlines())

        # Multi url, mix of works
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/7331928256471/post/yPvnb\n")
            fd.write("https://kemono.party/gumroad/user/3340403173434\n")
            fd.write("https://kemono.party/gumroad/user/7331928256471/post/iMbJe\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(fd.readlines())
        
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Perry Leijten/Maya skinning tools by Perry Leijten from Gumroad  Kemono")), 6862522)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Perry Leijten/Samus Rig by Perry Leijten from Gumroad  Kemono")), 72827106)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Jabir J3")), 952513)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Kenzie Smith Piano")), 4362578)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "MortMort")), 80470)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Nikolai Mamashev")), 98229752)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Randy Bishop")), 70006225)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Skylleon")), 4246089)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Tatyworks")), 19828495)
        os.remove(temp)

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

    def test_post_content(self) -> None:
        """
        Tests the downloading of post content
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None)

        # Empty post content
        self.KMP.routine("https://kemono.party/gumroad/user/6033318026591/post/uijUqf")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Motion Ape/Free Bounce Tool for After Effects by Motion Ape from Gumroad  Kemono/post__content.txt")))

        # Plaintext only
        self.KMP.routine(
            "https://kemono.party/patreon/user/8296916/post/53546555")
        with open(os.path.join(self.tempdir, "dreamsavior/Translator Ver 3.7.11 by dreamsavior from Patreon  Kemono/post__content.txt"), 'r') as fd:
            self.assertEqual(fd.read(), "There is a bug on ver 3.7.9 that prevents some users from installing the addon. This version fixes that bug.\
\nThis version also fixes a bug that caused Translator++ to write files with ASCII encoding characters despites the translation target being UTF8\
\nTranslator++ Ver 3.7.11\
\nUpdate : Renparser Ver 0.7.2\
\nFix : Renpy : Failed when exporting into a file\
\nFix : Renpy : Force write encoding into UTF-8 when detected as ASCII\
\nUpdate : KAGParser 1.2\
\nFix : KAG : Force write encoding into UTF-8 when detected as ASCII\
\nFix : Unable to install new addon\
\nI'm sorry for the inconvenience.\
\nEnjoy your day, and stay safe.\
\n(Yesterday I got the news that my mother and my brother were positive for covid)")

        # Links
        self.KMP.routine(
            "https://kemono.party/patreon/user/8296916/post/52915682")
        with open(os.path.join(self.tempdir, "dreamsavior/RPG Maker MZ Is Free on steam by dreamsavior from Patreon  Kemono/post__content.txt"), 'r') as fd:
            self.assertEqual(fd.read(), "Just a short notice. I'm not affiliated with Kadokawa nor endorsed by them. But \
when they make they software free ... even though for limited time I need to notice you all. You may need it to \
do minor editing to translate RMMZ based game.\nhttps://store.steampowered.com/app/1096900/RPG_Maker_MZ/\
\nhttps://store.steampowered.com/app/1096900/RPG_Maker_MZ/")

        # Images
        # <NOT SUPPORTED>
    
    def test_post_comments(self) -> None:
        """
        Tests downloading post comment
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None)

        # Empty
        self.KMP.routine("https://kemono.party/patreon/user/5442365/post/19064809")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "ZebraCorner/Patreon Rewards Update and follow us on Social Media by ZebraCorner from Patreon  Kemono/post__comments.txt")))
        # Gumroad
        self.KMP.routine("https://kemono.party/gumroad/user/6033318026591/post/LRWjd")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Motion Ape/Free Folder Structurer Tool for After Effects by Motion Ape from Gumroad  Kemono/post__comments.txt")))
        # Fantia
        self.KMP.routine("https://kemono.party/fantia/user/53451/post/775490")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "おののいもこ/眼鏡子 by おののいもこ from Fantia  Kemono/post__comments.txt")))
        # SubscribeStar TODO
        self.KMP.routine("https://kemono.party/subscribestar/user/sleepygimp/post/305785")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "sleepygimp/Nancys Day Off r08Dear Supportersyet again just in t.. by sleepygimp from SubscribeStar  Kemono/post__comments.txt")))
        # DL site
        self.KMP.routine("https://kemono.party/dlsite/user/RG44418/post/RE243414")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "DLsite/FREE Life with Maid Kurumi-chan At Your Side Binaural by DLsite from DLsite  Kemono/post__comments.txt")))
        # Not empty
        self.KMP.routine("https://kemono.party/fanbox/user/237083/post/3011863")
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "Blood Rouge/WIP唾吐きクソビッチと化した金城遙華 by Blood Rouge from Pixiv Fanbox  Kemono/post__comments.txt")))       

    def getDirSz(self, dir: str) -> int:
        """
        Returns directory and its content size

        Return directory and its content size
        """
        size = 0
        for dirpath, dirname, filenames in os.walk(dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    size += os.path.getsize(fp)
        return size


if __name__ == '__main__':
    unittest.main()
