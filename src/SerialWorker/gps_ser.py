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

def safe_float(val):
    try:
        return float(val)
    except:
        return val
def convertAltitude(msg):
    if not msg or not msg[:-1]:
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
                 date=values_list[8], time=values_list[0],timestamp=time.time())
        if not d['time']:
            d['time'] = time.strftime("*%H%M%S")

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
        # print("SAT DATA",sat_data)
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

class parseGPS2:
    @staticmethod
    def GPRMC(values_list,ser=None):
        return parseGPS.GPRMC(values_list)
    @staticmethod
    def GPGGA(values_list,ser=None):
        return parseGPS.GPGGA(values_list)
    @staticmethod
    def GPGSV(values_list,ser=None):
        n_sat = int(values_list[2])
        satellites = []
        signal = -3
        for i in range(int(values_list[1]),int(values_list[0])+1):
            if not values_list:
                print("ERROR... no GSV values_list??????",repr(values_list))
                return None
            result = parseGPS.GPGSV(values_list)
            # print("PAGE: ",i,result)
            satellites.extend(result['values'])
            if values_list[2] == values_list[1]:
                # print("GOT GPGSV Complete")
                # print("NSAT:",n_sat,len(satellites))

                if(len(satellites) >= 3):
                    signals = [float(sat['signal']) for sat in satellites]
                    signals.sort(reverse=True);
                    signal = sum(signals[:3])/float(3)
                else:
                    signal = -2
                break
            values_list,raw = ser.read_line()
            if values_list:
                values_list = values_list[1:]
        return {'satellites_values':satellites,'num_satellites':n_sat,'satellite_signal':signal}

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
def ConnectToPortAndSpeedItUp(port,baudRates=[4800,9600,19200,38400],targetRate=4800):
    c = serial.Serial(port,timeout=1.0)
    for baud in baudRates:
        c.close()
        c.baudrate = baud
        c.open()
        msg = c.read(100)
        if "$G" in msg and "\r\n" in msg:
            print("Found Baud:",baud)
            if baud != targetRate:
                set_baudrate(c,targetRate)
            break
    else:
        return None
    #send Configure
    print("Configure GPS @ %sbps"%targetRate)
    set_msg_mode(c,"RMC",1) # update lat/lon/time every 1 seconds
    set_msg_mode(c,"GGA",1) # update sealevel height every 1 seconds
    set_msg_mode(c,"GSV",10) # update satelites every 10 seconds
    #DISABLE THE REST
    set_msg_mode(c,"GLL",0)
    set_msg_mode(c,"VTG",0)
    set_msg_mode(c,"MSS",0)
    set_msg_mode(c,"ZDA",0)
    set_msg_mode(c,"GSA",0)
    return c
def set_baudrate(ser,baudrate):
    msg = "$PSRF100,1,%s,8,1,0" % baudrate
    cs = reduce(lambda a, b: a ^ b, bytearray(msg[1:]))
    msg = "%s*%02X\r\n" % (msg, cs)
    print("SET BAUD: %s" % baudrate, msg)
    ser.write(msg)
    ser.flush()
    ser.close()
    ser.baud = baudrate
    ser.open()
    print(repr(ser))
def set_msg_mode(ser,msgType="RMC",queryRate=1):
    msgTypeCode = {"RMC":"04","GGA":"00","GLL":"01","GSA":"02","GSV":"03","VTG":"05","MSS":"06","ZDA":"08"}[msgType]
    msg="$PSRF103,%s,00,%02d,01"%(msgTypeCode,queryRate)
    cs = reduce(lambda a,b:a^b,bytearray(msg[1:]))
    msg = "%s*%02X\r\n" % (msg, cs)
    print("SET MODE: %s to sample every %d seconds : %r"%(msgType,queryRate,msg))
    ser.write(msg)
    time.sleep(0.1)
    # c.write("")
    # c.write("%s*%02x\r\n"%(msg,cs))
class GPSSerial:
    alive = 0;
    def __init__(self,port="/dev/gps"):
        log.warn("INIT %s"%port)
        self.conn = ConnectToPortAndSpeedItUp(port)#serial.Serial(port,baudrate=4800,timeout=1.0)

        time.sleep(1.1)
        log.warn("opened connection %r"%(self.conn,))
    def close(self):
        self.conn.close()
    def read_line(self,onChecksumError="warn"):
        line = self.conn.readline();
        log.warn(repr(line))
        try:
            msg, checksum_expect = line.strip().rsplit("*", 1)
        except:
            log.error("!!! %r"%line)
            return None,line
        checksum_calculated = reduce(operator.xor, bytearray(msg[1:]))
        if int(checksum_expect,16) != checksum_calculated:
            if onChecksumError == "warn":
                sys.stderr.write("ChecksumError: %r but calculated %02X\n"%(msg,checksum_calculated))
            elif onChecksumError == "error":
                raise Exception("ChecksumError: %r but calculated %02X\n" % (msg, checksum_calculated))
        return msg.split(","),line
    def read_forever(self,on_recv_gps_payload_callback,delay=0.01):
        handlers = {
            "$GPRMC": parseGPS2.GPRMC,
            "$GPGGA": parseGPS2.GPGGA,
            "$GPGSV": parseGPS2.GPGSV
        }
        self.alive = 1;
        buffer = ""
        while self.alive:
            time.sleep(delay)
            values,raw = self.read_line()
            if not values:
                continue
            if values[0] in handlers:
                on_recv_gps_payload_callback(handlers[values[0]](values[1:],self),raw)
            else:
                print("Not Found:",values[0])
                on_recv_gps_payload_callback(None,raw)


    def get_reading(self,retries=3):
        log.warn("Start Read")
        t0 = time.time()
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
            print("Reading Took %0.2fs"%(time.time()-t0))
        return data



if __name__ == "__main__":
    # set_msg_mode(None, msgType="VTG", queryRate=1)
    # exit(1)
    s = GPSSerial("COM4")
    def result(ob,raw):
        print("GOT :",ob)
        # print("RAW:",raw)
    s.read_forever(result)
