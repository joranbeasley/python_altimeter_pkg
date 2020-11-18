#!/usr/bin/python

import os
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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator
import datetime
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger("main_gui")
logger.setLevel(logging.DEBUG)
logger.addHandler(RotatingFileHandler("/logfiles/main_gui.log",maxBytes=500000,backupCount=1))
logger.addHandler(logging.StreamHandler())
r = redis.StrictRedis(host='localhost', port=6379, db=0)
class StatusLight:
    def __init__(self,master,label,state=0,colors=["red","green"]):
        self.root = master

def timeTicks(x, pos):
    d = datetime.timedelta(seconds=x%86400)
    return str(d)

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
        self.main_label = tk.Label(self.root, text="----.-",font=("Helvetica", 46),bg="white",bd=0)
        self.main_label.place(x=20,y=35)
        def toggleTrace2():
            self._trace2 = not self._trace2
        self.sealevel = tk.Button(self.root, text="---.-\nmeters sealevel",
                                    command=toggleTrace2,
                                    anchor="w",
                                    relief="raised")
        self.sealevel.place(x=200,y=35)
        self.unit_label = tk.Label(self.root,anchor="w",text="meters ground",font=("helvetica",11),bg="white")
        self.unit_label.place(x=188,y=88)

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
        self.plot_records.append([time.time(),value])
        self.plot_records2.append([time.time(),value2])
        self.plot_records = self.plot_records[-100:]
        self.plot_records2 = self.plot_records2[-100:]
        self.sealevel.config(text="%0.1f \nmeters sealevel"%(value2))
        if self.th is None:
            self.th = True
            threading.Thread(target=self.update_chart).start()

    def update_chart(self):
        #delete old data
        t0 = time.time()
        self.axes.draw_artist(self.axes.patch)
        # set the new data, could be multiple lines too
        times, alt = zip(*self.plot_records)
        self.line1.set_data(times, alt)
        self.axes.draw_artist(self.line1)
        if self._trace2:
            # set line2 data
            times, gps = zip(*self.plot_records2)
            self.line2.set_data(times,gps)
            self.axes.draw_artist(self.line2)
        else:
            # set line2 data
            self.line2.set_data([],[])
            self.axes.draw_artist(self.line2)

        # redraw the axis (and re-limit them)
        self.axes.relim()
        self.axes.autoscale_view()
        self.fig.canvas.draw()
        self.th = None
        logger.info("Took %0.2fs to update the chart(seperate thread)"%(time.time()-t0))
        # update figure
#        self.fig.canvas.flush_events()


        """        print("B4Plot",time.time()-t0)
        t1 = time.time()
        self.axes.clear()
        print("CA",time.time()-t1)
        t2 = time.time()
        times, alt = zip(*self.plot_records)
        self.axes.plot(times,alt)
        print("P",time.time()-t2)
        if self._trace2:
            t3 = time.time()
            times, gps = zip(*self.plot_records2)
            self.axes.plot(times,gps)
            print("P2",time.time()-t3)
        t4 = time.time()
        self._fixAxes()
        print("FIX AX:",time.time()-t4)"""
    def _createFigure(self):
        t0 = time.time()
        self.fig = Figure(figsize=(4, 1), dpi=75)
        self.fig.patch.set_facecolor("white")
        self.time_axis_formatter = FuncFormatter(timeTicks)
        self.axes = self.fig.add_subplot(111)
        self.ticks2 = MaxNLocator(nbins=2)
        self.ticks1 = MaxNLocator(nbins=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas._tkcanvas.config(bg='white', borderwidth=0, highlightthickness=0)
        self.canvas.draw()
        self.line1 = self.axes.plot([],[])[0]
        self.line2 = self.axes.plot([],[])[0]
        self.canvas.get_tk_widget().place(y=99,height=90)
        self._fixAxes()
        logger.info("Create Figure Took %0.2fs"%(time.time()-t0))
    def _fixAxes(self):
        self.axes.yaxis.set_major_locator(self.ticks1)
        self.axes.xaxis.set_major_locator(self.ticks2)
        self.axes.xaxis.set_major_formatter(self.time_axis_formatter)
        try:
            self.fig.tight_layout()
        except:
            logger.exception("Could not create tight_layout!")
        finally:
            self.canvas.draw()
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
        r.publish("download","/fake_usb")
        self.root.focus_set()

    def update_tick(self):
        t0 = time.time()
        data = self.get_data_from_redis()
        logger.warn("Took %0.2fs to fetch current data"%(time.time()-t0))
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
                self.buttons[1]['state'] = tk.DISABLED
            elif data['devices']['usb'] == 'connected' and self.buttons[1]['state'] == tk.DISABLED:
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
            try:
                value1 = float(data['data']['altitude_ground'])
            except ValueError:
                value1 = float("nan")
            if str(value1) == "nan" and data['devices']['altimeter'] == "connected":
                self.header.alt_indicator_light.configure(bg="DarkGoldenrod2")
        if 'altitude_sealevel' in data['data']:
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
        t1 = time.time()
        self.addValue(value1,value2)
        logger.info("Took %0.2fs to Add the Value"%(time.time()-t1,))
        logger.info("Took %0.2fs to complete Tick"%(time.time()-t0,))

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
        #self.root.after(1000,lambda:self.layout.updateHeader(bg="black",fg="red",text="No Devices!!!"))
        self.root.configure(bg="white")
        self.root.geometry("320x240")
        self.layout = Layout(self.root)
        update_ui()

    def mainloop(self):
        self.root.mainloop()

if __name__ == "__main__":
    MyApp().mainloop()

