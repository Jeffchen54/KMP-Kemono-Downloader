import logging
import os
import shutil
import tempfile
import patoolib
from patoolib import util
import sys

import jutils
"""
Extracts files using patoolib

@author Jeff chen
@version 6/15/2022
"""

def supported_zip_type(fname:str) -> bool:
        """
        Checks if a file is a zip file (7z, zip, rar)

        Param:
            fname: zip file name or path
        Return True if zip file, false if not
        """
        file = fname.rpartition('/')[2]
        extension = file.rpartition('.')[2]
        return 'zip' == extension or 'rar' == extension or '7z' == extension
        
def extract_zip(zippath: str, destpath: str, temp:bool) -> None:
        """
        Extracts a zip file to a destination. Does nothing if file
        is password protected. Zipfile is deleted if extraction is 
        successful
        
        Cases: 
            (1) Unzip directory does not exists ->  Extract to directory
            (2) Unzip directory exists but size does not match extracted dir -> Extracted dir prepended with (#)
            (3) Unzip directory exists and size matches -> Counted as duplicate and skips unzip directory
            (4) Extracted files conflict with existing files -> Same as case 2
        # Unzip directory refers to directories within a zip folder, for example
        test.zip
            -> animals
            -> dog1.jpg
            -> cat1.png
            
            animals is a directory, this is an unzip directory

        Param:
        unzip: full path to zip file included zip file itself
        destpath: full path to destination
        temp: True to extract to a temp dir then moving the files to destpath, false to extract
            directly to destpath. TODO implement.
        Pre: Is a zip file, can be checked using supported_zip_type(). destpath exists
        """
        destpath += '\\'
        backup_destpath = destpath
        
        # A tempdir is used to bypass Window's 255 char limit when unzipping files
        with tempfile.TemporaryDirectory(prefix="temp") as dirpath:
            dirpath += '\\'
            try:
                patoolib.extract_archive(zippath, outdir=dirpath + '\\', verbosity=-1, interactive=False)

                for f in os.listdir(dirpath):
                    if os.path.isdir(os.path.abspath(dirpath + f)):
                        # Duplicate file name handler
                        downloaded = False
                        while not downloaded:
                            try:
                                shutil.copytree(os.path.abspath(dirpath + f), os.path.abspath(destpath + f), dirs_exist_ok=False)
                                downloaded = True
                            except FileExistsError as e:
                                # If duplicate dir is found, it will be stashed in the same dir but with (n) prepended 
                                counter = 1
                                nextName = e.filename
                                currSz = jutils.getDirSz(os.path.abspath(dirpath + f.replace("\\", "")))
                                # Check directory size of dirpath vs destpath, if same size, we are done
                                done = False
                                while(not done):
                                    # If the next directory does not exists, change destpath to that directory
                                    if not os.path.exists(nextName):
                                        destpath = nextName
                                        done = True
                                    else:
                                        # If directory with same size is found, we are done
                                        dirsize = jutils.getDirSz(nextName)
                                        if dirsize == currSz:
                                            done = True
                                            downloaded = True
                                    
                                    # Adjust path for next iteration
                                    if not done:
                                        nextName = destpath + '(' + str(counter) + ')'
                                        counter += 1

                                # Move files from dupe directory to new directory
                        shutil.rmtree(os.path.abspath(dirpath + f), ignore_errors=True)
                        
                    else:
                        shutil.copy(os.path.abspath(dirpath + f), os.path.abspath(destpath + f))
                        os.remove(os.path.abspath(dirpath + f))
                    
                    # Reset destpath as it may have been modified due to dupe files
                    destpath = backup_destpath

                os.remove(zippath)
            except util.PatoolError as e:
                logging.critical("Unzipping a non zip file has occured, failure is described below:" +
                                "\n + ""File name: " + zippath + "\n" + "File size: " + str(os.stat(zippath).st_size))
                logging.critical(e)
                d = os.listdir(destpath)
                if len(d) == 0:
                    os.rmdir(destpath)
            except RuntimeError:
                logging.debug("File name: " + zippath + "\n" +
                            "File size: " + str(os.stat(zippath).st_size))

def main():
    if supported_zip_type(sys.argv[1]):
        extract_zip(os.path.abspath(sys.argv[1]), os.path.abspath("./testing") + '\\', True)
    else:
        print("Is not ZIP -> " + sys.argv[1])
if __name__ == "__main__":
    main()