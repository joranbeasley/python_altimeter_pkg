import operator
import re
import struct
import sys
import serial
import os
import subprocess
import time
#sudo socat PTY,link=/dev/ttyS10 PTY,link=/dev/ttyS11
proc = subprocess.Popen(["/usr/bin/socat","PTY,link=/dev/ttyS_GPS","PTY,link=/dev/gps"])
def resolve_path(fname):
     try:
        from pathlib import Path
        return Path(fname).resolve()
     except:
        return os.path.realpath(fname)
print("waiting for ports to spawn")
while not os.path.exists("/dev/ttyS_GPS") or not os.path.exists("/dev/gps"):
    time.sleep(0.1)
real_path = resolve_path("/dev/ttyS_GPS")
real_path2 = resolve_path("/dev/gps")
print("Fix permissions and ownership")
os.system("chmod 664 %s"%(real_path))
os.system("chmod 664 %s"%(real_path2))
os.system("chown root:dialout %s"%(real_path))
os.system("chown root:dialout %s"%(real_path2))
print(os.popen("ls -la %s"%real_path).read())
print(os.popen("ls -la %s"%real_path2).read())
print("START!")
s = serial.Serial("/dev/ttyS_GPS")
print("OPENED??")
import random

def fix_checksums(s1):
    def calc_cs(s2):
        return "%02X"%reduce(operator.xor,bytearray(s2.strip("*$")))
    def replacer(m):
        return m.group_upd(1) + calc_cs(m.group_upd(1)) + "\r\n"
    return re.sub("(\$GP.*?\*).{2}\r\n",replacer,s1)

while True:
    height = random.uniform(120,125)
    #time.sleep(10)
    #46.73127 -
    ctime = time.strftime("%H%M%S")
    cdate = time.strftime("%d%m%y")
    msg = """$GPRMC,%s,V,46.73127,n,117.17962,w,2.3,25.7,%s,,,N*47\r\n$GPGGA,%s,,,,,0,00,,%s,M,12.2,M,,0000*5B\r\n$GPGSV,3,1,09,17,73,039,12,19,69,046,14,02,53,178,14,12,52,306,16*74\r\n$GPGSV,3,2,09,24,43,234,,06,24,045,,32,03,319,,05,02,148,*77\r\n$GPGSV,3,3,09,28,01,117,*4C\r\n"""%(
     ctime,cdate,ctime,
     height
    )
    # msg = "\x13as\x33\xca\xcb\xcc\xcdJUNKJUNK\x07P\x04fzsdJUNKJUNK\xea\xeb\xec\xed"
#    msg = """$GPGRM,"""%val
    m2 = fix_checksums(msg)
#    import pdb;pdb.set_trace()
    s.write(m2)
    time.sleep(0.25)
#
#while True:
#    s.write(msg)

