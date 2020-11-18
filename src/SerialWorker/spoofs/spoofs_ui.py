import json
import os
import time

import urllib

lat,lon = "-122.337798,37.810550".split(",")
import tkinter as tk
from PIL import Image, ImageTk
import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)
class TextEntry:
    def __init__(self,master,label,value):
        self.root = tk.Frame(master)
        self.var = tk.StringVar(value=value)
        self.label = tk.Label(self.root,text=label,anchor="w")
        self.entry = tk.Entry(self.root,textvariable=self.var)
    def pack(self,**kwargs):
        self.label.pack(side=tk.LEFT,anchor='w')
        self.entry.pack(side=tk.LEFT,anchor='e')
        self.root.pack(**kwargs)
        return self
    def get(self):
        return self.var.get()
    def set(self,value):
        return self.var.set(value)
class GUI:
    def getImageMap(self,fname,lat,lon,width=200,height=200,zoom=7.67):
        url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/geojson(%7B\"type\"%3A\"Point\"%2C\"coordinates\"%3A%5B{lat}%2C{lon}%5D%7D)/{lat},{lon},{zoom},0.00,0.00/{width}x{height}?access_token=pk.eyJ1Ijoiam9yYW5iZWFzbGV5IiwiYSI6ImNrNTdyeGJoYTA2cDczbHFxMGV3NWM5bXkifQ.jSykM5vl10p8tQINocpl3Q"
        with open(fname,"wb") as f:
            f.write(urllib.urlopen(url.format(lat=lat,lon=lon,zoom=zoom,width=width,height=height)).read())
    def PhotoMap(self):
        self.getImageMap("tmp.png",self.lat.get(),self.lon.get())
        im = Image.open('tmp.png')
        img = ImageTk.PhotoImage(im)
        self.image.configure(image=img)
        self.image.image = img
        return self.image
    def Update(self):
        fake_reading_data = {"altitude_ground":self.altimeter.get(),
                             "altitude_sealevel":self.alt_gps.get(),
                             "latitude":self.lat.get(),
                             "longitude":self.lon.get(),
                             "date":time.strftime("%Y%d%m"),
                             "time":time.strftime("%H%M%S")}
        fake_devices = {
            "gps":["disconnected","connected"][self.toggles[0].get()],
            "altimeter":["disconnected","connected"][self.toggles[1].get()],
            "usb":["disconnected","connected"][self.toggles[2].get()],
        }
        print("FAKE READING:",fake_reading_data)
        print("FAKE DEVICES:",fake_devices)
        r.set("reading_data",json.dumps(fake_reading_data))
        r.set("devices",json.dumps(fake_devices))

        self.PhotoMap()
    def __init__(self,master):
        self.root = master
        self.alt_gps = TextEntry(self.root,"gps_altitude","133.2").pack()
        # self.alt.pack()
        # self.alt_var_sealevel = tk.StringVar(value="133.2")
        # self.alt_var_ground = tk.StringVar(value="93.2")
        # self.alt_sealevel = tk.Entry(self.root,textvariable=self.alt_var_sealevel).pack()
        self.lat = TextEntry(self.root,"latitude",lat).pack()
        self.lon = TextEntry(self.root,"latitude",lon).pack()
        # self.gps_lat_var = tk.StringVar(value=lat)
        # self.gps_lat = tk.Entry(self.root,textvariable=self.gps_lat_var)
        # self.gps_lon_var = tk.StringVar(value=lon)
        # self.gps_lon = tk.Entry(self.root,textvariable=self.gps_lon_var)
        # self.gps_lat.pack()
        # self.gps_lon.pack()

        self.altimeter = TextEntry(self.root,"altitude2","121.4").pack()
        f2 = tk.Frame(self.root)
        self.toggles = [tk.IntVar(),tk.IntVar(),tk.IntVar()]
        self.gps_toggle = tk.Checkbutton(f2,text="GPS",variable=self.toggles[0])
        self.gps_toggle.pack(side=tk.LEFT)
        self.alt_toggle = tk.Checkbutton(f2,text="ALT",variable=self.toggles[1])
        self.alt_toggle.pack(side=tk.LEFT)
        self.usb_toggle = tk.Checkbutton(f2,text="USB",variable=self.toggles[2])
        self.usb_toggle.pack(side=tk.LEFT)
        self.usb_path = "/fake_usb"
        f2.pack()
        self.btn = tk.Button(self.root,text="Update",command=self.Update).pack()
        self.btn2 = tk.Button(self.root,text="PlayGPSTrack",command=self.Update).pack()
        self.image = tk.Label(self.root)
        self.map = self.PhotoMap().pack()

root = tk.Tk()
gui = GUI(root)
root.mainloop()
