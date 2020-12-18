import io
import struct
import sys

import serial
from utils import read_frame, getNBITS

import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
log = None
class AltimeterSer:
    def close(self):
        self.conn.close()
    def __init__(self,port):
        global log
        log = logging.getLogger("altimeter_errors")
        log.setLevel(logging.DEBUG)
        log.addHandler(RotatingFileHandler("/logfiles/smartmicro.log", backupCount=1, maxBytes=25000))
        log.addHandler(StreamHandler(sys.stdout))
        if port is not None:
            if port.startswith("SPOOF:"):
                self.conn = io.BytesIO(port[6:])
                log.warning("Instanciated fake spoofed altimeter data")
            else:
                try:
                    self.conn = serial.Serial(port,115200,timeout=1)
                except:
                    log.exception("Failed to open com! %r"%port)
                    raise
                else:
                    log.warn("\n\nOpened (SM)Altimeter Port: %r\n\n"%self.conn)
        else:
            log.warn("You must set inst.conn before calling get_reading!!!")

    def _getRawPayload(self):
        start_token = "\xca\xcb\xcc\xcd"
        end_token = "\xea\xeb\xec\xed"
        return read_frame(self.conn,start_token,end_token,log=log)

    @staticmethod
    def _unpackRawPayload(rawBytesPayload):
        def __find_section(flag=0x750):
            def ___next_section(tmp):
                return  struct.unpack(">hb", tmp[:3]), tmp[3:]
            section,tmp = ___next_section(rawBytesPayload)
            while section[0] != flag:
                section, tmp =___next_section(tmp[section[1]:])
            return tmp[:section[1]][::-1]
        ALTITUDE_SECTION_FLAG=0x750
        altitude_section = __find_section(ALTITUDE_SECTION_FLAG)
        return getNBITS(22, altitude_section) * 0.01

    def get_reading(self):
        self.conn.flush()
        try:
            raw = self._getRawPayload()
        except AssertionError:
            log.exception("Error parsing Payload")
            return {'altitude_ground': float('nan'),'speed_ground':float("nan"),"snr_ground":float("nan")}
        try:
            result = {'altitude_ground':self._unpackRawPayload(raw),'speed_ground':float("nan"),"snr_ground":float("nan")}
            log.debug("RESULT FROM SmartMicro: %r"%result)
            return result
        except struct.error as e:
            log.exception("Unable to unpack malformed payload: %r"%(raw,))
            return {'altitude_ground':float('nan'),'speed_ground':float("nan"),"snr_ground":float("nan")}


if __name__ == "__main__":
    def encode(value):
        msg = '\x07P\x04%s'%(struct.pack('i',int(value*100))[::-1])
        return msg
    a = AltimeterSer("SPOOF:\x13as\x33\xca\xcb\xcc\xcdaa\x04JUNKbb\x04JUNK%s\xea\xeb\xec\xed"%encode(5521.2))
    print a.get_reading()
