import struct
import serial
import logging
from logging.handlers import RotatingFileHandler
mode = 3
bw=100 # bandwidth
f0=100 # ramp frequency
Ns = 200 # max_theoretical_dist = 75 * Ns/bw
NTAR = 2 # track at most two targets
rangeMAX =100 # max range to look for targets (max is 100)
MTI = 0 # moving targets? 0=disabled 1=enabled
Mth = 0 # sensitivity for large object detection (1=low...4=highest) # 0 unused if MTI is 0
Alpha = 23 # Alpha help with target identification 3=high...25=lowest


def get_config_array(mode,f0,bw,Ns,NTAR,rangeMAX,MTI,Mth,Alpha):
    return [
        ((mode<<5) + (f0>>3))&0xFF,
        ((f0<<5) + (bw >> 3)) & 0xFF,
        ((bw<<5) + (Ns >> 3)) & 0xFF,
        ((Ns<<5) + (NTAR << 2) + (rangeMAX >> 6)) & 0xFF,
        (((rangeMAX&0b111111)<<2) + MTI) & 0xFF,
        (((Mth << 6) + (Alpha << 1)) & 0b11111111) + 0b00000001,
        0b11100100 #flag get alt,vel,snr, and mov
    ]
# print get_config(mode,f0,bw,Ns,NTAR,rangeMAX,MTI,Mth,Alpha)

class AltimeterSer2:
    def __init__(self,port):
        self.log = logging.getLogger("alt_urad")
        self.log.addHandler(RotatingFileHandler("/logfiles/urad.log",maxBytes=500000,backupCount=1))
        self.log.addHandler(logging.StreamHandler())
        try:
            self.ser = serial.Serial(port)
        except:
            self.log.exception("Unable To Open Port %r"%port)
            raise
        self.enable()
        self.set_config()
    def enable(self):
        self.ser.write("\x10")
        self.log.info("Wrote 0x10 to Device(enable)")
        resp = self.ser.read()
        self.log.info("Device Response: %r" % resp)
        resp = ord(resp)
        if resp != 0xAA:
            self.log.warn("WARN: bad acknowledgement expected 0xAA got %s "%hex(resp))
    def disable(self):
        self.ser.write("\x11")
        self.log.info("Wrote 0x11 to Device(disable)")
        resp = self.ser.read()
        self.log.info("Device Response: %r"%resp)
        resp = ord(resp)
        if resp != 0xAA:
            self.log.warn("WARN: bad acknowledgement expected 0xAA got %s " % hex(resp))
    def set_config(self):
        payload = bytearray(get_config_array(3, 100, 100, 200, 1, 100, 0, 0, 12))
        cs = chr(sum(payload) & 0xFF)
        payload = b"\x0E"+payload+cs
        self.ser.write(payload)
        self.log.info("WROTE CONFIG PAYLOAD: %r"%payload)
        resp = self.ser.read()
        self.log.info("RECV: %r"%resp)
        resp = ord(resp)
        if resp != 0xAA:
            self.log.warn("WARN: bad acknowledgement expected 0xAA got %s " % hex(resp))

    def get_reading(self):
        self.ser.write(b"\x0F")
        self.log.info("Request Reading: '\x0f'")
        results = self.ser.read(62)
        self.log.info("RAW: %r"%results)
        result = struct.unpack("<10f5IBB", )
        self.log.info("UNPACKED: %r"%results)
        self.log.info("---- end read ---")
        results = list(zip(*[result[i:i + 5] for i in range(0, 14, 5)]))
        return dict(zip(["altitude_ground", "velocity_ground", "radar_signal"], results[0]))

    def close(self):
        self.disable()
        self.ser.close()
        self.log.info("PORT CLOSED!")
