from asyncio import base_tasks
import tkinter as tk
from tkinter import Tk, ttk
from tkinter import messagebox, Menu, filedialog
from datetime import datetime
import webbrowser
import numpy as np
from numpy import random
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor,Button

plt.ion()

import serial
import serial.tools.list_ports
import csv
import subprocess


global connected
connected = False
target_port = 'NONE'
target_address = 'NONE'
baudrate = 9600
msgReceived  = ""
validCommands = []
cmdNames = []
profiles = []
validAddress = []
receivingData = False # 
ser = None
global count
count = 0
User  = ""
xy_point = [0,0]

# Gui Class will Always Log to Output Console
# Other functions will log to terminal 
## Valid Commands are in the format, CommandName,Value(if applicable)
# serial messages will be sent with start,stop chars <message> and a delemiter ',' if applicable




### Graphign Functions###

def graph_ZX():
    fig  =  Figure(figsize=(5,5), dpi=100)
    x = np.arange(0,4*np.pi,0.1) #start stop step
    y = np.sin(x)
    plot1 = fig.add_subplot(111)
    plot1.plot(x,y)
    return fig


def graph_XY():
    plt.rcParams["figure.figsize"] = [7.00, 3.50]
    plt.rcParams["figure.autolayout"] = True
    def mouse_event(event):
        print('x: {} and y: {}'.format(event.xdata, event.ydata))
    fig = plt.figure()
    cid = fig.canvas.mpl_connect('button_press_event', mouse_event)
    
    
    x = np.linspace(-10, 10, 100)
    y = np.exp(x)

    plt.plot(x, y)

    plt.show()  

def onClick(event,fig):
    xy_point[0]= event.x
    xy_point[1]= event.y
    fig.canvas.draw()

    



#### Message Parsing Functions ####

def UsersRead():
    with open( 'Users.csv','r') as UsersFile:
        reader = csv.reader(UsersFile)
        global profiles
        for row in reader:
            profiles.append(row)
def ValidCommandsRead():
    with open( 'Commands.csv','r') as CommandFile:
        reader = csv.reader(CommandFile)
        global validCommands 
        global cmdNames
        for row in reader:
            validCommands.append(row)
        cmdNames = [i[0] for i in validCommands]
        
def LookUpAddress():
    with open( 'addressBook.csv','r') as AddressFile:
        reader = csv.reader(AddressFile)
        global validAddress
        validAddress = [i for line in reader for i in line]


def Check_valid_Message(msg,app,output):
    # assumes msg != ''
    global cmdNames;target_address
    msgArgs =  msg.split(',') # split msg string into array 
    msglen = len(msgArgs) # gets number of arguments in message 

    #TOD0 check for preseitn valid address 
    if (msgArgs[0]  in validAddress):
        #check if msg has a valid msgAddress part
        if (msglen >= 2 and msgArgs[1] != ''):# checks if msg has inputted a value for command
            # find index of inputted command in valid commands
            target_index = [i for i,x in enumerate(cmdNames) if x == msgArgs[1]]
            if len(target_index) == 0:
                # inputted command not found
                print("Invalid command")
                error_msg = "<<!! Invalid command, input: 'help' for a list of commands"
                app.update_CommandOutput(error_msg,output)
                return False
            # check if the rest of the message is in a valid format based on the command
            validFormat = [i for i in validCommands[target_index[0]] if i != '']
                # checks if command selected requires arguments
            if (msglen == 1+len(validFormat) ):
                    # checks if the inout has the right amount of delimeters
                    # protects against execessive commas in msgContent part of message
                    if ((len(validFormat) >=2)):
                        # checks if inputted command requires any arguments
                        if (bool(msgArgs[2])):
                        # protects agains sending commands withought arguments
                            pass
                        else:
                            print("Invalid command")
                            error_msg = '<<!! '+ 'Invalid message format try: ' + ', '.join(validFormat)
                            app.update_CommandOutput(error_msg,output)
                            return False

                        if '/' in validFormat[1]:
                            #checks if command selected requires multiple arguments
                            if '/' in msgArgs[2]:
                                #checks if inputted msgContent contains a arguments delimeter
                                return True
                            else:
                                print("Invalid command")
                                error_msg = '<<!! '+ 'Invalid message format try: ' + ', '.join(validFormat)
                                app.update_CommandOutput(error_msg,output)
                                return False
                        else:
                            return True
                    else:
                        print("hello")
                        return True
            else:
                print("Invalid command")
                error_msg = '<<!! '+ 'Invalid message format try: ' + ', '.join(validFormat)
                app.update_CommandOutput(error_msg,output)    
                return False    
            
        else:
            print("Invalid command")
            error_msg = "<<!! Invalid command, input: 'help' for a list of commands"
            app.update_CommandOutput(error_msg,output)
            return False
    else:
        print('No Address')
        error_msg = "<<!! [Error] message must have a target address, input 'addressbook' or 'help'"
        app.update_CommandOutput(error_msg,output)
        return False   


def help_Command(app):
    msg ="<< List of All Commands available, CommandName and syntax, check Documentation for more information"
    app.update_CommandOutput(msg,text_output)
    for i in range(0,len(validCommands)):
        msg = validCommands[i][0]+":"+validCommands[i][1]
        app.update_CommandOutput(msg,text_output)

def get_address(app):
    msg = "<< List of all Valid Addresses, check Documentation for more information"
    app.update_CommandOutput(msg,text_output)
    for i in range(0,len(validAddress)):
        msg = validAddress[i]
        app.update_CommandOutput(msg,text_output)





###### Serial ReadWrite Functionality
def open_Serial(port,app):
    global ser
    global connected
    try:
        with serial.Serial() as ser:
            ser.baudrate = baudrate
            ser.port = port
            ser.bytesize = serial.EIGHTBITS
            ser.parity = serial.PARITY_NONE
            ser.stopbits = serial.STOPBITS_ONE
            ser.timeout = 1
            ser.xonxoff = False
            ser.rtscts = False,
            ser.dsrdtr = False,
            ser.gridwriteTimeout = 2
        ser.open()
        s_msg = "<:,a>"
        try:
            ser.write(s_msg.encode('utf-8')) # send initial connection handshake 
        except serial.SerialException:
            msg = ">>!! [Error] Device not configured"
            connected = False
    except serial.SerialException:
        msg = ">> [Error] Unable to open serial port at: " + port
        app.update_CommandOutput(msg,text_output)
        connected = False
    except TypeError as e:
        app.update_CommandOutput(str(e),text_output)
        connected = False
    try:
        ch = ser.readline().decode('utf-8')
        if ch== 'b':
            connected =True
            msg = "<<>> Connection Successful--------------------"
            app.update_CommandOutput(msg,text_output)
        else:
            connected = False
            msg = "<<>> Connection Failed--------------------"
            app.update_CommandOutput(msg, text_output)
    except serial.PortNotOpenError:
        msg = ">> [Error] Port not open"
    except serial.SerialException:
        msg = ">> [Error] Unable to open serial port at: " + port
        app.update_CommandOutput(msg,text_output)
        connected = False
        

def close_Serial():
    #Todo close serial port safely 
    global ser
    ser.flushInput()
    ser.flushOutput()
    ser.close()

    global target_port
    target_port = "NONE"
    print("serial closed")

def auto_find_Port(e_input):
    messagebox.showerror("Info", "Ensure Device is disconnected,  then press ok")
    i_ports = list(serial.tools.list_ports.comports())
    messagebox.showerror("Info", "Connect Device to USB port,  then press ok")
    f_ports = list(serial.tools.list_ports.comports())
    global target_port
    try:
        new_port = [i for i in f_ports if i not in i_ports]
        port = str(new_port[0]).split(' ', 1)
        target_port = port[0]
        msg = "Found Device on port " + target_port
        messagebox.showerror("Info",msg)
        e_input.delete(0,tk.END)
        e_input.insert(0,target_port)

    except (IndexError, ValueError):
        messagebox.showerror("Info", "No new Device Found")


def send_Serial(app,addrN,cmdN,u_content):
    global connected, target_port
    # create serial message <msgAddressID,function callID,function arguments>
    s_msg = "<"+addrN +","+cmdN +","+u_content+">"
    # todo check if msg is valid command
    #if ser.isOpen() == False:
        #ser.open()
    try:
        ser.write(s_msg.encode('utf-8'))
    except serial.SerialException:
        connected = False
        target_port= 'NONE'
        l_ConnectionPort.configure(text=target_port)
        msg = ">>!! [Error] Device not configured"
        app.update_CommandOutput(msg,text_output)
    #print("message sent")


def read_Serial(self):
    # open serial thread and update monitor 
    print("serial read")
    for i in range(0,10):
        msgReceived = i
        print (msgReceived)
        return msgReceived







class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.create_Main_Window()

    def create_Main_Window(self):
        self.title("ComsTerm")
        screen_size = '725x650'
        self.geometry(screen_size)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: self.handel_quit(self))
        global Commandframe
        global Connectionsframe


        Commandframe = ttk.Frame(self, borderwidth = 0.1, relief = "sunken", padding = 3 )
        Connectionsframe = ttk.Frame(self, borderwidth = 0.1, relief = "sunken", padding = 3 )

        Connectionsframe.grid(column =0, row =0, sticky = tk.NSEW)
        Commandframe.grid(column = 0, row=1, sticky = tk.NSEW)
        
        self.create_login()
        self.withdraw()
        

    def create_Menu(self,frame):
        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Presets", command= lambda:self.create_presetCommands_Window())
        filemenu.add_command(label="Load Script")
        filemenu.add_command(label="Save Session", command = lambda:self.handle_Save())
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command= lambda:self.handel_quit())
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Find")
        helpmenu.add_command(label="Open Documentation", command= lambda: self.handle_Documentation())
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=menubar)


    def create_CommandWindow(self,windowframe):
        global text_output

        windowframe.grid_columnconfigure(0, weight=2)
        windowframe.grid_rowconfigure(0, weight=1)

        b_send  = ttk.Button(windowframe, text = "Send", command = lambda: self.handle_Send_Command(e_input.get(), text_output))
        e_input = ttk.Entry(windowframe, width = 20)
        e_input.bind("<Return>",(lambda event: self.handle_Send_Command(e_input.get(), text_output)))
        text_output = tk.Text(windowframe, height=40, width=100)
        scroll_bar = ttk.Scrollbar(windowframe, orient ='vertical',  command = text_output.yview)
        text_output['yscrollcommand'] = scroll_bar.set
        text_output.config(state="disabled")
        

        text_output.grid(column = 0, row =0, columnspan = 2, sticky=tk.NSEW)
        scroll_bar.grid(column = 1, row =0, sticky = tk.E)
        b_send.grid(column = 1, row = 1, sticky =tk.W)
        e_input.grid(column = 0, row = 1, sticky = tk.NSEW)


    def create_ConnectionsWindow(self,frame):
        global User 
        l_user = ttk.Label(frame, text = "Welcome: " + User, foreground='green')
        e_input = ttk.Entry(frame, width=20)
        b_Connect = ttk.Button(frame,text="Connect", command = lambda: self.handel_Connect_Command(e_input.get()))
        b_Disconnect = ttk.Button(frame,text="Disconnect", command = lambda: self.handle_Disconnect_Command())
        b_auto = ttk.Button(frame,text="Auto Connect", command = lambda: auto_find_Port(e_input))
        l_Connection_Name = ttk.Label(frame, text="Connected to: ", foreground = 'yellow')
        l_ConnectionPort = ttk.Label(frame,text=target_port, foreground = "yellow")
        e_addr = ttk.Entry(frame)
        b_addr = ttk.Button(frame,text="Set Msg Address", command = lambda: self.handel_preset_addr(e_addr.get()))
        r1 = ttk.Radiobutton(frame,text="Serial", value = 1)
        r2 = ttk.Radiobutton(frame,text="Ethernt", value = 2)
        r3 = ttk.Radiobutton(frame,text="Wifi", value = 3)


        e_input.grid(column = 0, row = 0, sticky = tk.NSEW)
        e_addr.grid(column = 0, row = 1, sticky = tk.NSEW)
        b_auto.grid(column = 0, row = 2, sticky = tk.NSEW)

        b_Connect.grid(column = 1, row = 0, sticky = tk.NSEW)
        b_addr.grid(column = 1, row = 1, sticky = tk.NSEW)
        l_Connection_Name.grid(column = 1, row = 2, sticky = tk.E)

        b_Disconnect.grid(column = 2, row = 0, sticky = tk.NSEW)
        l_ConnectionPort.grid(column = 2, row = 2, sticky = tk.W)

        r1.grid(column = 3, row = 0, sticky = tk.W)
        r2.grid(column = 3, row = 1, sticky = tk.W)
        r3.grid(column = 3, row = 2, sticky = tk.W)

        l_user.grid(column = 4, row = 0, sticky = tk.W)


    
    def create_presetCommands_Window(self):
        global count 
        global presetWindow
        global text_output
        
        if count ==1:
            presetWindow.focus()
        else:
            presetWindow = tk.Toplevel(self)
            presetWindow.geometry("600x400")
            #presetWindow.resizable(False, False)
            presetWindow.title("Motion Controller")
            # create Frames 
            JointCtrlFrame = ttk.Frame(presetWindow, borderwidth = 0.1, relief = "sunken", padding = 3 )
            PosCtrlFrame = ttk.Frame(presetWindow, borderwidth = 0.1, relief = "sunken", padding = 3 )
            EndEffectorFrame = ttk.Frame(presetWindow, borderwidth = 0.1, relief = "sunken", padding = 3 )
            PoseTrackFrame = ttk.Frame(presetWindow, borderwidth = 0.1, relief = "sunken", padding = 3 )

            # confgure grid 
            presetWindow.rowconfigure(0, weight = 1)
            presetWindow.rowconfigure(1, weight = 3)
            presetWindow.rowconfigure(2, weight = 4)
            # position frames in window
            JointCtrlFrame.grid(column = 0, row = 0, sticky = tk.NSEW)
            PosCtrlFrame.grid(column = 1, row = 0, sticky = tk.NSEW)
            EndEffectorFrame.grid(column = 0, row = 1, columnspan=2, sticky = tk.NSEW)
            PoseTrackFrame.grid(column = 0, row = 2, columnspan=2, sticky = tk.NSEW)


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

            # create widgets for Position Control Frame
            l_title = ttk.Label(PosCtrlFrame, text = "Position Control")
            b_sleep = ttk.Button(PosCtrlFrame, text = "Sleep", command = lambda: self.handel_PosControll(0))
            b_unsleep = ttk.Button(PosCtrlFrame, text = "Unsleep", command = lambda: self.handel_PosControll(1))
            b_extend = ttk.Button(PosCtrlFrame, text = "Extend", command = lambda: self.handel_PosControll(2))
            b_claw = ttk.Button(PosCtrlFrame, text = "Claw Position", command = lambda: self.handel_PosControll(3))

            # position widgets in Position Control Frame
            l_title.grid(column = 0, row = 0, columnspan =2)
            b_sleep.grid(column = 0, row = 1, sticky = tk.NSEW)
            b_unsleep.grid(column = 1, row = 1, sticky = tk.NSEW)
            b_extend.grid(column = 0, row = 2, sticky = tk.NSEW)
            b_claw.grid(column = 1, row = 2, sticky = tk.NSEW)

            # create widgets for End Effector Frame



            presetWindow.protocol("WM_DELETE_WINDOW", lambda: self.handel_quit(presetWindow))
            count +=1

    def create_login(self):
        login_win = tk.Toplevel(self)
        login_win.geometry("300x110")
        login_win.title("Login")
        login_win.resizable(False,False)
        login_win.protocol("WM_DELETE_WINDOW", lambda: self.handel_quit(self))
        b_login = ttk.Button(login_win, text = "Login",command = lambda: self.handle_login(e_uname.get(), e_pswd.get(), login_win, label))
        e_uname = ttk.Entry(login_win, width = 20)
        e_pswd = ttk.Entry(login_win, width = 20, show="*")
        e_pswd.bind("<Return>", (lambda entry:self.handle_login(e_uname.get(), e_pswd.get(), login_win, label)))
        l_uname = ttk.Label(login_win, text = "Username: ")
        l_pswd = ttk.Label(login_win, text = "Password: ")
        label  = ttk.Label(login_win, text= "")
        b_login.grid(column =0,row=3, columnspan =2, sticky = tk.NSEW, padx = (10,10), pady = (0,10))
        l_uname.grid(column =0, row =0, sticky = tk.NSEW, padx = (10,10))
        l_pswd.grid(column =0, row =1, sticky = tk.NSEW, padx = (10,10))
        e_uname.grid(column =1, row=0, sticky = tk.NSEW)
        e_pswd.grid(column =1, row =1, sticky = tk.NSEW)
        label.grid(column =1, row=2, sticky = tk.NSEW)


### Command Functions ###

    def handle_Send_Command(self, msg, output):
        #Posts command to OutputStream
        if 1==1:
            if msg != "" :
                if msg != "help": 
                    if msg != "addressbook":
                        if Check_valid_Message(msg,self,output):
                            # all messages should have at min address,command
                            u_msg = ">> " + msg # >>User Message Sent
                            self.update_CommandOutput(u_msg, output)

                            # map word command to command number
                            u_addr = msg.split(',')[0]
                            u_cmd = u_msg.split(',')[1]
                            if (msg.count(',') ==1):
                                # msg contains command that does not require arguments
                                u_content = '';
                            else:
                                u_content = msg.split(',')[2]
                            
                            cmdN = cmdNames.index(u_cmd)
                            addrN = validAddress.index(u_addr)
                            # call send serial msg command
                            send_Serial(self,addrN,cmdN,u_content)
                    else:
                        get_address(self)
                else:
                    help_Command(self)
                    # clears command input fields
        else:
            msg = ">>!! No Device Connected"
            self.update_CommandOutput(msg, output)

    def handel_Connect_Command(self,port):
        if port != "":
            if not connected:
                msg = ">> Connecting to: " + port
                # verify that port is a valid port number
                self.update_CommandOutput(msg, text_output)
                #Call open Serial Command
                open_Serial(port,self)
                if connected:
                    l_ConnectionPort.configure(text=port) # update Connection label
            else:
                msg = ">>!! Connection to " +port+ " already exists"
                self.update_CommandOutput(msg, text_output)

        else:
            msg = ">>!! Error, Enter a valid Port address"
            self.update_CommandOutput(msg, text_output)


    def handle_Disconnect_Command(self):
        if connected:
            print("Disconeting from ", target_port)
        else:
            print("Terminal is not Connected to a Port")


    def handel_Jog_Command(self,val):
        subprocess.call(" python test.py 1", shell=True)




    def update_CommandOutput(self,msg,output):
        output.config(state = "normal")
        output.insert('end', msg + '\n') # writes msg to terminal 
        output.config(state = 'disabled')  # closes terminal again


    def handel_preset_addr(self,address):
        if address != "":
            if address in validAddress:
                # update label
                # update address
                target_address = address
                msg = ">> Address set to: " + address
                self.update_CommandOutput(msg, text_output)
            else:
                target_address = 'NONE'
                msg = ">>!! Error, Enter a valid Address"
                self.update_CommandOutput(msg, text_output)

    def handel_quit(self,window):
        global count
        msg = "Do you want to quit " + window.title() 
        res = messagebox.askquestion("askquestion", msg)
        if res == "yes" :
            if window.title() == "ComsTerm":
                print("Quitting Serial Ports")
                # place holder for closing serial 
            count = 0
            window.destroy()
        elif res == "no":
            pass
    
    def handle_login(self,un, pw, win, label):
        global User
        users  = [i[0] for i in profiles]
        pswds = [i[1] for i in profiles]
        if un in users:
            idx  = users.index(un)
            c_pswd = pswds[idx]
            if c_pswd == pw:
                User = un
                win.destroy()
                # create  main Gui Windows
                self.deiconify()
                self.create_CommandWindow(Commandframe)
                self.create_ConnectionsWindow(Connectionsframe)
                self.create_Menu(Connectionsframe)
            else:
                label.config(text = " Wrong Password") 
        else: 
            label.config(text = " Wrong Username") 




    def handle_Save(self):
        global text_output
        sessionContent = text_output.get('1.0', 'end-1c')
        name =  datetime.today().isoformat() 
        name = User+ "-" + name 
        f = filedialog.asksaveasfile(mode='w', defaultextension=".txt",initialfile= name )
        if f is None: 
            return
        f.write(sessionContent)
        f.close() 

    def handle_Documentation(self):
        webbrowser.open('https://winstonrodigo.atlassian.net/wiki/spaces/DEV/overview', new = 2, autoraise = True)

def Start_Application():
    print("Starting ComsTerminal")
    # background checks for system settings
    # Starts Threads and Queues
    # reads in Valid Commands form file
    # Reads in Valid Addresses
    ValidCommandsRead()
    UsersRead()
    LookUpAddress()
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    Start_Application()
