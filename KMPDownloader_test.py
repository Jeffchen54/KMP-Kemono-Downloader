from re import T
import shutil
from tkinter import N
import unittest
from KMPDownloader import KMP
import os
from KMPDownloader import DeadThreadPoolException
import logging
from Threadpool import tname
"""
Tests KMPDownloader.py,
##################################################
WARNING Contains unsafe works!!! #################
##################################################

Author: Jeff Chen
Last modified: 6/6/2022
"""
class KMPTestCase(unittest.TestCase):

    def setUp(self) -> None:
        """
        Sets up an Null KMP since tests require different paramaters
        """
        logging.basicConfig(level=logging.INFO)
        self.KMP = None
        tname.id = None

    @classmethod
    def setUpClass(cls):
        """
        Create temporary testing directory
        """
        cls.tempdir = os.path.abspath('./') + '\\temp\\'

        if os.path.exists(cls.tempdir):
            logging.critical("Please remove before testing ->" + cls.tempdir)
            exit()

    def test_start_kill_threads(self) -> None:
        """
        Tests the starting and killing of threads
        """
        self.KMP = KMP(self.tempdir, False, tcount=None, chunksz=None, ext_blacklist=None)
        
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

        self.KMP.close()
    def test_trim_fname(self) -> None:
        """
        Tests __trim_fname
        """
        self.KMP = KMP(self.tempdir, False, tcount=None, chunksz=None, ext_blacklist=None)
        # <a class="post__attachment-link" href="/data/ac/95/ac95d0d22d3bf2b76e66305ba8b45e573d08980419f7aca786e11945f53342c4.zip?f=%E3%81%BE%E3%81%A8%E3%82%81DL%E7%94%A8.zip">
        #    Download まとめDL用.zip
        #  </a>

        # Case 3 -> Space
        self.assertEqual(self.KMP._KMP__trim_fname(
            "Download まとめDL用.zip"), "まとめDL用.zip")

        # Case 3 -> Multiple spaces
        self.assertEqual(self.KMP._KMP__trim_fname(
            "Download 1_2 2016 aged whiskey.zip"), "1_2 2016 aged whiskey.zip")

        # Case 2 -> Bad extension
        self.assertEqual(self.KMP._KMP__trim_fname(
            "/data/3d/68/3d68def31822e95ad249ceb2237fcdae29b644e6702366ddae761572be900955.jpg?f=https%3A//c10.patreonusercontent.\
com/3/e30%253D/patreon-media/p/post/30194248/7cffbc9604664ccab13f3b57fdc78e6f/1.jpe%3Ftoken-time%3D1570752000%26token\
-hash%3DLadY-wBiRPi84Qb5X-KI7NEgEP6HE6lljOLiHBm7qY8%253D"), "3d68def31822e95ad249ceb2237fcdae29b644e6702366ddae761572be900955.jpg")

        # Case 1 -> Good extension
        self.assertEqual(self.KMP._KMP__trim_fname(
            "/data/4f/83/4f83453fc625095401da81248a2242246b01b229bc5e1b2e1dd470da866f1980.jpg?f=b9ffc2f9-2c11-42c8-b5a2-7995a233ca41\
.jpg"), "b9ffc2f9-2c11-42c8-b5a2-7995a233ca41.jpg")

        self.assertEqual(self.KMP._KMP__trim_fname("/data/8b/e7/8be7e3fc0b0304c97b0bd5d9f7a66b2ad97c2d798808b52824642480e8dfe0d7.gif?f=BBS-Snoggler-Update.gif"), "BBS-Snoggler-Update.gif")
        self.KMP.close()
    def test_download_static_files(self) -> None:
        """
        Tests downloading files under different circumstances
        """

        # Single thread no image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/33271853/post/36694748")
        self.KMP.close()

        # 3 Thread no image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/33271853/post/47946953")
        self.KMP.close()

        # Single Thread, 2 image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/33271853/post/36001529")
        self.KMP.close()

        # 3 Threads, 2 image
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/33271853/post/47255266")
        self.KMP.close()

        # 1 Thread, multi images
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/33271853/post/65647736")
        self.KMP.close()

        # 16 Thread multi images
        self.KMP = KMP(self.tempdir, unzip=False, tcount=16, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/33271853/post/52792630")
        self.KMP.close()

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
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/5563321775917/post/wSIJ")
        self.KMP.close()

        # Single .cvf
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/5563321775917/post/mRSH")
        self.KMP.close()

        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/New Creator FAQ - All the Basics in One Place by Gumroad Help Center from Gumroad  Kemono/Creatorpedia.pdf").st_size, 14704)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/An Example CSV of Exported Sales Data by Gumroad Help Center from Gumroad  Kemono/Sales_CSV_Example.csv").st_size, 2933)

    def test_download_animated_attachments(self) -> None:
        """
        Tests downloaded animated gif files
        """
        # 2 Threads, 2 gifs
        self.KMP = KMP(self.tempdir, unzip=False, tcount=2, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/523894/post/66527944")
        self.KMP.close()

        # Single .mp4
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/5563321775917/post/jnBuO")

        # .mov
        self.KMP.routine(unpacked=0, url=
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
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/5563321775917/post/moNG")

        # .sf2, .wav
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/3915675902935/post/NTJQZ")

        self.assertEqual(os.stat(self.tempdir + "Truebones Motions Animation Studios/FREE STAR TREK SOUND FX INCLUDES SOUND FONT and .WAV file formats. by Truebones Motions Animation Studios from Gumroad  Kemono/HS_StarTrekFX.sf2").st_size, 807090)
        self.assertEqual(os.stat(self.tempdir + "Truebones Motions Animation Studios/FREE STAR TREK SOUND FX INCLUDES SOUND FONT and .WAV file formats. by Truebones Motions Animation Studios from Gumroad  Kemono/sf2_smpl.wav").st_size, 806998)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/BONUS_TRACK_Cant_Tail_Me_Nothing.mp3").st_size, 6541049)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/Tribute_to_1776.mp3").st_size, 6244398)
        self.assertEqual(os.stat(
            self.tempdir + "Gumroad Help Center/A Music Album - Jam time by Gumroad Help Center from Gumroad  Kemono/Why_Am_I_Michael_Bluth.mp3").st_size, 1746643)
        self.KMP.close()

    def test_download_zip_attachments(self) -> None:
        """
        Tests downloading of a zip file and unzipping of zip files
        """
        # Single zip file
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/samplescience/post/YeLB")

        size = self.getDirSz(self.tempdir + (
            r"SampleScience Plugins  Samples/SampleScience TR-626 HD by SampleScience Plugins  Samples. from Gumroad  Kemono/SampleScience_TR626_HD"))
        self.assertEqual(size, 4509259)
        self.KMP.close()

    def test_download_alternate_zip_attachments(self) -> None:
        """
        Tests downloading of alternate zip files (7z...) and unzipping
        """

        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None, ext_blacklist=None)
        # Single 7z file
        # Has been tested in other tests

        # Single .rar file
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/gumroad/user/6075196025658/post/lWrr")
        size = self.getDirSz(self.tempdir + (
            r"Joe Daniels/jd Flour Sack rig for Maya by Joe Daniels from Gumroad  Kemono/jd_floursack"))
        self.assertEqual(size, 4878146)
        self.KMP.close()

    def test_download_non_file(self) -> None:
        """
        Tests downloading an invalid file
        """
        # If it don't crash, it pass
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/8296916/post/59821763")
        self.KMP.close()  
    
    def test_download_empty_window(self) -> None:
        """
        Tests downloading an artist with no works
        """
        # https://kemono.party/gumroad/user/gunwild
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/8296916/post/59821763")
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "Gunwild")), 0)
        self.KMP.close()

    def test_file_text(self) -> None:
        """
        Tests downloading an artist with a link in their files segment
        """
        self.KMP = KMP(self.tempdir, unzip=False, tcount=1, chunksz=None, ext_blacklist=None)
        
        # DNE
        self.KMP.routine(unpacked=0, url="https://kemono.party/fanbox/user/305765/post/3885644")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Y.P/NEXT by Y.P from Pixiv Fanbox  Kemono/file__text.txt")))

        # Exists
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/5489259/post/30194248")
        with open(os.path.join(self.tempdir, "misswarmj/My First NSFW ASMR Video Preview  by misswarmj from Patreon  Kemono/file__text.txt"), 'r') as fd:
            self.assertEqual(fd.read(), "MissWarmJ on Twitter\n\
              \n\
\n\
                  Hey,pls wear your earphone watch till the end! 1:38minuts~ It is the first NSFW #ASMR Preview. Would appriated Mega RT and Likes ^^ https://t.co/mwmfzS0cfb https://t.co/3n7bUYMzRD\n\
https://twitter.com/misswarmj/status/1176210868121546752\n\
\
____________________________________________________________\n\
")
        self.KMP.close()


    def test_download_bulk(self) -> None:
        """
        Tests downloading bulk files
        """
        temp = os.path.join(self.tempdir, "temp.txt")
        self.KMP = KMP(self.tempdir, unzip=True, tcount=6, chunksz=None, ext_blacklist=None)
        if os.path.exists(temp):
            os.remove(temp)


        # Single url, all works
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/5352387105120\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(unpacked=0, url=fd.readlines())

        # Single url, single work
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/650894809818/post/HskiT\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(unpacked=0, url=fd.readlines())

        # Multi url, all works
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/5252246151109\n")
            fd.write("https://kemono.party/gumroad/user/6100863138065\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(unpacked=0, url=fd.readlines())

        # Multi url, works only
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/5428435542017/post/wEhslZ\n")
            fd.write("https://kemono.party/gumroad/user/863606373292/post/FyiUu\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(unpacked=0, url=fd.readlines())

        # Multi url, mix of works
        os.remove(temp)
        with open(temp, 'w+') as fd:
            fd.write("https://kemono.party/gumroad/user/7331928256471/post/yPvnb\n")
            fd.write("https://kemono.party/gumroad/user/3340403173434\n")
            fd.write("https://kemono.party/gumroad/user/7331928256471/post/iMbJe\n")
            fd.flush()
            fd.seek(0)
            self.KMP.routine(unpacked=0, url=fd.readlines())
        
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
        self.KMP.close()

    def test_download_polluted_href(self):
        """
        Tests downloading files from a source that contains both internally hosted
        and externally hosted URLs. 
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=2, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/fanbox/user/3102267/post/3841095")
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "mochitaichi/抱き枕カバー用のラフ by mochitaichi from Pixiv Fanbox  Kemono")), 3716346)
        self.KMP.close()

    def test_extract_same__dest(self):
        """
        Tests extracting xzip files to the same directory
        """
        # Zip File already exists
        
        second = KMP(self.tempdir, unzip=True, tcount=2, chunksz=None, ext_blacklist=None)
        second.routine(unpacked=0, url="https://kemono.party/fanbox/user/646778/post/3474562")

        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "nbit/Basic 2022年 03月 by nbit from Pixiv Fanbox  Kemono/01basic - Blue Archive Ako.zip")))
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "nbit/Basic 2022年 03月 by nbit from Pixiv Fanbox  Kemono/01basic - Blue Archive Ako.zip")))
        size = self.getDirSz(self.tempdir + (
            r"nbit/Basic 2022年 03月 by nbit from Pixiv Fanbox  Kemono/cap"))
        size2 = self.getDirSz(self.tempdir + (
        r"nbit/Basic 2022年 03月 by nbit from Pixiv Fanbox  Kemono/(1)cap"))
        self.assertTrue(size ==  63149843 or size == 103350378)
        self.assertTrue(size2 == 63149843 or size2 == 103350378)
        second.close()
    
    def test_duplicate_file(self):
        """
        WARNING: Test takes significant time to complete

        Tests downloading a set of files and redownloading it, no new files
        should be added after redownloading
        """
        # Download directory
        self.KMP = KMP(self.tempdir, unzip=True, tcount=12, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url='https://kemono.party/fanbox/user/39123643?o=25')
        
        # get size
        size = self.getDirSz(self.tempdir + (r"Belko"))
        logging.info(size)
        # Redownload
        self.KMP.reset()
        self.KMP.routine(unpacked=0, url='https://kemono.party/fanbox/user/39123643?o=25')

        # Confirm size is unchanged
        self.assertEqual(self.getDirSz(self.tempdir + (r"Belko")), size)
        self.KMP.close()

    def test_download_dead_image(self):
        """
        Tests downloading a dead 3rd party link
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=2, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/5489259/post/22660508")
        self.KMP.close()
        # If it does not crash, it passes
    
    def test_download_link_not_file(self):
        """
        Tests downloading a page where the download section contains links instead 
        of files, should be skipped
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=2, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/5489259/post/29891980")  
        self.KMP.close()      
        # If it does not crash, it passes

    def test_download_non_image_img(self):
        """
        Tests downloading an 'image' that isn't actually an image but a link
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=2, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/5489259/post/16278266")

        self.assertTrue(os.path.exists(self.tempdir + "misswarmj/New Feet lover post on Twitter by misswarmj from Patreon  Kemono/0.jpg"))
        self.assertTrue(os.path.exists(self.tempdir + "misswarmj/New Feet lover post on Twitter by misswarmj from Patreon  Kemono/1.jpg"))
        self.assertFalse(os.path.exists(self.tempdir + "misswarmj/New Feet lover post on Twitter by misswarmj from Patreon  Kemono/2.jpg"))
        self.assertTrue(os.path.exists(self.tempdir + "misswarmj/New Feet lover post on Twitter by misswarmj from Patreon  Kemono/3.jpg"))
        self.KMP.close()

    def test_post_content(self) -> None:
        """
        Tests the downloading of post content
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None, ext_blacklist=None)

        # Empty post content
        self.KMP.routine(unpacked=0, url="https://kemono.party/gumroad/user/6033318026591/post/uijUqf")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Motion Ape/Free Bounce Tool for After Effects by Motion Ape from Gumroad  Kemono/post__content.txt")))

        # Plaintext only
        self.KMP.routine(unpacked=0, url=
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
        self.KMP.routine(unpacked=0, url=
            "https://kemono.party/patreon/user/8296916/post/52915682")
        with open(os.path.join(self.tempdir, "dreamsavior/RPG Maker MZ Is Free on steam by dreamsavior from Patreon  Kemono/post__content.txt"), 'r') as fd:
            self.assertEqual(fd.read(), "Just a short notice. I'm not affiliated with Kadokawa nor endorsed by them. But \
when they make they software free ... even though for limited time I need to notice you all. You may need it to \
do minor editing to translate RMMZ based game.\nhttps://store.steampowered.com/app/1096900/RPG_Maker_MZ/\
\nhttps://store.steampowered.com/app/1096900/RPG_Maker_MZ/")

        # Images on KMP and on other website
        # https://kemono.party/patreon/user/8296916/post/52732723
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/8296916/post/52732723")
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "dreamsavior/Error File list not found in init file by dreamsavior from Patreon  Kemono/0.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "dreamsavior/Error File list not found in init file by dreamsavior from Patreon  Kemono/1.png")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "dreamsavior/Error File list not found in init file by dreamsavior from Patreon  Kemono/2.png")))
        self.KMP.close()

    def test_post_comments(self) -> None:
        """
        Tests downloading post comment
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=1, chunksz=None, ext_blacklist=None)

        # Empty
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/5442365/post/19064809")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "ZebraCorner/Patreon Rewards Update and follow us on Social Media by ZebraCorner from Patreon  Kemono/post__comments.txt")))
        # Gumroad
        self.KMP.routine(unpacked=0, url="https://kemono.party/gumroad/user/6033318026591/post/LRWjd")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Motion Ape/Free Folder Structurer Tool for After Effects by Motion Ape from Gumroad  Kemono/post__comments.txt")))
        # Fantia
        self.KMP.routine(unpacked=0, url="https://kemono.party/fantia/user/53451/post/775490")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "おののいもこ/眼鏡子 by おののいもこ from Fantia  Kemono/post__comments.txt")))
        # SubscribeStar TODO
        self.KMP.routine(unpacked=0, url="https://kemono.party/subscribestar/user/sleepygimp/post/305785")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "sleepygimp/Nancys Day Off r08Dear Supportersyet again just in t.. by sleepygimp from SubscribeStar  Kemono/post__comments.txt")))
        # DL site
        self.KMP.routine(unpacked=0, url="https://kemono.party/dlsite/user/RG44418/post/RE243414")
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "DLsite/FREE Life with Maid Kurumi-chan At Your Side Binaural by DLsite from DLsite  Kemono/post__comments.txt")))
        # Not empty
        self.KMP.routine(unpacked=0, url="https://kemono.party/fanbox/user/237083/post/3011863")
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "Blood Rouge/WIP唾吐きクソビッチと化した金城遙華 by Blood Rouge from Pixiv Fanbox  Kemono/post__comments.txt")))       
        self.KMP.close()

    def test_broken_url(self):
        """
        Tests downloading of a file with bad file extension 
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/5489259/post/30194248")
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "misswarmj/My First NSFW ASMR Video Preview  by misswarmj from Patreon  Kemono/0.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "misswarmj/My First NSFW ASMR Video Preview  by misswarmj from Patreon  Kemono/1.jpg")))
        self.KMP.close()

    def test_discord(self):
        """
        Tests downloading discord content
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=12, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/discord/server/634594002624184360")

        # 100
        self.assertEqual(os.stat(os.path.join(self.tempdir, "634594002624184360/100円_100yen/discord__content.txt")).st_size, 7845)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "634594002624184360/100円_100yen/images")), 75556767)

        # 100(1)
        self.assertEqual(os.stat(os.path.join(self.tempdir, "634594002624184360/100円_100yen(1)/discord__content.txt")).st_size, 528)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "634594002624184360/100円_100yen(1)/images")), 0)
        
        # 300 
        self.assertEqual(os.stat(os.path.join(self.tempdir, "634594002624184360/300ビール_beer/discord__content.txt")).st_size, 20742)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "634594002624184360/300ビール_beer/images")), 277344917)

        # 300
        self.assertEqual(os.stat(os.path.join(self.tempdir, "634594002624184360/300ビール_beer(1)/discord__content.txt")).st_size, 4011)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "634594002624184360/300ビール_beer(1)/images")), 8197562)

        # wip
        self.assertEqual(os.stat(os.path.join(self.tempdir, "634594002624184360/作業中_wip/discord__content.txt")).st_size, 128463)
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "634594002624184360/作業中_wip/images")), 487333680)

        self.KMP.close()


    def test_unpacked(self):
        """
        Tests the unpacked download mode
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=10, chunksz=None, ext_blacklist=None)

        # No works
        self.KMP.routine(unpacked=2, url="https://kemono.party/gumroad/user/antijingoist")

        # All works
        self.KMP.routine(unpacked=2, url="https://kemono.party/fanbox/user/21587853")

        # Single page of works
        self.KMP.routine(unpacked=2, url="https://kemono.party/fanbox/user/144708?o=25")

        # Single work
        self.KMP.routine(unpacked=2, url="https://kemono.party/fanbox/user/24164271/post/2934828")

        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "Abbie Gonzalez")), 0)
        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "ie")), 1)
        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "みこやん")), 144)
        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "めかの工場")), 138)

        self.KMP.close()

    def test_download_undefined_char(self):
        """
        Tests downloading a file whose name contains an 
        undefined char
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=12, chunksz=None, ext_blacklist=None)
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/38223307/post/43447399")
        self.assertEqual(self.getDirSz(os.path.join(self.tempdir, "HALkawa501/PSDChina Miku PSDClip Data by HALkawa501 from Patreon  Kemono")), 140413258)
        self.KMP.close()

    def test_ext_blacklist(self):
        """
        Tests downloading files with a blacklist
        """
        # Non blacklisted
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=['psd', 'rando', 'doesnotexists', 'chicken', 'bacon'])
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/881792/post/64901768")
        self.KMP.close()

        # Some blacklisted
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=['mp4'])
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/881792/post/66258950")
        self.KMP.close()

        # All blacklisted
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=['gif'])
        self.KMP.routine(unpacked=0, url="https://kemono.party/patreon/user/881792/post/63450534")
        self.KMP.close()

        self.assertEqual(self.getDirSz(self.tempdir + "diives/Melina SMALL VIDEO WITH AUDIO by diives from Patreon  Kemono"), 11884327)
        self.assertEqual(self.getDirSz(self.tempdir + "diives/Nat The Bunny NDE by diives from Patreon  Kemono"), 1101)
        self.assertEqual(self.getDirSz(self.tempdir + "diives/Rya by diives from Patreon  Kemono"), 4708568)

        shutil.rmtree(self.tempdir + "diives/Nat The Bunny NDE by diives from Patreon  Kemono")

        # All blacklisted with partial unpacking
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=['gif'])
        self.KMP.routine(unpacked=1, url="https://kemono.party/patreon/user/881792/post/63450534")
        self.KMP.close()
        self.assertEqual(os.stat(self.tempdir + "diives/Nat The Bunny NDE by diives from Patreon  Kemono - post__content.txt").st_size, 230)
    

        # All blacklisted with unpacking
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=['gif'])
        self.KMP.routine(unpacked=2, url="https://kemono.party/patreon/user/881792/post/63450534")
        self.KMP.close()
        
        self.assertEqual(self.getNumFiles(self.tempdir + "diives"), 2)

    def test_partial_unpacked(self):
        """
        Tests partially unpacked download mode
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=None)
        
        # With files
        self.KMP.routine(unpacked=1, url="https://kemono.party/fanbox/user/49494721/post/3765544")

        self.assertEqual(self.getDirSz(self.tempdir + "soso\久岐忍 by soso from Pixiv Fanbox  Kemono"), 1899290)

        # No files
        self.KMP.routine(unpacked=1, url="https://kemono.party/fanbox/user/49494721/post/2082281")

        self.assertTrue(os.path.exists(self.tempdir + "soso/リクエストボックス by soso from Pixiv Fanbox  Kemono - post__comments.txt"))
        self.assertTrue(os.path.exists(self.tempdir + "soso/リクエストボックス by soso from Pixiv Fanbox  Kemono - post__content.txt"))
        self.KMP.close()
    
    def test_partial_unpacked_blacklist(self):
        """
        Tests partially unpacking a work that is empty after applying a blacklist
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, ext_blacklist=['jpg'])
        self.KMP.routine(unpacked=1, url="https://kemono.party/patreon/user/12281898/post/67498846")
        self.assertTrue(os.path.exists(self.tempdir + "MANA/WIP by MANA from Patreon  Kemono - post__content.txt"))
        self.assertFalse(os.path.exists(self.tempdir + "MANA/WIP by MANA from Patreon  Kemono"))
        
        self.KMP.close()
            
    def test_exclude_posts(self):
        """
        Tests excluding posts
        """
        # https://kemono.party/fanbox/user/3316400/post/488806
        # No exclusions
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, post_name_exclusion=[])
        self.KMP.routine("https://kemono.party/fanbox/user/3316400/post/532363", unpacked=None)
        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "MだSたろう\\BRSその２-高画質版2枚 by MだSたろう from Pixiv Fanbox  Kemono")), 4)
        self.KMP.close()
        
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, post_name_exclusion=["Nothing"])
        self.KMP.routine("https://kemono.party/fanbox/user/3316400/post/490300", unpacked=None)
        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "MだSたろう\\限定褐色 by MだSたろう from Pixiv Fanbox  Kemono")), 4)        
        self.KMP.close()
        
        # Exclusions
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, post_name_exclusion=["August"])
        self.KMP.routine("https://kemono.party/gumroad/user/trylsc", unpacked=None)
        self.assertEqual(self.getNumFiles(os.path.join(self.tempdir, "TRYLSC")), 0)        
        self.KMP.close()
        

    def test_exclude_link(self):
        """
        Tests excluding links
        """
        # No exclusions
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, link_name_exclusion=[])
        self.KMP.routine("https://kemono.party/gumroad/user/2986488497406/post/bMhu", unpacked=None)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "burningtides\Phuture Noize - A New Day Remake  FLP  Presets by burningtides from Gumroad  Kemono\Phuture-Noize---A-New-Day-Remake-.zip")))
        self.KMP.close()
        
        # Some exclusions
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, link_name_exclusion=["19","18"])
        self.KMP.routine("https://kemono.party/gumroad/user/5646205703539/post/xIMAi", unpacked=None)
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Pitiwazou - Cédric Lepiller\SPEEDSCULPT by Pitiwazou - Cédric Lepiller from Gumroad  Kemono\speedsculpt_2_80_v_0_1_19.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "Pitiwazou - Cédric Lepiller\SPEEDSCULPT by Pitiwazou - Cédric Lepiller from Gumroad  Kemono\speedsculpt_2_80_v_0_1_17.zip")))
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Pitiwazou - Cédric Lepiller\SPEEDSCULPT by Pitiwazou - Cédric Lepiller from Gumroad  Kemono\speedsculpt_2_80_v_0_1_18.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "Pitiwazou - Cédric Lepiller\SPEEDSCULPT by Pitiwazou - Cédric Lepiller from Gumroad  Kemono\speedsculpt_2_83_v_0_1_20.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "Pitiwazou - Cédric Lepiller\SPEEDSCULPT by Pitiwazou - Cédric Lepiller from Gumroad  Kemono\speedsculpt_2_9_v_0_1_22.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "Pitiwazou - Cédric Lepiller\SPEEDSCULPT by Pitiwazou - Cédric Lepiller from Gumroad  Kemono\speedsculpt_2_79_v_0_1_9.zip")))
        self.KMP.close()
        
        # All excluded
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, link_name_exclusion=["sfm"])
        self.KMP.routine("https://kemono.party/gumroad/user/6791944931428/post/nYFnj", unpacked=None)
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, "Bluejuicyjuice\\18 Nidoqueen SFM model by Bluejuicyjuice from Gumroad  Kemono\\NidoSFM.7z")))
        self.KMP.close()     
        
    def test_server_name(self):
        """
        Tests downloading of server name
        """
        # Mp4 and images
        self.KMP = KMP(self.tempdir, unzip=False, tcount=3, chunksz=None, download_server_name_type=True)
        self.KMP.routine("https://kemono.party/fanbox/user/49494721/post/4072005", unpacked=None)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "soso\胡桃Live2Dアニメ by soso from Pixiv Fanbox  Kemono\\d1c15668-08e1-4bea-a1bc-a55d25e59bc3.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "soso\胡桃Live2Dアニメ by soso from Pixiv Fanbox  Kemono\\胡桃_Live2D.mp4")))
        self.KMP.close()     
    
    def test_password_zip(self):
        """
        Tests download and extraction of a password 
        protected zip
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None, download_server_name_type=True)
        self.KMP.routine("https://kemono.party/fanbox/user/262147/post/4062214", unpacked=2)
        self.assertFalse(os.path.exists(os.path.abspath("./") + "クレー計20枚パスワード付zip"))
        self.KMP.close()
    def test_alt_routine(self):
        """
        Tests alternate download for all download types
        """
        self.KMP = KMP(self.tempdir, unzip=True, tcount=3, chunksz=None)
        # All Artist Page
        self.KMP.alt_routine("https://kemono.party/fanbox/user/836862", unpacked=2)
        self.assertEquals(self.getNumFiles(os.path.join(self.tempdir, "tsumikisata")), 544)        
        # Single Artist Page
        self.KMP.alt_routine("https://kemono.party/patreon/user/19467060?o=25", unpacked=2)
        self.assertEquals(self.getNumFiles(os.path.join(self.tempdir, "katecavanaugh")), 86)        
       
        # Single Artist Work
        self.KMP.alt_routine("https://kemono.party/patreon/user/169359/post/27626311", unpacked=2)
        self.assertEquals(self.getNumFiles(os.path.join(self.tempdir, "seductionrl")), 8)        
        
        # Discord Channel
        # TODO
        # Text file
        # TODO
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

    
    def getNumFiles(self, dir:str) -> int:
        """
        Returns the number of files in a directory

        Return number of files in a directory
        """
        return len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])



if __name__ == '__main__':
    unittest.main()
