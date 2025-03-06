import serial, serial.tools.list_ports

import subprocess

def scanUSB() -> list:
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return ports


import subprocess

def check_darkmode():
    """Checks DARK/LIGHT mode of macos."""
    cmd = 'defaults read -g AppleInterfaceStyle'
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    return bool(p.communicate()[0])