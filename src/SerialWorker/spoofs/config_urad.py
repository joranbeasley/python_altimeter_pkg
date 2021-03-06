try:
    import tkinter as tk
except:
    import Tkinter as tk
class LabeledEntry(object):
    def __init__(self,master,label,on_change=lambda:1,validate_fn=lambda:1):
        """

        :param master:
        :param label:
        :param on_change:
        :param validate_fn: must return None if validation succeeds, return string error message if validation fails
        """
        self.master = master
        self.root = tk.Frame()
        self.var = tk.StringVar()
        self.label = tk.Label(self.root,text=label,anchor="e")
        self.te =  tk.Entry(master=self.root,textvariable=self.var)
        self.label.pack(side=tk.LEFT)
        self.te.pack(side=tk.LEFT)
        self.te.bind("<FocusOut>",self._lostFocus)
    def _lostFocus(self,e):
        print("VAL:",self.value)
    def __getattr__(self, item):
        return getattr(self.root,item)

    @property
    def value(self):
        return self.var.get()
    @value.setter
    def value(self,value):
        return self.var.set(value)
class LabeledMenu(object):
    def __init__(self,master,label,choices,on_change=lambda:1):
        """
        :param master:
        :param label:
        :param on_change:
        """
        self.master = master
        self.root = tk.Frame()
        self.var = tk.StringVar()
        self.var.set(choices[0])
        self.choices = choices
        self.label = tk.Label(self.root,text=label,anchor="e")
        self.menu =  tk.OptionMenu(self.root,self.var,*choices,command=lambda *a:on_change())
        self.label.pack(side=tk.LEFT)
        self.menu.pack(side=tk.LEFT)
        # self.te.bind("<FocusOut>",self._lostFocus)
    def __getattr__(self, item):
        return getattr(self.root,item)

    @property
    def value(self):
        return self.var.get()
    @value.setter
    def value(self,value):
        return self.var.set(value)

class LabeledScale(object):
    def __init__(self,master,label,minVal=0,maxVal=100,on_change=lambda:1):
        """
        :param master:
        :param label:
        :param on_change:
        :param validate_fn: must return None if validation succeeds, return string error message if validation fails
        """
        self.master = master
        self.root = tk.Frame()
        self.var = tk.StringVar()
        self.label = tk.Label(self.root,text=label,anchor="se")
        self.scale =  tk.Scale(master=self.root,from_=minVal,to=maxVal,orient=tk.HORIZONTAL,command=lambda *a:on_change())
        self.label.pack(side=tk.LEFT,expand=True,fill="y")
        self.scale.pack(side=tk.LEFT)

    def __getattr__(self, item):
        return getattr(self.root,item)
    def setRange(self,minVal=0,maxVal=100):
        self.scale.configure(from_=minVal,to=maxVal)
    @property
    def value(self):
        return self.scale.get()
    @value.setter
    def value(self,value):
        print("SET VAL:",value)
        return self.scale.set(value)
class URADForm:
    def __init__(self,master,defaults=None):
        defaults = defaults or {}
        self.root = master
        def ttt():
            print("CHANGED:mode",self.entry1.value)
            rangeF0={
                '1':[5,245]
            }.get(self.entry1.value,[5,195])
            self.entry2.setRange(*rangeF0)
            self.lbl_mode.configure(text={
                '1':'MEAS: Speed',
                '2':'MEAS: Distance',
                '3':'MEAS: Distance + Speed',
                '4':'MEAS: Distance + Speed',
            }.get(self.entry1.value))
        def fff():
            print("CHANGED:f0")
            maxBW = 245 - int(self.entry2.value)
            self.entry3.setRange(50,maxBW)
        def dist_change():
            BW = float(self.entry3.value)
            Ns = int(self.entry4.value)
            txt = "MAX THEORETICAL DISTANCE\nDmax=75*(Ns/BW) = %0.3fs"%(75.0*(Ns/BW))
            self.lbl_dist.configure(text=txt)
        def MAKECONFIG():
            print("CREATE CONFIG")
        def TESTCONFIG():
            print("TEST CONFIG")

        self.entry1 = LabeledMenu(master,"mode",list("1234"),on_change=ttt)
        self.entry1.grid(row=0,column=0)
        self.lbl_mode = tk.Label(master,text="Speed")
        self.lbl_mode.grid(row=0,column=1)
        self.entry2 = LabeledScale(master,"f0",5,245,on_change=fff)
        self.entry2.grid(row=1,column=0)
        self.entry3 = LabeledScale(master,"BW",50,240,on_change=dist_change)
        self.entry3.grid(row=1,column=1)
        self.entry4 = LabeledScale(master,"Ns",50,200,on_change=dist_change)
        self.entry4.grid(row=2,column=0)
        self.entry5 = LabeledScale(master,"Alpha",3,25)
        self.entry5.value = 10 #.scale.set(10)
        self.entry5.grid(row=2,column=1)
        self.generate_btn  = tk.Button(master, text="Test Config", command=TESTCONFIG)
        self.generate_btn2 = tk.Button(master, text="Commit Config", command=MAKECONFIG)
        self.generate_btn.grid(row=3,column=0)
        self.generate_btn2.grid(row=3,column=1)
        self.lbl_dist = tk.Label(master,text="MAX THEORETICAL DISTANCE\nDmax=75*(Ns/BW) = %0.3fs",justify="left")

        #self.entry6 = LabeledMenu(f1,"Ntar",choices=['1','2','3','4','5'])
        self.lbl_dist.grid(row=4,column=0,columnspan=2)
        # self.entry6.pack()




if __name__ == "__main__":
    root = tk.Tk()
    f = URADForm(root)
    root.mainloop()
