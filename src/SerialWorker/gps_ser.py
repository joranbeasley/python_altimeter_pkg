import json
import operator

import serial
import time
import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s - %(message)s")
log = logging.getLogger("gps_raw")
log.setLevel(logging.DEBUG)
hnd = RotatingFileHandler("/logfiles/gps_raw.txt", backupCount=1, maxBytes=25000)
hnd.setFormatter(logging.Formatter("%(asctime)-15s - %(message)s"))
log.addHandler(hnd)
log.warn("OPENED!")
def safe_float(val):
    try:
        return float(val)
    except:
        return val
def convertAltitude(msg):
    if not msg:
        return ""
    if isinstance(msg,basestring):
        return float(msg[:-1]) *(-1 if msg[-1].lower() in "sw" else 1)
    elif isinstance(msg,(list,tuple)):
        return convertAltitude(msg[0]+msg[1])

class parseGPS:
    @staticmethod
    def GPRMC(values_list):
        d = dict(latitude=values_list[2] + values_list[3], longitude=values_list[4] + values_list[5],
                 speed=safe_float(values_list[6]),
                 heading=safe_float(values_list[7]),
                 date=values_list[8], time=values_list[0])
        d["latitude2"] = convertAltitude(d["latitude"])
        d["longitude2"] = convertAltitude(d["longitude"])
        return d
    @staticmethod
    def GPGGA(values_list):
        return {"altitude_sealevel": safe_float(values_list[-6]),
                "geoid_height": safe_float(values_list[-4])}
    @staticmethod
    def GPGSV(values_list):
        def float_it(value):
            try:
                return float(value)
            except:
                return -1
        sat_data = {"n_sat": int(values_list[2]),
                    'values':[{'id':values_list[i],'ele':values_list[i+1],
                              'azm':values_list[i+2],'signal':float_it(values_list[i+3])
                              } for i in range(3,len(values_list),4)]}
        print("SAT DATA",sat_data)
        return sat_data


    # @staticmethod
    # def GPGSV(cls, values_list):
    #     n_sat = int(values_list[2])
    #     my_list = [values_list[i:i+4] for i in range(3,len(values_list)+1,4)]
    #     while int(msg[1]) < int(msg[0]):
    #         msg = cls.ser.get_verified_sentence()[1:]
    #         my_list.extend([msg[i:i+4] for i in range(3,len(msg)+1,4)])
    #     my_list = filter(None,my_list)
    #     assert len(my_list) == n_sat,"[Error Bad Sat Count Expexted %d, Found %d]"%(n_sat,len(my_list))
    #     signals = map(safecast_map(map_index=3),my_list)
    #     return dict(strength=numpy.average(sorted(signals[-5:])))
class GPSSerial:
    def __init__(self,port="/dev/gps"):
        log.warn("INIT %s"%port)
        self.conn = serial.Serial(port,baudrate=4800,timeout=1.0)
        time.sleep(1.1)
        log.warn("opened connection %r"%(self.conn,))
    def close(self):
        self.conn.close()
    def get_reading(self,retries=3):
        log.warn("Start Read")
        self.conn.flush()
        line = self.conn.readline()
        if not line:
            if retries <= 0:
                return None
            return self.get_reading(retries-1)
        handlers = {
            "$GPRMC": parseGPS.GPRMC,
            "$GPGGA": parseGPS.GPGGA,
            "$GPGSV": parseGPS.GPGSV
        }
        data = {}
        while handlers:
            while not line.split(",",1)[0] in handlers:
                line = self.conn.readline()

            msg,checksum_expect = line.strip().rsplit("*",1)
            checksum_calculated=reduce(operator.xor,bytearray(msg[1:]))
            if int(checksum_expect,16) == checksum_calculated:
                log.warn(line.strip()+" (passed %s=%s)"%(int(checksum_expect,16),checksum_calculated))
                values = msg.split(",")
                if values[0] == "$GPGSV":
                    print("HANDLE:",values)
                    handler = handlers[values[0]]
                    sat_data = handler(values[1:])
                    # print("UPDATE:", data['satellites'])
                    data.setdefault('satellites', {})[values[2]] = sat_data
                    print("UPDATE:",data['satellites'])
                    expected_pages = list(range(1,int(values[1])+1))
                    expected_keys = set(map(str, expected_pages))
                    if expected_keys.intersection(data['satellites'].keys()) == expected_keys:
                        print("done with GPGSV payload!")
                        d = {}
                        d.update(data['satellites'])
                        data['satellites'] = {'n_sat':d['1']['n_sat'],
                                              'values':d['1']['values']}

                        for p in expected_pages[1:]:
                            data['satellites']['values'].extend(d[str(p)]['values'])
                        print("PROCESSED:",data['satellites']['values'].sort(key=lambda x:x['signal'],reverse=True))
                        if any(x['signal']<0 for x in data['satellites']['values'][:4]):
                            data['satellites_signal'] = -1
                        else:
                            data['satellites_signal'] = sum([x['signal'] for x in data['satellites']['values'][:4]])/4.0
                        data['satellites_values'] = json.dumps(data['satellites']['values'])
                        data['num_satellites'] = data['satellites']['n_sat']
                        data.pop('satellites')
                        handlers.pop('$GPGSV')
                    else:
                        line = self.conn.readline()
                        print("CHECK:",line)
                else:
                    data.update(handlers.pop(values[0])(values[1:]))

            else:
                log.warn(line.strip()+" (FAIL CHECKSUM! %s != %s)"%(int(checksum_expect,16),checksum_calculated))
                if retries <=0:
                    return data
                retries -= 1
        return data



if __name__ == "__main__":
    s = GPSSerial("COM4")
    t0 = time.time()
    print(s.get_reading())
    t1 = time.time()
    print(s.get_reading())
    t2 = time.time()
    print(t1-t0,t2-t1)
