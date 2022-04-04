# Importing Libraries
import serial
import time
ser = serial.Serial(port='/dev/cu.usbmodem105655601', baudrate=115200, timeout=.1)
ser.reset_input_buffer()



#// message format  <Command,Value>



while True:
    b_send = input("enter value:") # enters usr blink value
    msgSend  = "<Blink," + b_send + ">" # creates message in desierd format
    print(msgSend)
    ser.write(msgSend.encode('utf-8')) # send message to ser Object
    time.sleep(1)

