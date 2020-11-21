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
    def __init__(self,port="/dev/urad"):
        global log
        log = logging.getLogger("urad_logger")
        log.setLevel(logging.DEBUG)
        log.addHandler(RotatingFileHandler("/logfiles/urad_log.txt", maxBytes=50000, backupCount=1))
        log.addHandler(logging.StreamHandler())
        self.ser = serial.Serial(port,1e6)
        self.cfg = {}
        self.__do_configure()
    def get_reading(self):
        ret_code,results,raw_results = URAD.detection(self.ser)
        nTar = results[0]
        altitude = results[1][0]
        vel  = results[2][0]
        snr  = results[3][0]
        return {"altitude_ground":altitude,"speed_ground":vel,"snr_ground":snr}
    def read_forever(self,callback, delay=0.25):
        while True:
            callback(self.get_reading())
            time.sleep(delay)

    def __do_load_user_config_variables(self,fpath="/boot/urad_config.txt"):

        data = {"Ns": 200, "mode": 2, "BW": 240, "f0": 5, "Ntar": 3, "Rmax": 100, "MTI": 0, "Mth": 0, "Alpha": 10,
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
            log.info("Loaded CFG : %s"%(pprint.pformat(cfg)))
            return cfg
        except:
            log.exception("Error loading config: %r"%fpath)
            return data

    def __do_configure(self):
        self.cfg = self.__do_load_user_config_variables("/boot/urad_config.txt")
        URAD.loadConfiguration(self.ser,**self.cfg)
        URAD.turnON(self.ser)

def test():
    def handle_reading(reading):
        print("GOT READING:",reading)
    AltimeterUradSer().read_forever(handle_reading)
