import glob
import threading #multiprocessing
import os
import shutil
import time
import redis
import json
import serial
import traceback
import atexit
import signal
import sys

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    SerialWorker.r.publish("kill_t1","1")
    SerialWorker.r.publish("kill_t2","1")
    print("NOTIFIED THREADS!!!")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# signal.pause()
@atexit.register
def at_exit():
   print("!@#!@#!@#!@#!@#!@#!@#!@#!@#!@#!@#")


class SerialAltimeterWorker:
    def __init__(self):
        print("INIT SERIAL ALTIMETER WORKER!@#")
        self.main_loop_real()


    def get_reading(self,conn):
        return conn.get_reading()
#        return {
#            "altitude_ground": "ASDASD", #random.uniform(1000, 2000),
#        }
    def main_loop(self):
        while True:
            reading = self.get_reading(None)
            GPSWorker.update_redis_reading(reading)
            time.sleep(0.1)

    def main_loop_real(self):
        from altimeter_ser import AltimeterSer
        print("STARTING SERIAL ALTIMETER MAIN LOOP!!@#")
        pub = SerialWorker.r.pubsub()
        pub.subscribe("kill_t1")
        while True:
            print("LOOP altimeter1")
            msg = pub.get_message(ignore_subscribe_messages=1) #get_message(ignore_subscribe_message=True)
            if msg:
               print("\n\nKILLING LOOP ALTIMETER OUTTER!!!\n\n")
               if msg['channel'] == "kill_t1":
                   sys.exit(0)
            try:
                 devices = json.loads(SerialWorker.r.get("devices")) # ==  "connected":
            except:
                 devices = {'gps':'disconnected', 'altimeter':'disconnected', 'usb':'disconnected'}
            print("altimeter DEVICES:",devices)
            if devices.get("altimeter") ==  "connected":
                print("ALTIMETER CONNECTED!")
                try:
                    conn = AltimeterSer("/dev/altimeter")
                    time.sleep(0.1)
                    print("OPENED ALTIMETER!!!")
                except:
                    traceback.print_exc()
                    print("DID NOT OPEN ALTIMETER!!")
                    time.sleep(0.7)
                    continue
                while True:
                    msg = pub.get_message(ignore_subscribe_messages=1) #get_message(ignore_subscribe_message=True)
                    if msg:
                        if msg['channel'] == "kill_t1":
                            print("\n\nKILLING LOOP ALTIMETER OUTTER!!!\n\n")
                            sys.exit(0)
                    try:
                        reading = self.get_reading(conn)
                    except:
                        print("ERROR GETTING READING!")
                        reading = None
                    print("GOT ALTIMETER READING!@#",reading)
                    if not reading:
                        print("CLOSED!!!")
                        conn.close()
                        time.sleep(0.1)
                        break
                    GPSWorker.update_redis_reading(reading)
                    time.sleep(0.5)
            GPSWorker.update_redis_reading({"altitude_ground":""})
            print("Seeee if we are open again?")
            time.sleep(1)


class GPSWorker:
    @staticmethod
    def start():
        GPSWorker()
    def __init__(self):
        from gps_ser import log
        log.warn("INIT GPS WORKER?")
        self.main_loop_real()

    def get_reading(self,conn):
        return conn.get_reading()
    def get_reading_fake(self,conn):
        return {
                "gps_update":time.time(),
                "altitude_sealevel":"BBBOB", #random.uniform(1000,2000),
                "latitude": "5",
                "longitude": "-2",
                "last_update": time.time()
            }

    def main_loop_fake(self):
        while True:
            reading = self.get_reading_fake(None)
            GPSWorker.update_redis_reading(reading)
            time.sleep(0.1)
    def read_forever(self,conn,pub):
        while True:
            msg = pub.get_message(ignore_subscribe_messages=1) #get_message(ignore_subscribe_message=True)
            if msg:
               print("KILL GPS INNER!!")
               if msg['channel'] == "kill_t2":
                   sys.exit(0)

            try:
                reading = self.get_reading(conn)
            except:
                reading = None
            if not reading:
                conn.close()
                time.sleep(0.1)
                return
            GPSWorker.update_redis_reading(reading)
            time.sleep(0.5)
    # def check_exists(self):
    #     if os.name == "nt":
    #         try:
    #             data = json.loads(SerialWorker.r.get("devices"))
    #         except:
    #             return False
    #         return data['gps'] == "connected"
    #     return os.path.exists("/dev/gps")
    def main_loop_real(self):
        from gps_ser import GPSSerial,log
        log.warn("START LOOP")
        pub = SerialWorker.r.pubsub()
        pub.subscribe("kill_t2")
        while True:
            msg = pub.get_message(ignore_subscribe_messages=1) #get_message(ignore_subscribe_message=True)
            if msg:
               print("KILL GPS OUTTER!!!")
               if msg['channel'] == "kill_t2":
                   sys.exit(0)
            try:
                devices = json.loads(SerialWorker.r.get('devices'))
            except:
                devices = {'gps':'disconnected'}
            log.warn("DEV: %r"%(devices,))
            if devices['gps'] == 'connected' or os.name == "nt":
                log.warn("OPEN SERIAL")
                try:
                    if os.name == "nt":
                        conn = GPSSerial("COM4")
                    else:
                        conn = GPSSerial("/dev/gps")
                    time.sleep(0.1)
                    log.warn("CONNECTED: %r"%(conn,))
                except:
                    # logging.getLogger("gps_raw").exception("CONNECTION ERROR!")
                    time.sleep(0.2)
                    log.exception("Could not open PORT")
                    if os.name == "nt":
                        devices.update({'gps':'disconnected'})
                        print("SET DEVICES:",devices)
                        SerialWorker.r.set('devices',json.dumps(devices))
                else:
                    if devices['gps'] == "disconnected":
                        devices.update({'gps': 'connected'})
                        print("SET DEVICES:", devices)
                        SerialWorker.r.set('devices', json.dumps(devices))
                    self.read_forever(conn,pub)
            self.update_redis_reading({"altitude_sealevel":"","num_satellites":"-1","satellites_signal":"-1"})
            time.sleep(1)

    @staticmethod
    def update_redis_reading(reading):
        # print("UPDATE:",reading)
        data = SerialWorker.get_current_reading() or {}
        data.update(reading)
        SerialWorker.r.set("reading_data",json.dumps(data))
def start_gps():
    GPSWorker.start()
def start_altimeter():
    SerialAltimeterWorker()

class SerialWorker:
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    def __init__(self):
        # construct python-redis interface
        self.p = self.r.pubsub()
        print(self.r.config_set("appendonly","no"))
        print(self.r.config_set("save",""))

        self.p.subscribe("kill")
        self.p.subscribe("download")
        # create and pass data to redis
        self.set_current_reading({})
        self.r.set("gps","disconnected")
        self.r.set('altimeter',"disconnected")
        self.main_loop()
    def download_logs(self,copyTo="/mnt/usb"):
        from gps_ser import log
        from altimeter_ser import log as alog
        # log = logging.getLogger("gps_raw")
        # alog = logging.getLogger("altimeter_errors")
        final_path = os.path.join(copyTo,"logfiles")
        shutil.rmtree(final_path,True)
        os.makedirs(final_path)
        for fname in glob.glob("/logfiles/*"):
            shutil.copy2(fname,final_path)
            try:
                os.remove(fname)
            except:
                print("CANNOT REMOVE %s"%fname)

    def main_loop(self):
        p1 = threading.Thread(target=start_altimeter)
        p2 = threading.Thread(target=start_gps)
        p1.start()
        p2.start()
        print("PRocesses STARTED")
        while True:
            msg = self.p.get_message(ignore_subscribe_messages=1)
            if msg:
                print("GOT MSG!!!", msg)
                if msg['channel'] == "kill":

#                    p1.terminate()
#                    p2.terminate()
                    p1.join()
                    p2.join()
                    break
                elif msg['channel'] == "download":
                    self.download_logs(msg['data'])
            self.update_device_states()
            self.refresh_current_reading()
            time.sleep(0.5)
            # print("DATA:",self.data)
        print("Exiting Serial Worker ... should automatically restart if configured")
    def update_device_states(self):
        self.r.set('download_count', len(glob.glob("/logfiles/*.csv")))
        if os.name == "nt":
            return
        try:
            states = json.loads(self.r.get("devices"))
        except:
            states = {'gps':'disconnected','altimeter':'disconnected','usb':'disconnected'}
        if states.get('gps','') != 'connected':
            if os.path.exists('/dev/gps'):
                states.update({'gps':'connected'})
                self.r.set('devices',json.dumps(states))
        else:
            if not os.path.exists('/dev/gps'):
                states.update({'gps':'disconnected'})
                self.r.set('devices', json.dumps(states))
        if states.get('altimeter','') != 'connected':
            if os.path.exists("/dev/altimeter"):
                states.update({'altimeter':'connected'})
                self.r.set('devices',json.dumps(states))
        else:
            if not os.path.exists('/dev/altimeter'):
                states.update({'altimeter':'disconnected'})
                self.r.set('devices',json.dumps(states))
        if states.get('usb','') != "connected":
            if len(glob.glob("/dev/sd*")) > 0:
                states.update({'usb':'connected'})
                self.r.set('devices',json.dumps(states))
        else:
            if len(glob.glob("/dev/sd*")) < 1:
                states.update({'usb': 'disconnected'})
                self.r.set('devices',json.dumps(states))
        print("DEVICE STATES UPDATED:",states)

    @staticmethod
    def addDevices(altimeter=None,gps=None,usb=None):
        try:
            data = json.loads(SerialWorker.r.get('devices'))
        except:
            data = {}
        if altimeter is not None:
            new_data = {'altimeter':altimeter}
        else:
            new_data = {}
        if gps is not None:
            new_data.update({'gps':gps})
        if usb is not None:
            new_data.update({'usb':gps})
        data.update(new_data)
        SerialWorker.r.set('devices',json.dumps(data))
    def set_current_reading(self,data):
        self.data = data
        GPSWorker.update_redis_reading(self.data)
    @staticmethod
    def kill():
        SerialWorker.r.publish("kill", 1)
    def refresh_current_reading(self):
        self.data = self.get_current_reading()

    @staticmethod
    def get_current_reading():
        try:
            return json.loads(SerialWorker.r.get('reading_data'))
        except:
            return {}


if __name__ == "__main__":
    SerialWorker()
