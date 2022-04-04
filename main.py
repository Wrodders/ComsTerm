import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import ipaddress
from datetime import datetime
import serial.tools.list_ports


target_port = "None" # global variable

def Auto_Connect_Command():
    messagebox.showerror("Info", "Ensure Device is disconected,  then press ok")
    i_ports = list(serial.tools.list_ports.comports())
    messagebox.showerror("Info", "Connect Device to USB port,  then press ok")
    f_ports = list(serial.tools.list_ports.comports())
    try:
        new_port = [i for i in f_ports if i not in i_ports]
        target_port = str(new_port[0]).split(' ', 1)
        target_port = target_port[0]
    
    except (IndexError, ValueError):
        messagebox.showerror("Info", "No new Port Found")
    #target_port = new_port[0].serial.tools.list_ports.ListPortInfo.device
    
    
    





class HandelLogger():
    # this will handdel the logging functionalite
    def create_log(self, msg):
        now  = datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        log = timestamp+' >> '+msg
        return log

#def valid_Command():


        





class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.create_Main_Window()

####### Window Creation Handlers #####
    def create_Main_Window(self):
        self.title("Robo Interface DEV")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        screen_size = str(screen_width)+"x"+str(screen_height)
        self.geometry(screen_size)
        # create panned windows 
        p1 = tk.PanedWindow(self, bd =3, showhandle = True, orient = "horizontal")
        p2 = tk.PanedWindow(p1, bd =3,showhandle = True,orient = "vertical")
        p3 = tk.PanedWindow(p1, bd= 3, showhandle = True )
        p4 = tk.PanedWindow(p1, bd= 3, showhandle = True, orient = 'vertical')
        

        # add panes to Main Window
        p1.pack(fill="both", expand = 1)
        p1.add(p2) 
        p1.add(p4)
        p2.add(p3)
        # create frames for each pannel
        connections_frame = ttk.Frame(p3, borderwidth = 0.1, relief = "sunken", padding = 3)
        swUpdate_frame = ttk.Frame(p1,borderwidth = 0.1, relief = "sunken", padding = 3)
        commands_frame = ttk.Frame(p2, borderwidth = 0.1, relief = "sunken", padding = 3)
        serialMonitor_frame = ttk.Frame(p4, borderwidth = 0.1, relief = "sunken" , padding = 3)
        preset_Commands_frame = ttk.Frame(p4, borderwidth = 0.1, relief = "sunken", padding = 3)

    
        #add frames to panels
        p2.add(commands_frame, stretch="always")
        p3.add(connections_frame)
        p4.add(preset_Commands_frame)

        p1.add(swUpdate_frame)
        p4.add(serialMonitor_frame, stretch="always")
        
        # call functions 
        self.create_Connections_Frame(connections_frame)
        self.create_swUpdate_Frame(swUpdate_frame)
        self.create_Commands_Frame(commands_frame)
        self.create_serialMonitor_Frame(serialMonitor_frame)
        self.create_presetCommands_Frame(preset_Commands_frame)

    def create_Connections_Frame(self, frame):
        #####create widgets################################
        c_mode = tk.StringVar() # conection mode selected 
        # Serail UART Mode
        Serial_radio = ttk.Radiobutton(frame,value = '1',text='Serial',variable=c_mode,
            command=lambda: print(c_mode.get()))
        Serial_radio.grid(column=0, row=1, sticky=tk.W)
        # TCP Ethernet Mode
        TCP_radio = ttk.Radiobutton(frame,value= '2',variable=c_mode,text='TCP',
            command=lambda: print(c_mode.get()))
        TCP_radio.grid(column=0, row=2, sticky=tk.W)
        for widget in frame.winfo_children():
            widget.grid(padx=0, pady=5)
        c_mode.set("1") # sets default connection to Serial

        b_Connect = ttk.Button(frame,text="Connect", command=lambda: self.Connect_Command(e_input.get(), c_mode.get(), l_ConnectionPort))
        b_Disconnect = ttk.Button(frame,text="Disconnect")
        b_auto = ttk.Button(frame,text="Auto Connect", command=lambda: Auto_Connect_Command())
        e_input = ttk.Entry(frame)
        l_Connection_Name = ttk.Label(frame, text="Connected to: ", foreground = 'yellow')
        l_ConnectionPort = ttk.Label(frame,text=target_port, foreground = "yellow")
        
        #layout widgets 
        e_input.grid(column=0, row= 0)
        b_Connect.grid(column=1, row=0, sticky=tk.EW)
        b_Disconnect.grid(column=1,row=1)
        b_auto.grid(column =2, row = 0)
        l_Connection_Name.grid(column =1, row = 2)
        l_ConnectionPort.grid(column =2, row =2)

    def create_swUpdate_Frame(self, frame):
        screen_size = self.winfo_screenwidth()
        frame_size = screen_size/25
        var = tk.StringVar()
        button1 = ttk.Button(frame,text="Download")
        button2 = ttk.Button(frame,text="Upload") 
        button3 = ttk.Button(frame,text="Revert")
        button4 = ttk.Button(frame,text="Scan")
        input = ttk.Entry(frame,textvariable=var, width = 30)
        ScanOutput = tk.Text(frame, height=10, width=int(frame_size), bg = "grey3")
        TargetOutput = tk.Text(frame, height=10, width=int(frame_size))

        input.grid(row = 0, column = 0, columnspan = 2, sticky=tk.W)
        button1.grid(row =0, column=1, sticky=tk.E) # download
        button2.grid(row = 1, column = 0, sticky=tk.E) # upload
        button3.grid(row=1, column=1, sticky=tk.W) # revert
        button4.grid(row =1, column =0, sticky=tk.W) # scan


        
        ScanOutput.grid(column=0, row=2, columnspan = 2, sticky=tk.W)
        TargetOutput.grid(column=0, row=3, columnspan= 2, sticky=tk.W)
        TargetOutput.config(state="disabled")
        ScanOutput.config(state="disabled")

    def create_presetCommands_Frame(self,frame):
        c_mode = tk.StringVar() # conection mode selected 
        # Open Loop Control  Mode
        radio1 = ttk.Radiobutton(frame,value = 'Value 1',text='Open Loop Control',variable=c_mode,
            command=lambda: print(c_mode.get()))
        radio1.grid(column=0, row=0, sticky=tk.W, pady = 5)
        # Closed Loop Controll Mode
        radio2 = ttk.Radiobutton(frame,value= 'Value 2',variable=c_mode,text='Closed Loop Control',
            command=lambda: print(c_mode.get()))
        radio2.grid(column=0, row=1, sticky=tk.W, pady = 5)
        # Gravity Compensation
        radio3 = ttk.Radiobutton(frame,value = 'Value 3',text='Gravity Compensation',variable=c_mode,
            command=lambda: print(c_mode.get()))
        radio3.grid(column=0, row=2, sticky=tk.W, pady = 5)

        button1 = ttk.Button(frame,text="90")
        button2 = ttk.Button(frame,text="180")
        button3 = ttk.Button(frame,text=" 360")
        button4 = ttk.Button(frame,text="45")
        button5 = ttk.Button(frame,text="20")
        button6 = ttk.Button(frame,text="60")

        button1.grid(column =2, row = 0)
        button2.grid(column = 3, row =0)
        button3.grid(column = 2, row =1)
        button4.grid(column = 3, row = 1)
        button5.grid(column = 4, row = 0)
        button6.grid(column = 4, row= 1)

    def create_Commands_Frame(self, frame):
        screen_size = self.winfo_screenwidth()
        frame_size = screen_size/22
        e_input = ttk.Entry(frame,width = int(frame_size/2))
        e_input.grid(column=0, row=1, sticky= tk.NSEW)
        b_send = ttk.Button(frame,text="Send", command = lambda: self.Send_Command(e_input.get()))
        b_send.grid(column=1, row=1, sticky= tk.W)
        output = tk.Text(frame,height = 30, width = int(frame_size))
        output.grid(column=0, row=0, sticky= tk.NSEW, columnspan = 2)
        output.config(state="disabled")
        #(screen_size/6)

        frame.grid_rowconfigure(0, minsize=200, weight=1)
        frame.grid_columnconfigure(0, minsize=200, weight=1)
        frame.grid_columnconfigure(1, weight=1)


####### Event Handlers ###############

    def create_serialMonitor_Frame(self,frame):
        var = tk.StringVar()
        screen_size = self.winfo_screenwidth()
        frame_size = screen_size/22
        output = tk.Text(frame,height = 30, width = int(frame_size))
        output.config(state="disabled")
        b_display = ttk.Button(frame,text="Display Data", command = lambda: self.display_data_Command(output, 'hello'))
        b_start_log = ttk.Button(frame,text="Log Data to File")
        b_stop_log = ttk.Button(frame,text="Save and Stop Logs")

        e_input = ttk.Entry(frame, textvariable = var)

        output.grid(column=0, row=0, sticky= tk.NSEW, columnspan = 2)
        b_display.grid(column=0, row=1, sticky= tk.NSEW)
        b_start_log.grid(column =1, row =1, sticky= tk.E)
        b_stop_log.grid(column =1, row =2, sticky = tk.E)
        e_input.grid(column =0, row =2, sticky=tk.NSEW)
        
        frame.grid_rowconfigure(0, minsize=200, weight=1)
        frame.grid_columnconfigure(0, minsize=200, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
    def Connect_Command(self,var, c_mode, l_port):
        # validates entry input 
        # starts Serial Thread
        if len(var) != 0: 
            if c_mode == "2": # if connection is in TCP mode
                try:
                    target_port = ipaddress.ip_address(var)
                    # TODO call the BeginTCP Function on thread
                    l_port.config(text = target_port) # update port connection info
                except ValueError:
                    messagebox.showerror("Error", "Enter a valid IP Address ")
            if c_mode =="1": #  if connection is in Serial Mode
                # open pyserial port at usb 
                print("opening serial port")
        else:
            messagebox.showerror("Error", "Please enter a Port Address")

    def Disconnect_Command(self,c_mode):
        # handels Disconnection process
        # clears the connected to var 
        # calls the disconect connection function based on c_mode 
        #closes serial thread 
        print("Disconected")
    
    def Send_Command(self,msg,terminal):
        if valid_Command():
            self.display_data_Command(terminal, msg)
             # calls Serial write command
    def display_data_Command(self, terminal, msg):

        log = logHandler.create_log(msg)
        terminal.config(state = 'normal') # opens ternimal to write 
        terminal.insert('1.0', log + '\n') # writes msg to terminal 
        terminal.config(state = 'disabled')  # closes terminal again



################################################################
if __name__ == "__main__":
    print("Statring Application")
    app = GUI()
    logHandler = HandelLogger() # initial log handler
    app.mainloop()