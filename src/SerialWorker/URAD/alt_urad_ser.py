import pprint

import URADLIB as URAD
import configparser
import serial
import time
import logging
from logging.handlers import RotatingFileHandler
class FakeLog:
    def __getattr__(self, item):
        def print_it(*s):
            print(s)
        return print_it
log = FakeLog()


class AltimeterUradSer:
    log_setup = {'filename':"/logfiles/urad.log",'maxBytes':50000,'backupCount':1}
    def setupLogging(self):
        global log
        log = logging.getLogger("urad_logger")
        log.setLevel(logging.DEBUG)
        handleF = RotatingFileHandler(**self.log_setup)
        handleF.setFormatter(logging.Formatter("%(asctime)s:: %(msg)s"))
        log.addHandler(handleF)
        # handleS = logging.StreamHandler()
        # handleS.setFormatter(logging.Formatter("%(name)s:: %(msg)s"))
        # log.addHandler(handleF)
    def __init__(self,port="/dev/urad",cfg=None):
        global log
        cfg = cfg or {}
        self.setupLogging()
        try:
            self.ser = serial.Serial(port,1e6)
        except:
            log.exception("Failed to open com(urad)! %r"%port)
            raise
        else:
            log.warn("URAD Serial Port Open: %r"%self.ser)
        self.cfg = {}
        self.__do_configure(cfg)
    def close(self):
        URAD.turnOFF(self.ser)
        self.ser.close()

    def get_reading(self):
        ret_code,results,raw_results,raw_bytes = URAD.detection(self.ser)
        log.debug("URAD RESULT?: %r"%(raw_bytes,))
        # log.info("RESULTS2: %r"%(results))
        dist = max([float(v) for v in results[1]])
        return {"altitude_ground":dist,"speed_ground":results[2][0],"snr_ground":results[3][0]}
                   
    def read_forever(self,callback, delay=0.25):
        while True:
            callback(self.get_reading())
            time.sleep(delay)

    def __do_load_user_config_variables(self,fpath="/boot/urad_config.txt"):

        data = {"Ns": 200, "mode": 2, "BW": 120, "f0": 23, "Ntar": 1, "Rmax": 100, "MTI": 0, "Mth": 0, "Alpha": 10,
                "distance_true": True,
                "velocity_true": True, "SNR_true": True, "I_true": False, "Q_true": False, "movement_true": False}
        try:
            cfg = configparser.ConfigParser()
            cfg.read(fpath)
            def convert_or_fallback(key):
                try:
                    return int(cfg['config'][key])
                except:
                    return data[key]
            cfg = {key: convert_or_fallback(key) for key in data}
            # log.info("Loaded CFG : %s"%(pprint.pformat(cfg)))
            return cfg
        except:
            log.exception("Error loading config: %r"%fpath)
            return data
    def reconfigure(self,newCfg):
        self.cfg = self.__do_load_user_config_variables("/boot/urad_config.txt")

        self.cfg.update({k:v for k,v in newCfg.items() if k in self.cfg})
        print("RECONFIG alt_urad.URADSerial:",self.cfg)
        URAD.turnOFF(self.ser)
        URAD.loadConfiguration(self.ser,**self.cfg)
        URAD.turnON(self.ser)
    def __do_configure(self,cfg=None):
        cfg = cfg or {}
        self.cfg = self.__do_load_user_config_variables("/boot/urad_config.txt")
        self.cfg.update(cfg)
        URAD.loadConfiguration(self.ser,**self.cfg)
        URAD.turnON(self.ser)

def test():
    def handle_reading(reading):
        print("GOT READING:",reading)
    AltimeterUradSer().read_forever(handle_reading)
