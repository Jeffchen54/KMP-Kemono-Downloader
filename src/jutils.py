import io
import os

"""
Misc helpful utils, mainly related to File IO

@author Jeff Chen
@version 6/15/2022
"""

def write_utf8(text:str, path:str, mode:str) -> None:
    """
    Writes utf-8 text to a file at path

    Param:
        text: text to write
        path: where file to write to is located including file name
        mode: mode to set FIle IO
    """
    with io.open(path, mode=mode,  encoding='utf-8') as fd:
        fd.write(text)


def write_to_file(path:str, line: str, mutex) -> None:
    """
    Appends to a file, creates the file if it does not exists

    Param:
        path: file to write to, absolute path 
        line: line to append to file
        mutex: (Optional) mutex lock associated with the file
    """
    if mutex:
        mutex.acquire()

    write_utf8(line, path, 'a')
    #if not os.path.exists(path):
    #    open(path, 'a').close()

    #with open(fname, "a") as myfile:
    #    myfile.write(line)


    if mutex:
        mutex.release()


def getDirSz(dir: str) -> int:
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