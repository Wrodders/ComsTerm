import pygame
from client.controller import ZMQCommander
from core.ZmqDevice import Endpoint, Transport, ZmqPub
import time
def main():
    # Initialize pygame's joystick module

    pygame.init()
    pygame.joystick.init()

    cmdr = ZMQCommander(paramRegMapFile="paramRegMap.csv")
    cmdr.publisher = ZmqPub(endpoint=Endpoint.LOCAL_CMD, transport=Transport.TCP)
    cmdr.publisher.pub.connect()

    # Ensure at least one joystick is connected
    if pygame.joystick.get_count() == 0:
        print("No joystick detected. Please pair your PS4 controller and try again.")
        return

    # Connect to the first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Connected to joystick: {joystick.get_name()}")

    try:
        rx_last = 0
        ry_last = 0
        while True:
            # Process pygame events
            pygame.event.pump()
            # Get joystick axes (e.g., left stick: axis 0 & 1, right stick: axis 2 & 3)
            rx = -round(joystick.get_axis(2)*1.4,3)  # Right stick horizontal
            ry = round(joystick.get_axis(3)*0.6,3)  # Right stick horizontal
            if abs(rx) < 0.05 : 
                rx = 0
            if (abs(ry) < 0.1):
                ry =0
            cmdr.pushSetCmd("AT",str(rx))
            cmdr.pushSetCmd("VT",str(ry))
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
