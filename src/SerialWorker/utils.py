import struct
from logging.handlers import RotatingFileHandler

import serial
from math import ceil
import logging
ffmt = logging.Formatter("%(asctime)s :: %(message)s")
sfmt = logging.Formatter("%(name)s :: %(message)s")
def initHandlers(logger,filename,maxBytes=50000,backupCount=1):
    # sh = logging.StreamHandler()
    fh = RotatingFileHandler(filename,maxBytes=maxBytes,backupCount=backupCount)
    # sh.setFormatter(sfmt)
    fh.setFormatter(ffmt)
    # logger.addHandler(sh)
    logger.addHandler(fh)
    sh = None
    return sh,fh
def getNBITS(n,msg):
    '''

    >>> bin(getNBITS(3,'\\x13'))
    '0b11'
    >>> bin(getNBITS(22,'\\x13\\x14\\x22\\x33'))
    '0b1000100001010000010011'

    :param n: number of bits to parse
    :param msg:
    :return:
    '''
    struct_map = ["","b","h","i","i","q","q","q","q"]
    struct_use = struct_map[int(ceil(n/8.0))]
    print("S:",struct_use,msg)
    return struct.unpack_from(struct_use, msg)[0] & (2**n-1)
def read_frame(c,start_token,end_token,size=None,log=None):
    """
    return the bytes between the start
    >>> import io
    >>> read_frame(io.BytesIO("JUNK\x12\x13\x14\x15HELLO WORLD\xe5\xe6\xe7\xe8JUNK"),
    ...                       start_token="\x12\x13\x14\x15",end_token="\xe5\xe6\xe7\xe8")
    'HELLO WORLD'
    >>> read_frame(io.BytesIO("JUNK\x12\x13\x14\x15HELLO WORLD\xe5\xe6\xe7\xe8JUNK"),
    ...                       start_token="\x12\x13",end_token="\xe7\xe8")
    '\\x14\\x15HELLO WORLD\\xe5\\xe6'

    :param c:
    :param start_token:
    :param end_token:
    :return:
    """
    msg0 = read_until(c,start_token,size,exceptOnSize=True)
    msg1 = read_until(c,end_token,size,exceptOnSize=True)[:-len(end_token)]
    if(log):
        log.debug("Read JUNK: %r"%msg0)
        log.debug("RAW FRAME: %r"%msg1)
    return msg1

def read_until(conn, terminator='\n', size=None,exceptOnSize=False):
    """
    Read until a termination sequence is found ('\n' by default), the size
    is exceeded or until timeout occurs.
    """
    lenterm = len(terminator)
    line = bytearray()
    timeout = serial.Timeout(getattr(conn,"_timeout",1))  # conn._timeout)
    while True:
        c = conn.read(1)
        if c:
            line += c
            if line[-lenterm:] == terminator:
                break
            if size is not None and len(line) >= size:
                if not exceptOnSize:
                    break
                else:
                    raise AssertionError("token %r not found in %r"%(terminator,line))
        else:
            if not exceptOnSize:
                break
            else:
                raise AssertionError("token %r not found in %r" % (terminator, line))

        if timeout.expired():
            break
    return bytes(line)
