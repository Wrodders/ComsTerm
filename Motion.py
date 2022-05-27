
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk  
from tkinter import Tk, ttk
import numpy as np




CurrentPos= np.array([0,0])
TargetPos = np.array([])
global ax
global canvas

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.createMainWindow()
    
    def createMainWindow(self):
        self.title("ComsTerm")
        screen_size = '850x750'
        self.geometry(screen_size)
        self.resizable(False, False)

        self.createFrames()


    def createFrames(self):
        mainWin = self
        # create Frames 
        JointCtrlFrame = ttk.Frame(mainWin, borderwidth = 0.1, relief = "sunken", padding = 3 )
        PosCtrlFrame = ttk.Frame(mainWin, borderwidth = 0.1, relief = "sunken", padding = 3 )
        EndEffectorFrame = ttk.Frame(mainWin, borderwidth = 0.1, relief = "sunken", padding = 3 )
        CoordsFrame = ttk.Frame(mainWin, borderwidth = 0.1, relief = "sunken", padding = 3 )
        

        # confgure grid 

        mainWin.rowconfigure(1, weight = 4)
        mainWin.columnconfigure(2, weight = 1)
    
        # position frames in window
        JointCtrlFrame.grid(column = 0, row = 0, sticky = tk.NSEW)
        PosCtrlFrame.grid(column = 1, row = 0, sticky = tk.NSEW)
        EndEffectorFrame.grid(column = 0, row = 1, columnspan=2, sticky = tk.NSEW)
        CoordsFrame.grid(column=2,row=1,sticky=tk.NSEW)
        
        # create widgets for End Effector Frame
        self.createGraphXY(EndEffectorFrame)

        # create widgets for Joint Control Frame
        l_tJoint = ttk.Label(JointCtrlFrame, text = "Target Joint: ")
        e_tJoint = ttk.Entry(JointCtrlFrame)
        e_input = ttk.Entry(JointCtrlFrame, width = 10)
        b_jog = ttk.Button(JointCtrlFrame, text = "Jog", command = lambda: self.handel_Jog_Command(e_input.get()))
        b_runTo = ttk.Button(JointCtrlFrame, text = "Run To", command = lambda: self.handel_RunTo_Command(e_input.get()))
        b_stop = tk.Button(JointCtrlFrame, text = "Stop",bg = 'red', command = lambda: self.handel_Stop_Command())
        b_revolve = ttk.Button(JointCtrlFrame, text = "Revolve", command = lambda: self.handel_Revolve_Command(e_input.get()))

        # position widgets in Joint Control Frame
        l_tJoint.grid(column = 0, row = 0, sticky = tk.W)
        e_tJoint.grid(column = 1, row = 0, columnspan= 2, sticky = tk.EW)
        e_input.grid(column = 0, row = 1, sticky = tk.W)
        b_jog.grid(column = 1, row = 1, sticky = tk.W)
        b_runTo.grid(column = 2, row = 1, sticky = tk.W)
        b_stop.grid(column = 0, row = 2, sticky = tk.W)
        b_revolve.grid(column = 1, row = 2, sticky = tk.W)

        # create widgets for Pose Control Frame
        l_title = ttk.Label(PosCtrlFrame, text = "Position Control")
        b_sleep = ttk.Button(PosCtrlFrame, text = "Sleep", command = lambda: self.handel_PosControll(0))
        b_unsleep = ttk.Button(PosCtrlFrame, text = "Unsleep", command = lambda: self.handel_PosControll(1))
        b_extend = ttk.Button(PosCtrlFrame, text = "Extend", command = lambda: self.handel_PosControll(2))
        b_claw = ttk.Button(PosCtrlFrame, text = "Claw Position", command = lambda: self.handel_PosControll(3))

        # position widgets in Pose Control Frame
        l_title.grid(column = 0, row = 0, columnspan =2)
        b_sleep.grid(column = 0, row = 1, sticky = tk.NSEW)
        b_unsleep.grid(column = 1, row = 1, sticky = tk.NSEW)
        b_extend.grid(column = 0, row = 2, sticky = tk.NSEW)
        b_claw.grid(column = 1, row = 2, sticky = tk.NSEW)
        
        # create widgets for Coordinate Controll Frame
        l_title = ttk.Label(CoordsFrame, text = "Coordinate Control")
        l1 = ttk.Label(CoordsFrame, text = "X")
        l2 = ttk.Label(CoordsFrame, text = "Y")
        l3 = ttk.Label(CoordsFrame, text = "Z")
        l4 = ttk.Label(CoordsFrame, text = "End Effector Angle: ")
        l5 = ttk.Label(CoordsFrame, text = "Trajectory Type: ")
        e1 = ttk.Entry(CoordsFrame, width = 5)
        e2 = ttk.Entry(CoordsFrame, width = 5)
        e3 = ttk.Entry(CoordsFrame, width = 5)
        e4 = ttk.Entry(CoordsFrame, width = 5)
        c1 = ttk.Combobox(CoordsFrame, state="readonly")
        c1['values'] = ["Linear", "Quadratic", "Besian",]
        c1.current(0)
        b_move = ttk.Button(CoordsFrame, text = "Move To", command = lambda: self.Updateplot(e1.get(),e2.get(),e3.get()))

        # position widgets in Coordinate Controll Frame
        l_title.grid(column = 1, row = 0, columnspan =2, sticky = tk.EW)
        e1.grid(column = 0, row = 1, sticky = tk.NSEW)
        e2.grid(column = 1, row = 1, sticky = tk.NSEW)
        e3.grid(column = 2, row = 1, sticky = tk.NSEW)
        l1.grid(column = 0, row = 2)
        l2.grid(column = 1, row = 2)
        l3.grid(column = 2, row = 2)
        l4.grid(column = 0, row = 3, columnspan=2,sticky = tk.NSEW)
        e4.grid(column = 2, row = 3, sticky = tk.NSEW)

        l5.grid(column = 0, row = 4, columnspan= 2, sticky = tk.NSEW)
        c1.grid(column = 0, row = 5, columnspan=3, sticky = tk.NSEW)
        b_move.grid(column = 0, row = 6, columnspan = 3, sticky = tk.NSEW)

        
        



    def createGraphXY(self,frame):
        global fig
        global ax
        global canvas
        fig =plt.figure(figsize=(3, 3.5))
        ax=fig.add_subplot(projection='3d')
        setupAxies(ax)
        canvas=FigureCanvasTkAgg(fig,frame)
        canvas.get_tk_widget().grid(row=0,column=1)
        ax.plot(0,0,0,linestyle="None",marker='o', color='red')
        canvas.draw()


    def Updateplot(self,xval,yval,zval):
        print(zval)
    
        ax.clear()
        setupAxies(ax)         # clear axes from previous plot

        

        ax.plot(int(xval),int(yval),int(zval),linestyle="None",marker='o', color='red')
        canvas.draw()


def setupAxies(ax):
    plt.grid()
    plt.xlim([-10, 10])
    plt.ylim([-10, 10])
   


app=Application()
app.mainloop()