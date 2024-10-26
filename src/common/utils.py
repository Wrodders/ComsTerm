import serial, serial.tools.list_ports

def scanUSB() -> list:
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return ports

