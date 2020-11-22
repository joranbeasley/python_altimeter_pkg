import glob
import re
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
import argparse
p = argparse.ArgumentParser()
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    SerialWorker.r.publish("kill_t1","1")
    SerialWorker.r.publish("kill_t2","1")
    print("NOTIFIED THREADS!!!")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# signal.pause()
class SerialAltimeterWorker:
    def __init__(self,altimeter_port="/dev/altimeter",urad_port="/dev/urad"):
        print("INIT SERIAL ALTIMETER WORKER!@#")
        self.altimeter_port = altimeter_port
        self.urad_port = urad_port
        self.main_loop_real()


    def get_reading(self,conn):

        return conn.get_reading()
#        return {
#            "altitude_ground": "ASDASD", #random.uniform(1000, 2000),
#        }
#     def main_loop(self):
#         while True:
#             reading = self.get_reading(None)
#             GPSWorker.update_redis_reading(reading)
#             time.sleep(0.1)
    def read_forever(self,conn,pub):
        while True:
            msg = pub.get_message(ignore_subscribe_messages=1)  # get_message(ignore_subscribe_message=True)
            if msg:
                if msg['channel'] == "kill_t1":
                    print("\n\nKILLING LOOP ALTIMETER OUTTER!!!\n\n")
                    sys.exit(0)
                elif msg['channel'] == "reconfigure_urad":
                    print("RECONFIGURE URAD IF POSSIBLE!", conn)
                    try:
                        cfg = json.loads(msg['data'])
                    except:
                        cfg = {}
                    try:
                        conn.reconfigure(cfg)
                    except:
                        print("Could not use config:",cfg)
                        traceback.print_exc()
            try:
                reading = self.get_reading(conn)
            except:
                print("ERROR GETTING READING!")
                reading = None
            print("GOT ALTIMETER READING!@#", reading)
            if not reading:
                print("CLOSED!!!")
                conn.close()
                time.sleep(0.1)
                break
            GPSWorker.update_redis_reading(reading)
            time.sleep(0.5)
    def get_smart_micro(self):
        from altimeter_ser import AltimeterSer
        conn = AltimeterSer(self.altimeter_port)
        time.sleep(0.1)
        print("OPENED smartmicro ALTIMETER!!!")
        return conn
    def get_urad(self,cfg=None):
        from URAD.alt_urad_ser import AltimeterUradSer
        conn = AltimeterUradSer(self.urad_port,cfg)
        time.sleep(0.1)
        print("OPENED smartmicro ALTIMETER!!!")
        return conn
    def get_altimeter_instance(self,cfg):
        if os.path.exists("/dev/altimeter"):
            print("I think there is a smartmicro attached, attempting to connect")
            return self.get_smart_micro()
        elif os.path.exists("/dev/urad"):
            print("I think i have a urad distance unit attached")
            return self.get_urad(cfg)
        elif os.name == "nt":
            try:
                print("GET URAD?",cfg)
                return self.get_urad(cfg)
            except:
                try:
                    return self.get_smart_micro()
                except:
                    print("Could not get windows ports ... mark as no altimeter")
                SerialWorker.addDevices(altimeter="disconnected")
        raise AssertionError("Unable to find altimeter instance! LSUSB RESULTS BELOW\n%s"%(os.popen("lsusb").read()))

    def main_loop_real(self):

        pub = SerialWorker.r.pubsub()
        pub.subscribe("kill_t1","reconfigure_urad")
        conn = None
        cfg = {}
        while True:
            msg = pub.get_message(ignore_subscribe_messages=1) #get_message(ignore_subscribe_message=True)
            if msg:
               print("RECV MSG(ALTIMETER): {channel} : {data}".format(**msg))

               if msg['channel'] == "kill_t1":
                   print("EXIT NOW!!!")
                   sys.exit(0)
               elif msg['channel'] == "reconfigure_urad":
                   print("RECONFIGURE URAD IF POSSIBLE!", conn)
                   try:
                       cfg = json.loads(msg['data'])
                   except:
                       cfg = {}
                   print("UPDATE CFG:", cfg)
                   # getattr(conn,"reconfigure",lambda x:1)(cfg)

            try:
                 devices = json.loads(SerialWorker.r.get("devices")) # ==  "connected":
            except:
                 devices = {'gps':'disconnected', 'altimeter':'disconnected', 'usb':'disconnected'}
            print("D:",devices)
            if devices.get("altimeter") ==  "connected":
                try:
                    conn = self.get_altimeter_instance(cfg)
                except:
                    print("FAILED TO OPEN ALTIMETER even though i expected to!!!")
                    SerialWorker.addDevices(altimeter="disconnected")
                    traceback.print_exc()
                    time.sleep(0.7)
                    continue
                else:
                    print("OPENED:",conn)
                    self.read_forever(conn,pub)
            GPSWorker.update_redis_reading({"altitude_ground":""})
            #print("Seeee if we are open again?")
            time.sleep(1)


class GPSWorker:
    @staticmethod
    def start(port="/dev/gps"):
        GPSWorker(port)
    def __init__(self,port="/dev/gps"):
        from gps_ser import log
        self.port = port
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
    def update_port(self,port):
        self.port = port
    def main_loop_real(self):
        from gps_ser import GPSSerial,log
        # log.warn("START LOOP")
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
            # log.warn("DEV: %r"%(devices,))
            if devices['gps'] == 'connected':
                # log.warn("OPEN SERIAL")
                try:
                    conn = GPSSerial(self.port)
                    time.sleep(0.1)
                    log.warn("CONNECTED: %r"%(conn,))
                except:
                    # logging.getLogger("gps_raw").exception("CONNECTION ERROR!")
                    time.sleep(0.2)
                    # log.exception("Could not open PORT")
                    if os.name == "nt":
                        devices.update({'gps':'disconnected'})
                        # print("SET DEVICES:",devices)
                        SerialWorker.r.set('devices',json.dumps(devices))
                else:
                    # if devices['gps'] == "disconnected":
                    #     devices.update({'gps': 'connected'})
                    #     # print("SET DEVICES:", devices)
                    #     SerialWorker.r.set('devices', json.dumps(devices))
                    self.read_forever(conn,pub)
            self.update_redis_reading({"altitude_sealevel":"","num_satellites":"-1","satellites_signal":"-1"})
            time.sleep(1)

    @staticmethod
    def update_redis_reading(reading):
        # print("UPDATE:",reading)
        data = SerialWorker.get_current_reading() or {}
        data.update(reading)
        SerialWorker.r.set("reading_data",json.dumps(data))
def start_gps(cfg):
    GPSWorker.start(cfg['gps'])
def start_altimeter(cfg):
    SerialAltimeterWorker(cfg['alt'],cfg['urad'])

class SerialWorker:
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    def __init__(self,port_gps="/dev/gps",port_alt="/dev/altimeter",port_urad="/dev/urad",usb_glob="/dev/sd*"):
        # construct python-redis interface
        self.p = self.r.pubsub()
        self.ports = {'gps':port_gps,'alt':port_alt,'urad':port_urad}
        print("USE CFG:",self.ports)
        print(self.r.config_set("appendonly","no"))
        print(self.r.config_set("save",""))

        self.p.subscribe("kill","download")
        # create and pass data to redis
        self.set_current_reading({})
        self.r.set("gps","disconnected")
        self.r.set('altimeter',"disconnected")
        self.main_loop()
    def download_logs(self,copyTo="/mnt/USB"):
        from gps_ser import log
        from altimeter_ser import log as alog
        # log = logging.getLogger("gps_raw")
        # alog = logging.getLogger("altimeter_errors")
        try:
            devices = json.loads(SerialWorker.r.get("devices"))
        except:
            devices = {}
        SerialWorker.addDevices(usb="disconnected")

        print("DOWNLOAD LOGFILES TO: %s"%copyTo)
        os.system("mount -a")
        final_path = os.path.join(copyTo,"logfiles")
        shutil.rmtree(final_path,True)
        os.makedirs(final_path)
        for fname in glob.glob("/logfiles/*"):
            if fname.endswith(".csv"):
                print("DOWNLOAD: %r -> %r"%(fname,copyTo))
                shutil.copy2(fname,copyTo)
            else:
                print("DOWNLOAD: %r -> %r"%(fname,final_path))
                shutil.copy2(fname,final_path)
            try:
                os.remove(fname)
            except:
                print("CANNOT REMOVE %s"%fname)
        os.system("sync")
        os.system("umount /mnt/USB")
        SerialWorker.addDevices(usb="connected")
    def main_loop(self):
        p1 = threading.Thread(target=start_altimeter,args=[self.ports,])
        p2 = threading.Thread(target=start_gps,args=[self.ports,])
        p1.start()
        p2.start()
        while True:
            self.p.listen()
            msg = self.p.get_message(ignore_subscribe_messages=1)
            if msg:
                print("GOT MSG!!!", msg)
                if msg['channel'] == "kill":
                    SerialWorker.r.publish("kill_t1", "1")
                    SerialWorker.r.publish("kill_t2", "1")
                    p1.join()
                    p2.join()
                    break
                elif msg['channel'] == "download":
                    self.download_logs(msg['data'])
                # elif msg['channe'] == 'update_ports':
                #     self.update_ports()

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
            if os.path.exists("/dev/altimeter") or os.path.exists('/dev/urad'):
                states.update({'altimeter':'connected'})
                self.r.set('devices',json.dumps(states))
        else:
            if not os.path.exists('/dev/altimeter') and not os.path.exists('/dev/urad'):
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

    #reading_g.add_argument('-g', 'geiod_height', type=float, required=False)

if __name__ == "__main__":
    from parse_args import parse_args
    def handle_args(args):
        if args.subparser_cmd == "run":
            print ("RUN APPLICATION", args)
            SerialWorker(port_gps=args.bu,port_alt=args.smartmicro,port_urad=args.urad)
        elif args.subparser_cmd == "update":
            if args.subparser_what == "reading":
                print("UPDATE READING:", args)
                keys = ['altitude_sealevel','altitude_ground','latitude','longitude','num_satellites','satellites_signal','geoid_height']
                data = {k:getattr(args,k) for k in keys if getattr(args,k) is not None}
                print("DATA:",data)
                GPSWorker.update_redis_reading(data)
                print (SerialWorker.r.get("reading_data"),)
            elif args.subparser_what == "connect":
                data = {k:"connected" if getattr(args,k) else None for k in ['gps','altimeter','usb']}
                print("CONNECT:",data)
                SerialWorker.addDevices(**data)
            elif args.subparser_what == "disconnect":
                data = {k:"disconnected" if getattr(args,k) else None for k in ['gps','altimeter','usb']}
                SerialWorker.addDevices(**data)
                print SerialWorker.r.get("devices")
            elif args.subparser_what == "urad":
                print "ARGS:",args
                keys = "mode","f0","BW","Ns","Rmax","Alpha","Ntar","MTI","Mth"
                data = {k:getattr(args,k) for k in keys if getattr(args,k) is not None}
                if args.redis:
                    print("Publish event data:",data)
                    SerialWorker.r.publish("reconfigure_urad",json.dumps(data))
                if args.output:
                    if os.path.exists(args.output):
                        print("File Exists ... only update it")
                        with open(args.output,"rb") as f:
                            content = f.read()
                        pat="|".join(sorted(data.keys(),key=len,reverse=True))
                        print("PAT:",pat)
                        # print(content)
                        def subber(m):
                            newVal = data.pop(m.group(2))
                            print "Update: %s, was %s setting to %s"%(m.group(2),m.group(3),newVal)
                            return "\n"+m.group(1)+m.group(2)+"="+str(newVal)
                        content2 = re.sub("\n(\s*)("+pat+")\s*=\s*(.*)",subber,content)
                        if data:
                            content2 += "\n"
                            for key in data.keys():
                                print "ADD NEW: %s=%s" % (key, data[key])
                                content2+="%s=%s\n"%(key,data[key])
                        #print content2
                        # re.sub(content)
                        with open(args.output, "wb") as f:
                            f.write(content2)
                    else:
                        print("Saving to New File: '%s'" % (args.output))
                        with open(args.output,"wb") as f:
                            f.write("# Automatically generated by SerialWorker/main\n\n[config]\n")
                            for key in keys:
                                if key in data and data[key] is not None:
                                    f.write("%s=%s\n" % (key, data[key]))
                                    print("%s=%s" % (key, data[key]))

                elif not args.redis:
                    print("# Dump to stdout from SerialWorker/main update urad directive")
                    for key in keys:
                        if key in data and data[key] is not None:
                            print("%s=%s"%(key,data[key]))



                # print("CFG:",data)
                # SerialWorker.addDevices(**data)

                # print SerialWorker.r.get("devices")
    handle_args(parse_args())
    # p.add_argument("-s","smart-micro",help="smartmicro port",required=False,type=str,default="/dev/altimeter")
    # p.add_argument("-u","urad",help="smartmicro port",required=False,type=str,default="/dev/urad")
    # p.add_argument("-g","gps",help="BU-353S4 port",default="/dev/gps",required=False,type=str)
    # group = p.add_argument_group('update',help="update the redis-cli and exit")
    # reading_g = group.add_argument_group("reading",help="update the active reading")
    # devices_g = group.add_argument_group("devices",help="update connected devices")
    # reading_g.add_argument("-a","altitude_sealevel",type=float,required=False)
    # reading_g.add_argument('-x',"altitude_ground",type=float,required=False)
    # reading_g.add_argument('-g','geiod_height',type=float,required=False)
    # reading_g.add_argument('-g', 'geiod_height', type=float, required=False)
    # p.parse_args()
    # SerialWorker()
