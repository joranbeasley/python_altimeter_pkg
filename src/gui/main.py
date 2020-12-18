#!/usr/bin/python

import os
import signal
import sys
import threading
import csv
import itertools
import glob
import json
import random
import time
import traceback
import redis

try:
    import tkinter as tk
except:
    import Tkinter as tk
import datetime
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger("main_gui")
logger.setLevel(logging.DEBUG)
logger.addHandler(RotatingFileHandler("/logfiles/main_gui.log",maxBytes=500000,backupCount=1))
logger.addHandler(logging.StreamHandler())
r = redis.StrictRedis(host='localhost', port=6379, db=0)
from ChartPanel import ChartPanel

class StatusLight:
    def __init__(self,master,label,state=0,colors=["red","green"]):
        self.root = master

def timeTicks(x, pos):
    d = datetime.timedelta(seconds=x%86400)
    return str(d)
# figure =  Figure(figsize=(4,1), dpi=75)
def signal_SIGIO(sig, frame):
    # SIGIO=12
    try:
        logger.setLevel(logging.DEBUG)
    except:
        logger.exception("Could not set log level...")
    logger.debug("GOT SIG2")

def signal_SIGUSR1(sig, frame):
    # SIGUSR1=10
    try:
        logger.setLevel(logging.INFO)
    except:
        logger.exception("Could not set log level...")
    logger.info("GOT SIG3")
def signal_SIGUSR2(sig, frame):
    # SIGUSR2=12
    try:
        logger.setLevel(logging.WARNING)
    except:
        logger.exception("Could not set log level...")
    logger.warn("GOT SIG4")

if os.name != "nt":
    # SIGIO = 29
    signal.signal(signal.SIGIO, signal_SIGIO)
    # SIGUSR1 = 10
    signal.signal(signal.SIGUSR1, signal_SIGUSR1)
    # SIGUSR2 = 12
    signal.signal(signal.SIGUSR2, signal_SIGUSR2)
class Header:
    def __init__(self,master,label="initializing",bg="white",fg="black",gps="no",alt="no"):
        self.root = master
        self.state = {"text":label,"bg":bg,"fg":fg,"gps":gps,"alt":alt}
        self.state = {"text":label,"bg":bg,"fg":fg,"gps":gps,"alt":alt}
        self.header = tk.Label(self.root, text="   initializing...",
                               font=("helvetica",16),
                               bg=self.state['bg'],fg=self.state['fg'], anchor="w")
        self.gps_indicator = tk.Label(self.root, text="gps", bg=self.state['bg'],fg=self.state['fg'], anchor="nw")
        self.gps_indicator_light = tk.Label(self.gps_indicator, bg="red",borderwidth=1, relief="solid")
        self.alt_indicator = tk.Label(self.root, text="alt", bg=self.state['bg'],fg=self.state['fg'], anchor="nw")
        self.alt_indicator_light = tk.Label(self.alt_indicator, bg="red",borderwidth=1, relief="solid")
        self.header.place(x=0, y=0, width=320, height=35)
        self.gps_indicator.place(x=270, height=35)
        self.gps_indicator_light.place(y=17, x=6, width=10, height=10)
        self.alt_indicator.place(x=300, height=35)
        self.alt_indicator_light.place(y=17, x=3, width=10, height=10)
        self.gps_label = tk.Label(self.root,text="12\n99%",bg="black",fg="white")
        self.gps_label.place(x=240)
    def update(self,bg=None,fg=None,text=None,gps=None,alt=None,gps_status=None):
        if alt:
            self.state['alt'] = alt
        if gps:
            self.state['gps'] = gps
        if text:
            self.state['text'] = text
        if fg:
            self.state['fg'] = fg
        if bg:
            self.state['bg'] = bg
            if not fg:
                if bg == "black":
                    self.state['fg'] = "red"
                else:
                    self.state['fg'] = "black"
        if gps_status is not None:
            self.gps_label.configure(text=gps_status)
        self.header.configure(bg=self.state['bg'],fg=self.state['fg'],text="   %s"%(self.state['text'],))
        self.gps_indicator.configure(bg=self.state['bg'],fg=self.state['fg'])
        self.gps_indicator_light.configure(bg=["green","red"][self.state['gps']=="no"])
        self.alt_indicator.configure(bg=self.state['bg'], fg=self.state['fg'])
        self.alt_indicator_light.configure(bg=["green", "red"][self.state['alt'] == "no"])
        self.gps_label.configure(bg=self.state['bg'])
class Layout:
    def __init__(self, root):
        self._logging_file=None
        self.root = root
        self.th = None
        self.plot_records = []
        self.plot_records2 = []
        self._trace2 = False
        self._logging = None
        self.state = {'usb':'no','gps': 'no', 'altimeter': 'no', "display_value": "No Reading","recording":"NOT RECORDING"}
        self.header= Header(self.root,"initializing...","goldenrod1")
        self.main_label = tk.Label(self.root, text="----.-",font=("Helvetica", 76),bg="white",bd=0)
        self.main_label.place(x=20,y=35)
        def toggleTrace2():
            self._trace2 = not self._trace2
            if self._trace2:
                logger.warn("TOGGLE ON TRACE2")
                self.sealevel.config(bg="yellow",state=tk.NORMAL)
                self.chart.showTrace(1)
                self.chart.update()
            else:
                self.sealevel.config(bg="light grey",state=tk.NORMAL)
                logger.warn("TOGGLE OFF TRACE2")
                self.chart.hideTrace(1)
                self.chart.update()
        # self.sealevel = tk.Button(self.root, text="---.-\nmeters sealevel",
        #                             command=toggleTrace2,
        #                             anchor="w",
        #                             relief="raised")
        # self.sealevel.place(x=200,y=35)
        self.unit_label = tk.Label(self.root,anchor="w",text="meters ground",font=("helvetica",11),bg="white")
        self.unit_label.place(x=188,y=132)

        self._createFigure()
        # self.ico = SateliteIcon(self.root,"12\n(-1%)")
        # self.ico.canvas.place(x=190,y=35)
        self.buttons = [tk.Button(self.root,text="Start Recording",bg="green",command=self.toggleRecording,state=tk.NORMAL),
                        tk.Button(self.root,text="Download")]
        # self.buttons[0].bind("<ButtonRelease>", self.WtoggleRecording)
        self.buttons[0].place(y=190,height=50,width=250)
        self.buttons[1]['state']=tk.DISABLED
        self.buttons[1].place(x=250,y=190,height=50,width=70)
        self.unit_label.lift()
    def pauseRecording(self):
        self.state['recording'] = "RECORDING PAUSED"
        self.buttons[1].configure(state=tk.DISABLED,bg="light grey")
        self.buttons[0].configure(text="Resume Recording", bg="SteelBlue1")
        self.header.update("SteelBlue1", "black", "RECORDING PAUSED")
        self.root.focus_set()
    @property
    def logging(self):
        if self.state['recording'] == "RECORDING":
            if not self._logging:
                try:
                    data = json.loads(r.get('reading_data'))
                    fname = "/logfiles/" + data["date"] + "T" + data["time"] + ".csv"
                    if fname.endswith("/T.csv"):
                        fname = time.strftime("/logfiles/x%Y%m%dT%H%M%S.csv")
                except:
                    logger.exception("Unable to get valid filename, generating from systime")
                    fname = time.strftime("/logfiles/x%Y%m%dT%H%M%S.csv")
                fname0 = fname[:-4]
                for i in itertools.count(1):
                    if not os.path.exists(fname):
                       break
                    fname = "%s (%s).csv"%(fname0,i)

                labels = ['date', 'time', 'altitude_ground', 'latitude', 'longitude', 'latitude2', 'longitude2',
                          'altitude_sealevel', 'geoid_height', 'speed', 'heading', "strength","num_satellites","satellites_signal","satellites_values"]
                self._logging_file = open(fname, "wb")
                self._logging = csv.DictWriter(self._logging_file,labels,extrasaction="ignore")
                self.logging.writeheader()
                logger.info("LOGGING INITIALIZED!!! %r"%(self._logging_file,))
                    # fname = find_next_log_name()
                # self._logging = csv.DictWriter()
            return self._logging
        return False
    def toggleRecording(self,*args):
        logger.info("TOGGLE Recording : %s"%(self.state['recording'],))
        if self.state['recording'] in ["NOT RECORDING","RECORDING PAUSED"] :
            self.state['recording'] = "RECORDING"
            self.buttons[0].configure(text="Stop Recording",bg="red",state=tk.NORMAL)
            self.buttons[1].configure(text="PAUSE",bg="SteelBlue1",state=tk.NORMAL)
            self.buttons[1]['command'] = self.pauseRecording
            self.header.update("chartreuse3","black","RECORDING","yes")
        else:
            self.state['recording'] = "NOT RECORDING"
            try:
               self._logging_file.close()
            except:
               logger.exception("ERROR CLOSING LOGGING FILE!")
            self._logging = None
            log_ct = len(glob.glob("/logfiles/*.csv"))
            self.buttons[1].configure(text="Download\n(%s)"%log_ct,bg="light grey", state=tk.DISABLED)
            self.buttons[0].configure(text="Start Recording",bg="green",state=tk.NORMAL)
            self.header.update("black", "red", "NOT RECORDING")

    def addValue(self,value,value2):
        try:
            vAlt = float(value)
        except:
            vAlt = float("nan")
        try:
            vGPS = float(value2)
        except:
            vGPS = float("nan")
        value_a = value if value == "---.-" else "%0.1f"%vAlt
        value_b = value2 if value2 == "---.-" else "%0.1f"%vGPS

        self.main_label.configure(text="%0.1f"%value)
        # self.chart.add_point(0,[time.time(),value])
        # self.chart.add_point(1,[time.time(),value2],update=True)
        # self.sealevel.config(text="%0.1f \nmeters sealevel"%(value2))


    def _createFigure(self):
        # self.chart = ChartPanel(self.root,320,80)
        # self.chart.hideTrace(1)
        # self.chart.place(y=99)
        # return self.chart
        pass

    def _fixAxes(self):
        traceback.print_stack()
        print("DONT CALL FIXAXES NOW!!!")

    @staticmethod
    def get_data_from_redis():
        def decode(s,default=None):
            try:
                return json.loads(s)
            except:
                return default
        return {
            'data':decode(r.get("reading_data"),{"latitude":"-1","longitude":"-1","altitude_ground":"1.1","altitude_sealevel":"999.9"}),
            'devices':decode(r.get('devices'),{"gps":"disconnected","altimeter":"disconnected","usb":"disconnected"}),
        }
    def request_download(self):
        r.publish("download","/mnt/USB")
        self.root.focus_set()
    def update_chart_tick(self,i):
        # logger.info("Update The Chart? %r"%self.chart.tr)
        # self.update_chart_easy()
        pass

    def update_tick(self):
        t0 = time.time()
        data = self.get_data_from_redis()
        # logger.warn("Took %0.2fs to fetch current data"%(time.time()-t0))
        t1 = time.time()
        header_text = self.state['recording']
        header_color = {
            'NOT RECORDING':"black",
            "RECORDING":"chartreuse3",
            "RECORDING PAUSED":"SteelBlue3"
        }.get(header_text,"red")
        self.header.update(
            text=header_text,
            bg=header_color,
            gps=["yes","no"][data['devices']['gps']!="connected"],
            alt=["yes","no"][data['devices']['altimeter']!="connected"],
            gps_status="%d\n%d%%"%(int(data['data'].get('num_satellites','-1')), float(data['data'].get('satellites_signal','-1')))
        )
        log_ct = len(glob.glob('/logfiles/*.csv'))
        if header_text == "NOT RECORDING":
            if data['devices']['usb'] != 'connected' and self.buttons[1]['state'] != tk.DISABLED:
                logger.info("DISABLE DOWNLOAD BUTTON(no usb)")
                self.buttons[1]['state'] = tk.DISABLED
            elif data['devices']['usb'] == 'connected' and self.buttons[1]['state'] == tk.DISABLED:
                logger.info("ENABLE DOWNLOAD BUTTON(usb)")
                self.buttons[1]['state'] = tk.NORMAL

            self.buttons[1].configure(text="Download\n(%s)"%(log_ct,),
                                      command=self.request_download)
        elif self._logging_file:
            fname = os.path.basename(self._logging_file.name)
            self.buttons[0]['text'] = {
                   'RECORDING': 'Stop Recording\n%s'%fname,
                   'RECORDING PAUSED': 'Resume Recording\n%s'%fname
            }.get(self.state['recording'], self.buttons[0]['text'])
            self.buttons[1]['text'] = "PAUSE\n(%s)"%log_ct
        value1 = float('nan')
        value2 = float('nan')
        if 'altitude_ground' in data['data']:
            logger.info("UPDATE altimeter data:",data['data'])
            try:
                value1 = float(data['data']['altitude_ground'])
            except ValueError:
                value1 = float("nan")
            if str(value1) == "nan" and data['devices']['altimeter'] == "connected":
                self.header.alt_indicator_light.configure(bg="DarkGoldenrod2")
        if 'altitude_sealevel' in data['data']:
            logger.info("ALSO UPDATE GPS DATA(same)")
            try:
                if str(value2) == "nan":
                    value2 = float(data['data']['altitude_sealevel'])
                else:
                    float(data['data']['altitude_sealevel'])
            except:
                value = float("nan")
            if str(value2) == "nan" and data['devices']['gps'] == "connected":
                self.header.gps_indicator_light.configure(bg="DarkGoldenrod2")


        csv_logging =  self.logging
        if csv_logging:
            csv_logging.writerow(data['data'])
        t2 = time.time()
        self.addValue(value1,value2)
        # logger.info("Took %0.2fs to Add the Value"%(time.time()-t1,))
        logger.debug("Took %0.2fs to complete Tick(Query Redis=%0.2fs,UI=%s,AddValue=%0.2fs)"%(time.time()-t0,t1-t0,t2-t2,time.time()-t2))

    def updateHeader(self,bg,fg,text):
        self.header.update(bg,fg,text)
    def updateUI(self,value_data,gps_connected=None,altimeter_connected=None):
        pass

class MyApp:
    def __init__(self):
        def fake_ticks():
            self.layout.addValue(random.uniform(120,160))
            self.root.after(1000,fake_ticks)
        def update_ui():
            self.layout.update_tick()
            self.root.after(1000, update_ui)

        self.root = tk.Tk()
        self.root.withdraw()
        def show_me():
            self.root.update()
            self.root.deiconify()
            self.root.update()
            self.layout.buttons[0]['state'] = tk.NORMAL


        #self.root.after(1000,lambda:self.layout.updateHeader(bg="black",fg="red",text="No Devices!!!"))
        self.root.configure(bg="white")
        self.root.geometry("320x240")
        self.layout = Layout(self.root)
        self.root.bind("<KeyRelease>",self.onKeyDown)
        update_ui()
        self.root.after(1000, show_me)
        print("Bound Key Release")
    def onKeyDown(self,evt):
        if evt.char == "U":
            cmd = "%s %s"%(sys.executable,os.path.join(os.path.dirname(__file__),"urad_configure.py"))
            print("EXEC:",cmd)
            os.system(cmd)
        print("KeyDown??",evt.char)
    def mainloop(self):
        try:
            self.root.mainloop()
        except:
            logger.exception()
            raise

if __name__ == "__main__":
    app = MyApp()
    # ani = animation.FuncAnimation(figure, app.layout.update_chart_tick, interval=1000)
    app.mainloop()

