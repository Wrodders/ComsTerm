import tkinter as tk
from tkinter import Tk, ttk
from tkinter import messagebox, Menu, filedialog
from datetime import datetime
import webbrowser
import time
import asyncio

import serial
import serial.tools.list_ports
import csv
global connected
connected = False
target_port = 'NONE'
baudrate = 9600
msgReceived  = ""
validCommands = []
profiles = []
receivingData = False # 
ser = None
global count
count = 0
User  = ""

# Gui Class will Always Log to Output Console
# Other functions will log to terminal 
## Valid Commands are in the format, CommandName,Value(if applicable)
# serial messages will be sent with start,stop chars <message> and a delemiter ',' if applicable

async def timecheck(t):
    await asyncio.sleep(t)


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
        for row in reader:
            validCommands.append(row)

def Check_valid_Command(msg,app,output):
    msgArgs = [i for i in msg.split(',')]
    msgName = msgArgs.pop(0)
    commandNames = [validCommands[i][0] for i in range(len(validCommands))]
    target_index = [i for i,x in enumerate(commandNames) if x == msgName]
    if len(target_index) == 0:
        print("Invalid command")
        error_msg = "<<!! Invalid command, input: 'help' for a list of commands"
        app.update_CommandOutput(error_msg,output)
        return False
    validFormat = [i for i in validCommands[target_index[0]] if i != '']
    if (1+len(msgArgs)) == len(validFormat):
        return True
    else:
        error_msg = '<<!! '+ 'Invalid command format try: ' + ', '.join(validFormat)
        app.update_CommandOutput(error_msg,output)
        return False


def help_Command(app):
    msg ="<< List of All Commands available, CommandName and syntax, check Documentation for more information"
    app.update_CommandOutput(msg,text_output)
    for i in range(len(validCommands)):
        msg = validCommands[i][0] + ':' + validCommands[i][1]
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


def send_Serial(app,cmdN,value):
    global connected, target_port
    # todo check if msg is valid command
    #create serial message
    s_msg = '<' + str(cmdN) + ',' + value + '>'
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
        l_user = ttk.Label(frame, text = User)
        e_input = ttk.Entry(frame)
        b_Connect = ttk.Button(frame,text="Connect", command = lambda: self.handel_Connect_Command(e_input.get()))
        b_Disconnect = ttk.Button(frame,text="Disconnect", command = lambda: self.handle_Disconnect_Command())
        b_auto = ttk.Button(frame,text="Auto Connect", command = lambda: auto_find_Port(e_input))
        l_Connection_Name = ttk.Label(frame, text="Connected to: ", foreground = 'yellow')
        global l_ConnectionPort
        l_ConnectionPort = ttk.Label(frame,text=target_port, foreground = "yellow")

        l_user.grid(column=2, row = 1,)
        e_input.grid(column=0, row= 0)
        b_Connect.grid(column=1, row=0, sticky=tk.EW)
        b_Disconnect.grid(column=1,row=1)
        b_auto.grid(column =2, row = 0)
        l_Connection_Name.grid(column =1, row = 2)
        l_ConnectionPort.grid(column =2, row =2)
    
    def create_presetCommands_Window(self):
        global count 
        global presetWindow
        global text_output
        
        if count ==1:
            presetWindow.focus()
        else:
            presetWindow = tk.Toplevel(self)
            presetWindow.geometry("380x200")
            presetWindow.resizable(False, False)
            presetWindow.title("Preset Commands")
            b_jog90 = ttk.Button(presetWindow,text="Jog 90 degrees", command= lambda: self.handle_Send_Command("jog,90",text_output))
            b_jog45 = ttk.Button(presetWindow,text="Jog 45 degrees", command= lambda: self.handle_Send_Command("jog,45",text_output))
            b_jog180 = ttk.Button(presetWindow,text="Jog 180 degrees", command= lambda: self.handle_Send_Command("jog,180",text_output))
            b_rev10 = ttk.Button(presetWindow,text="10 revs", command= lambda: self.handle_Send_Command("rev,10",text_output))
            b_rev2 = ttk.Button(presetWindow,text="2 revs", command= lambda: self.handle_Send_Command("rev,2",text_output))
            b_rev1 = ttk.Button(presetWindow,text="1 rev", command= lambda: self.handle_Send_Command("rev,1",text_output))
            b_abs90 = ttk.Button(presetWindow,text="Abs 90 degrees", command= lambda: self.handle_Send_Command("abs,90",text_output))
            b_abs10 = ttk.Button(presetWindow,text="Abs 10 degrees", command= lambda: self.handle_Send_Command("abs,10",text_output))

            b_jog90.grid(column =0, row =0,sticky = tk.NSEW)
            b_jog180.grid(column = 0, row =1, sticky= tk.NSEW)
            b_jog45.grid(column = 0, row = 2, sticky = tk.NSEW)
            b_rev10.grid(column = 1, row = 0, sticky = tk.NSEW)
            b_rev2.grid(column = 1, row = 1, sticky = tk.NSEW)
            b_rev1.grid(column = 1, row = 2, sticky = tk.NSEW)
            b_abs90.grid(column = 2, row = 0, sticky = tk.E)
            b_abs10.grid(column = 2, row = 1, sticky = tk.NSEW)
            presetWindow.protocol("WM_DELETE_WINDOW", lambda: self.handel_quit(presetWindow))
            count +=1

    def create_login(self):
        login_win = tk.Toplevel(self)
        login_win.geometry("300x100")
        login_win.title("Login")
        login_win.resizable(False,False)
        b_login = ttk.Button(login_win, text = "Login",command = lambda: self.handle_login(e_uname.get(), e_pswd.get(), login_win, label))
        e_uname = ttk.Entry(login_win, width = 20)
        e_pswd = ttk.Entry(login_win, width = 20, show="*")
        e_pswd.bind("<Return>", (lambda entry:self.handle_login(e_uname.get(), e_pswd.get(), login_win, label)))
        l_uname = ttk.Label(login_win, text = "Username: ")
        l_pswd = ttk.Label(login_win, text = "Password: ")
        label  = ttk.Label(login_win, text= "")
        b_login.grid(column =0,row=3, columnspan =2, sticky = tk.NSEW, padx = (10,10))
        l_uname.grid(column =0, row =0, sticky = tk.NSEW, padx = (10,10))
        l_pswd.grid(column =0, row =1, sticky = tk.NSEW, padx = (10,10))
        e_uname.grid(column =1, row=0, sticky = tk.NSEW)
        e_pswd.grid(column =1, row =1, sticky = tk.NSEW)
        label.grid(column =1, row=2, sticky = tk.NSEW)



    def handle_Send_Command(self, msg, output):
        #Posts command to OutputStream
        if connected:
            if msg != "" :
                if msg != "help": 
                    if Check_valid_Command(msg,self,output):
                        command_msg = ">> " + msg # >> Message Sent
                        self.update_CommandOutput(command_msg, output)
                        # map word command to command number
                        if ',' in msg:
                            cmd = ','.join(msg.split(",")[:-1])
                            value = (msg.split(",")[-1])
                        else:
                            cmd = msg
                            value = ''
                        for i, x in enumerate(validCommands):
                            if cmd in x:
                                cmdN =  i
                        send_Serial(self,cmdN,value)
                else:
                    help_Command(self)
                    # clears commmand input fields
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


    def update_CommandOutput(self,msg,output):
        output.config(state = "normal")
        output.insert('end', msg + '\n') # writes msg to terminal 
        output.config(state = 'disabled')  # closes terminal again

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
    ValidCommandsRead()
    UsersRead()
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    Start_Application()
