
import logging
import os
import time
import requests
from tqdm import tqdm
from ssl import SSLError

class Error(Exception):
    """Base class for other exceptions"""
    pass
class MissingContentLengthException(Error):
    """ Raised when a response lacks content-length"""
    pass

def download(downloader:any, headers, url:str, fname:str, display_bar:str, retry_codes:list[int], timeouts:int, chunksz:int,
             retry_delay:int):
    """
    Downloads a file using a GET request

    Args:
        downloader (any): downloader to use
        url (str): url to download from
        fname (str): File name to download as, includes path and ext
        display_bar (str): Displays a progress bar labeled with provided argument
        retry_codes (list[int]): HTTP codes to retry on. If not included on the list, will not be retried after occurance.
        timeouts (int): Number of times to retry 'retry_codes'
        chunksz (int): What size chunks should file be downloaded in
    Returns: SUCCESS: None 
             FAILURE: HTTP code
            
    """
    
    done = False
    while not done:
        # Open download stream ######################################################################################
        data = None
        downloaded = 0
        while not data:
            try:
                data = downloader.get(url, stream=True, timeout=5, headers=headers)
                
                # Check if request was successful
                if data.status_code in retry_codes:
                    timeouts -= 1
                    
                    # If timeout exceeds or matches max timeouts, is failure
                    if timeouts <= 0:
                        logging.warning("HTTP {} has occured, max timeouts have been met".format(data.status_code)) 
                        return data.status_code
                    # If failed but not max timeouts, report result
                    else:
                        logging.warning("HTTP {} has occured, {} timeouts remaining".format(data.status_code, timeouts)) 
                        time.sleep(retry_delay)
                # If unlisted http code occured, immediately failure
                elif data.status_code >= 400:
                    logging.warning("Untracked HTTP {} has occured, skipping".format(data.status_code))
                    return data.status_code
                
            except(requests.RequestException) as e:
                logging.warning("{} has occured, retrying opening stream".format(e.__class__.__name__))
                time.sleep(retry_delay)

            
            # Get content length
            fullsize = data.headers.get('Content-Length')
            
            # If fullsize is not available, raise exception
            if not fullsize:
                raise MissingContentLengthException
            
            # Download in either the 2 possible ways ###############################################################
            # (1) With display bar
            try:
                if display_bar:
                    with open(fname, "wb") as fd, tqdm(
                                        desc=fname,
                                        total=int(fullsize) - downloaded,
                                        unit='iB',
                                        unit_scale=True,
                                        leave=False,
                                        bar_format= display_bar + " " + "({})".format(fname) + " -> [{bar}{r_bar}]",
                                        unit_divisor=int(1024)) as bar:
                        for chunk in data.iter_content(chunk_size=chunksz):
                            sz = fd.write(chunk)
                            fd.flush()
                            bar.update(sz)
                            downloaded += sz
                        bar.clear()
                # (2) Without display bar
                else:
                    with open(fname, 'wb') as fd:
                        for chunk in data.iter_content(chunk_size=chunksz):
                            sz = fd.write(chunk)
                            fd.flush()
                            downloaded += sz     
                            
                # File integrity check ###########################################################################
                if(os.stat(fname).st_size < int(fullsize)):
                    logging.warning("{} ({}/{}) not downloaded correctly, restarting download".format(fname, os.stat(fname).st_size, fullsize))
                else:
                    done = True
            except(requests.RequestException) as e:
                logging.warning("{} has occured, retrying download".format(e.__class__.__name__))
                time.sleep(retry_delay)
                
                
                        
                        
def head(downloader:any, headers:tuple, url:str, retry_codes:list[int], timeouts:int, retry_delay:int):
    """
    Gets head of the the url using a GET request

    Args:
        downloader (any): downloader to use
        downloader_req_args: Additional arguments to use in request().
        url (str): url to get head of
        retry_codes (list[int]): HTTP codes to retry on. If not included on the list, will not be retried after occurance.
        timeouts (int): number of times to retry 'retry_codes'
        retry_delay (int): Delay between any kind of retry in seconds
    Returns: SUCCESS: Response
             FAILURE: HTTP code
    """
    
    # Attempt a HEAD request
    req = None
    while not req:
        try:
            req = downloader.request('HEAD', url, timeout=5, headers=headers)
            
            # Check if request was successful
            if req.status_code in retry_codes:
                timeouts -= 1
                
                # If timeout exceeds or matches max timeouts, is failure
                if timeouts <= 0:
                    logging.warning("HTTP {} has occured, max timeouts have been met".format(req.status_code)) 
                    return req.status_code
                # If failed but not max timeouts, report result
                else:
                    logging.warning("HTTP {} has occured, {} timeouts remaining".format(req.status_code, timeouts)) 
                    time.sleep(retry_delay)
            # If unlisted http code occured, immediately failure
            elif req.status_code >= 400:
                logging.warning("Untracked HTTP {} has occured, skipping".format(req.status_code))
                return req.status_code
               
        except requests.RequestException as e:
            logging.warning("{} has occured, retrying download".format(e.__class__.__name__))
            time.sleep(retry_delay)
    
    return req