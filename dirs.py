from functools import reduce
import sys

"""
Small Windows->Python directory converter class
"""
def convert_win_to_py_path(winpath:str) -> str:
    """
    Converts a windows file path using "\" into /
    
    Param:
        winpath: Windows path to convert into python
    Return python path
    """
    repls = ("\\", '/'), 
    return reduce(lambda a, kv: a.replace(*kv), repls, winpath)

def replace_dots_to_py_path(dotspath:str) -> str:
    """
    Converts . and .. paths into absolute paths.
    '/' is not appended to the end of the paths.
    Path after . or .. are not modified

    Param: 
        dotspath: Path containing . or ..
    Return converted path using '/'
    """
    # Break up dotspath to get only the beginning portion
    p = dotspath.partition('/')

    # Convert to / first
    pypath = convert_win_to_py_path(sys.path[0])

    repls = ('..', pypath.rpartition('/')[0]), ('.', pypath),
    return reduce(lambda a, kv: a.replace(*kv), repls, p[0]) + p[1] + p[2]

