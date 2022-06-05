
import glob
import logging
import mmap
import os
from zipfile import BadZipFile, ZipFile
import dirs
import sys


def grabFiles(fpath:str, extension:str) -> list[str]:
    """
    Reports all files with the specified extension within a directory

    Param:
        fpath: Directory path to search files in.
        extension: Extention to look for withouit '.'
    Pre:
        fpath uses '/', not '\' and is a valid directory
    Return: List of files with extension, empty list if none found. Files use '/' instead of windows '\\'
    """

    file = glob.glob(fpath + "/*." + extension, recursive=True)
    return dirs.convert_win_to_py_path(file[0])

def findSubstrInDir(dir:str, substr:str) -> list[str]:
    """
    Searches a directory for all text files containing a substring

    Param:
        dir: Directory to look for a text file
        substr: Substring in text file to look for
    Pre: dir uses '/' and ends with '/'
    """

    # Pull up current directory information
    contents = os.scandir(dir)
    txt_files = []

    # Iterate through all elements
    for file in contents:
        # If is txt file, check for substring
        if file.stat().st_size > 0 and "txt" == file.name.rpartition(".")[2]:
            with open(file.path) as f:
                s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                if s.find(substr.encode('utf-8')) != -1:
                    txt_files.append(file.path)
                s.close()
        
        # If is a directory, recursive call into directory and append result
        elif file.is_dir():
            txt_files += findSubstrInDir(file.path + '/', substr)

    # Return result
    return txt_files


def extract_zip(zippath: str, destpath: str) -> None:
    """
    Extracts a zip file to a destination. Does nothing if file
    is password protected.

    Param:
    unzip: full path to zip file included zip file itself
    destpath: full path to destination
    """
    try:
        with ZipFile(zippath, 'r') as zip:
            zip.extractall(destpath)
        os.remove(zippath)
    except BadZipFile:
        logging.critical("Unzipping a non zip file has occured, please check if file has been downloaded properly" +
                            "\n + ""File name: " + zippath + "\n" + "File size: " + str(os.stat(zippath).st_size))
    except RuntimeError:
        logging.debug("File name: " + zippath + "\n" +
                        "File size: " + str(os.stat(zippath).st_size))

def bulk_unzip(dir:str) -> None:
    """
    Given a directory, search it and all subdirectories for any zip files and 
    unzip them. Fails if zip files are password protected

    Param:
        dir: Which directory to search
    Pre: dir uses '/' and ends with '/'
    """
    # Pull up current directory information
    contents = os.scandir(dir)

    # Iterate through all elements
    for file in contents:
        # If is zip file, unzip
        if file.stat().st_size > 0 and "zip" == file.name.rpartition(".")[2]:
           logging.info("Unzipping: " + file.path)
           extract_zip(file.path, file.path.rpartition('/')[0] + "/")
        
        # If is a directory, recursive call into directory and append result
        elif file.is_dir():
            bulk_unzip(file.path + '/')

logging.basicConfig(level=logging.INFO)
fname = sys.argv[1]

if(len(sys.argv) > 1):

    if(len(sys.argv) == 3 and sys.argv[1] == '-v'):
        bulk_unzip(dirs.convert_win_to_py_path(sys.argv[2]) + "/")
    else:
        matches = findSubstrInDir((dirs.convert_win_to_py_path(fname) + "/"), "drive")
        for match in matches:
            print(match)
        matches = findSubstrInDir((dirs.convert_win_to_py_path(fname) + "/"), "mega")
        for match in matches:
            print(match)
        matches = findSubstrInDir((dirs.convert_win_to_py_path(fname) + "/"), "bitly")
        for match in matches:
            print(match)