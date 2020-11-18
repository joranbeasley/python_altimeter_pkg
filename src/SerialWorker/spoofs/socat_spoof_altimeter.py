import struct
import sys
import serial
import os
import subprocess
import time
#sudo socat PTY,link=/dev/ttyS10 PTY,link=/dev/ttyS11
proc = subprocess.Popen(["/usr/bin/socat","PTY,link=/dev/ttyS_ALT","PTY,link=/dev/altimeter"])
def resolve_path(fname):
     try:
        from pathlib import Path
        return Path(fname).resolve()
     except:
        return os.path.realpath(fname)
time.sleep(1.0)
real_path = resolve_path("/dev/ttyS_ALT")
real_path2 = resolve_path("/dev/altimeter")

os.system("chmod 664 %s"%(real_path))
os.system("chmod 664 %s"%(real_path2))
os.system("chown root:dialout %s"%(real_path))
os.system("chown root:dialout %s"%(real_path2))
print("START!")
s = serial.Serial("/dev/ttyS_ALT")
print("OPENED??")
import random
while True:
    
    val = struct.pack(">i",random.uniform(110,120)*100)
    #time.sleep(10)
    # msg = "\x13as\x33\xca\xcb\xcc\xcdJUNKJUNK\x07P\x04fzsdJUNKJUNK\xea\xeb\xec\xed"
    msg = "\x13as\x33\xca\xcb\xcc\xcd\x07T\x04JUNK\x07Q\x04JUNK\x07P\x04%sJUNKJUNK\xea\xeb\xec\xed"%val
    s.write(msg)
    time.sleep(0.25)
#
#while True:
#    s.write(msg)
