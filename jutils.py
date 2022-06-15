import io
import os

"""
Misc helpful utils, mainly related to File IO

@author Jeff Chen
@version 6/15/2022
"""

def write_utf8(self, text:str, path:str, mode:str) -> None:
    """
    Writes utf-8 text to a file at path

    Param:
        text: text to write
        path: where file to write to is located including file name
        mode: mode to set FIle IO
    """
    with io.open(path, mode=mode,  encoding='utf-8') as fd:
        fd.write(text)

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