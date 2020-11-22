import time

import numpy
import pandas

try:
    import tkinter as tk
except:
    import Tkinter as tk
class Trace:
    def __init__(self,points=None, color='#000000'):
        # print("SET:",points)
        self.set_points(points)
        self.color = color

    def add_point(self,xVal,yVal):
        print("ADD :",xVal,yVal)
        self.set_points(numpy.array(self.points.tolist()[-99:]+[[xVal,yVal]]))

        print("ADD(2):(last= %s)" % (self.points[-1]))
    def set_points(self,values):
        if values is not None:
            self.points = numpy.array(values) if not isinstance(values, (numpy.ndarray, numpy.generic) ) else values
            x = self.points[:, 0]
            y = self.points[:, 1]
            self.xRange = [x.min(), x.max()]
            self.yRange = [y.min(), y.max()]
        else:
            self.points = numpy.array([])
            self.xRange = [float("inf"), float("-inf")]
            self.yRange = [float("inf"), float("-inf")]
        # print("POINTS SET",self.points, self)
    def set_color(self,color):
        self.color = color
    def translate(self,width,height,offsetX=0,offsetY=0,flat=False):
        # print(self, self.points)
        if len(self.points) == 0:
            return numpy.array([])
        if len(self.points) == 1:
            return numpy.array([[width//2,height//2]])
        #for x,y in self.points:
        p1 = self.points
        x = p1[:, 0]
        y = p1[:, 1]
        xr = self.xRange[1]-self.xRange[0]
        yr = self.yRange[1] - self.yRange[0]
        nx = ((x-self.xRange[0])/float(xr))*width + offsetX
        ny = height - height*((y-self.yRange[0])/float(yr)) + offsetY
        return numpy.array([nx,ny]).T if not flat else numpy.array([nx,ny]).T.flatten()


    def draw_point(self,canvas,x,y):
        def _create_circle(self, x, y, r, **kwargs):
            return self.create_oval(x - r, y - r, x + r, y + r, **kwargs)
        pass
    def draw(self,canvas,draw_area_size,offset):
        # print("DRAW:",self,self.points)
        print("DRAW:(last= %s)"%(self.points[-1]))
        p2 = self.translate(draw_area_size[0],draw_area_size[1],offset[0],offset[1])
        # print("P2:",p2)
        # for pt in p2:
        #     print("PT:",pt)
        #     self.draw_point(canvas,pt[0],pt[1])

        canvas.create_line(*p2.flatten(),fill=self.color,width=2)

class ChartPanel:
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    def __init__(self,master,width,height,
                 keepPoints=300,
                 xAxisLabel="x",yAxisLabel="y",
                 margin=None,
                 colors=None
                 ):
        self.root=master
        self.hiddenTraces = set()
        self.colors = colors or self.colors[:]
        self.keepPoints = keepPoints
        self.xAxisLabel = xAxisLabel
        self.yAxisLabel = yAxisLabel
        self.margin = margin or [35,10,5,25]
        if isinstance(self.margin,int):
            self.margin = [self.margin]*4
        if len(self.margin) == 1:
            self.margin = [self.margin[0]]*4
        if len(self.margin) == 2:
            self.margin = self.margin[:2] + self.margin[:2]
        # print self.margin
        self.cwidth = width-self.margin[0]-self.margin[2]
        self.cheight = height-self.margin[1]-self.margin[3]
        self.width = width
        self.height = height
        self.xRange = [float("inf"),float("-inf")]
        self.yRange = [float("inf"),float("-inf")]
        self.canvas = tk.Canvas(self.root,width=width,height=height)
        self.data = {}
    def hideTrace(self,trace_index):
        self.hiddenTraces.add(trace_index)
    def showTrace(self,trace_index):
        if trace_index in self.hiddenTraces:
            self.hiddenTraces.remove(trace_index)
    def addTrace(self,initialPoints,color=None):
        color = color or self.colors[len(self.data)]
        # print(self.data)
        self.data[len(self.data)] = Trace(initialPoints[:],color)
        # print(self.data,self.data[0].points)
    def update(self):
        t0 = time.time()
        self._drawAxes()
        print("Took %0.2fs to redraw chart"%(time.time()-t0))
    def _drawAxes(self,xOffset=0):

        # blit white background
        self.canvas.create_rectangle(-1,-1,self.width+2,self.height+2,fill="#FFFCFC",outline=None)
        for trace in sorted(self.data.keys()):
            # print(self.data[trace],self.data[trace].points)
            if trace not in self.hiddenTraces:
                self.data[trace].draw(self.canvas,[self.cwidth,self.cheight],[self.margin[0],self.margin[1]])
        # axis line y
        self.canvas.create_line(self.margin[0],self.margin[1],self.margin[0],self.margin[1]+self.cheight,self.cwidth+self.margin[0],self.margin[1]+self.cheight)
        # axis line x
        # self.canvas.create_line(self.cheight,5,self.cheight,5)
        self._drawXTicks()
        self._drawYTicks()
    def _drawXTicks(self):
        # self.canvas.create_line(13,5,15,5)
        # self.canvas.create_line(13,self.cheight//2+5,15,self.cheight//2+5)
        # self.canvas.create_line(13,self.cheight+5,15,self.cheight+5)
        # self.canvas.create_line(self.cwidth//2+15,self.cheight+5,self.cwidth//2+15,self.cheight+8)
        # self.canvas.create_line(self.cwidth+15,self.cheight+5,self.cwidth+15,self.cheight+5)
        start = int(time.time())-300
        start2 = start + 60 - start%60
        ticks = numpy.arange(start,time.time(),60)
        m,s = divmod(ticks,60)
        m = m % 60
        self.xRange = min([t.xRange[0] for t in self.data.values()]),max([t.xRange[1] for t in self.data.values()])

        # tick_labels = numpy.array2string(m,formatter={'float_kind':"{0:02.0f}:00".format})
        tick_values = m
        xr = self.xRange[1]- self.xRange[0]
        for i,tick_val in enumerate(m):
            time_str =  "%02d:00"%tick_val
            time_val = ticks[i]
            offset_time = (time_val - self.xRange[0])
            ratio = (offset_time/xr)
            xpos = ratio*self.cwidth+self.margin[0]
            ypos = self.margin[1]+self.cheight
            self.canvas.create_line(xpos,ypos,xpos,ypos+5)
        # print("TICKS:",ticks,)
    def _drawYTicks(self):
        self.yRange = min([t.yRange[0] for t in self.data.values()]), max([t.yRange[1] for t in self.data.values()])
        yr = self.yRange[1] - self.yRange[0]
        ys = numpy.linspace(self.yRange[0],self.yRange[1],3)
        # print(ys)
        for y in ys:
            ratio = (y-self.yRange[0])/yr
            ypos = self.cheight - ratio*self.cheight + self.margin[1]
            xpos = self.margin[0]
            self.canvas.create_line(xpos,ypos,xpos - 5,ypos)
            self.canvas.create_text([xpos-6,ypos],text="%0.0f"%y,anchor="e")
    def get_trace(self,trace_pk=0):
        return self.data[trace_pk]
    def set_points(self,tracePk,points):
        numpy.array(points)
        self.get_trace(tracePk).set_points(points)


    def __getattr__(self, item):
        return getattr(self.canvas,item)

if __name__ == "__main__":
    root = tk.Tk()
    cp = ChartPanel(root,320,80)
    x = int(time.time())-numpy.arange(299,0,-1)
    y = (numpy.random.uniform(-0.2,0.2,299) + numpy.sin(numpy.linspace(0,8,299)*2) + 2) * 100
    y2 = (numpy.random.uniform(-0.2,0.2,299) * numpy.cos(numpy.linspace(0,8,299)*2) + 2) * 100
    seconds_in_day = x%86400
    h,m = divmod(seconds_in_day,60)
    m,s = divmod(m,60)
    # print(h,m,s)
    cp.hideTrace(0)
    cp.addTrace(zip(x,y))
    cp.addTrace(zip(x,y2))
    cp.update()
    cp.pack()
    def addPoint():
        if numpy.random.random() > 0.9:
            if cp.hiddenTraces:
                cp.hiddenTraces.pop()
            else:
                cp.hideTrace(numpy.random.choice(cp.data.keys()))
        t = cp.get_trace(0)
        t1 = cp.get_trace(1)
        t1.add_point(time.time(),t1.points[-1][1]+numpy.random.uniform(-0.2,0.2))
        t.add_point(time.time(),t.points[-1][1]+numpy.random.uniform(-1.2,1.2))
        cp.update()
        root.after(1000,addPoint)

    addPoint()
    root.mainloop()
