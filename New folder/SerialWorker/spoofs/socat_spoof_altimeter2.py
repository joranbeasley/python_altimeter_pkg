import struct
import sys
import serial
import os
import subprocess
import time
import random
from spoofs_util import linux_start_port_spoof_bridge
#sudo socat PTY,link=/dev/ttyS10 PTY,link=/dev/ttyS11
if os.name == "nt":
    print("SPOOF PORT REQUIRED ON WINDOWS")
    spoofPort = sys.argv[1]
    print ("GOT SPOOF PORT:",spoofPort)
else:
    spoofPort = "/dev/ttyS_ALT2"
    targetPort = "/dev/altimeter2"
    spoofProc = linux_start_port_spoof_bridge(spoofPort,targetPort)

print("START!")
class SpoofURAD:
    def __init__(self,spoofPort):
        self.state = {'on':"off",'distance':98.2, 'velocity':22.1}
        self.ntar = 1
        self.mode = 0
        self.f0 = 0
        self.bw = 0
        self.ns = 0
        self.rmax = 0
        self.mti = 0
        self.mth = 0
        self.alpha = 0
        self.config_flags = 0
        self.ser = serial.Serial(spoofPort,timeout=1)

    def turn_on(self,state="on"):
        print("UPDATE STATE:",state)
        self.state.update({'on':state})
        self.ser.write("\xAA")
    def config_str(self):
        return "<CFG mode=%s f0=%s bw=%s ns=%s ntar=%s rangeMax=%s mti=%s mth=%s alpha=%s flags=%s />"%(
            self.mode,self.f0,self.bw, self.ns,self.ntar,self.rmax,self.mti,self.mth,self.alpha,
            bin(self.config_flags)[2:].zfill(8)
        )
    def set_config(self,msg):
        DIST_TRUE=0b10000000
        VELO_TRUE=0b01000000
        SNR_TRUE =0b00100000
        I_TRUE   =0b00010000
        Q_TRUE   =0b00001000
        MOV_TRUE =0b00000100
        if not isinstance(msg,bytearray):
            msg = bytearray(msg)
        print("Configure PORT: %r"%msg)
        checksum = sum(msg[:-1])&0xFF
        if msg[-1] != checksum:
            print "CHECKSUM FAILED: MSG: %r CALCULATED %r, but MSG INDICATES %r"%(msg,checksum,msg[-1])
            self.ser.write("\xAB")
        else:
            print "CS PASSED: %r"%(msg)
            self.mode = (msg[0] >> 5) & 0xFF
            self.f0 = (((msg[0] & 0b11111) << 3) + (msg[1] >> 5)) & 0xFF
            self.bw = (((msg[1] & 0b11111) << 3) + (msg[2] >> 5)) & 0xFF
            self.ns = (((msg[2] & 0b11111) << 3) + (msg[3] >> 5)) & 0xFF
            self.ntar = ((msg[3] & 0b11111) >> 2) & 0xFF
            self.rmax = (((msg[3] & 0b11) << 6) + (msg[4] >> 2)) & 0xFF
            self.mti = msg[4] & 0b11
            self.mth = (msg[5] >> 6)
            self.alpha = (msg[5] >> 1) & 0b11111
            self.config_flags = msg[6]
            self.ser.write("\xAA")
            print "CFG:", self.config_str()

    def detect(self):
        results_packetLen = 5 * 3 * 4 + 2
        distance = struct.pack("<5f",*[self.state['distance']+random.uniform(-1,1) for _ in range(5)])
        velocity = struct.pack("<5f",*[self.state['velocity']+random.uniform(-1,1) for _ in range(5)])
        snr = struct.pack("<5I",*[random.randint(20,60) for _ in range(5)])
        I_TRUE = 0b00010000
        Q_TRUE = 0b00001000
        IQ_PACKETS = ""
        if self.config_flags & (I_TRUE|Q_TRUE):
            IQ_PACKETS = ""
            pass
        result = distance+velocity+snr + '\xFF' + IQ_PACKETS + '\x00'
        print("L",len(result))
        self.ser.write(result)

    def main_loop(self):
        ENABLE='\x10'
        DISABLE='\x11'
        CONFIG='\x0E'
        DETECT='\x0F'

        while True:
            msg = self.ser.read(1)
            if not msg:
                sys.stdout.write(".")
                continue
            print("handle message %r"%msg)
            def ERROR():
                print("ERROR UNKNOWN CMD: %r... SKIP" % (msg,))
            handler = {
                ENABLE:lambda:self.turn_on("on"),
                DISABLE:lambda:self.turn_on("off"),
                CONFIG:lambda:self.set_config(bytearray(self.ser.read(8))),
                DETECT:lambda:self.detect()
            }.get(msg,ERROR)()
print("OPENED??")
SpoofURAD(spoofPort).main_loop()#


