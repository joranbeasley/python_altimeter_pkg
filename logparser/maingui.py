import tkinter as tk
class Layout:
    def quit(self):
        print("QUIT")
        self.root.quit()
    def hello(self):
        print("Load File")

    def __init__(self,master):
        self.root = master
        self.altitude_graph = tk.Label(self.root,text="ASD")
        self.altitude_graph.pack()

        # self.menubar = tk.Menu(self.root)
        # self.menubar.add_command(label="_Load", command=self.hello)
        # self.menubar.add_command(label="&Quit!", command=self.quit)
        # self.root.config(menu=self.menubar)
class MenuBar:
    def on_quit(self):
        self.root.quit()
    def on_open(self):
        print("OPEN FILE:")

    def __init__(self,master):
        self.root = master
        self.menubar = tk.Menu(self.root)

        # create a pulldown menu, and add it to the menu bar
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Open", command=self.on_open)

        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=self.menubar)

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.layout()
    def layout(self):
        self._menu = MenuBar(self.root)
        self._layout = Layout(self.root)
    def main_loop(self):
        self.root.mainloop()
MainApp().main_loop()
