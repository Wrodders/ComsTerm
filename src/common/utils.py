import serial, serial.tools.list_ports



def scanUSB( key: str) -> list:
    ports = [p.device for p in serial.tools.list_ports.comports() if key.lower() in p.device]
    return ports