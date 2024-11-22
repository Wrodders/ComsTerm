from multiprocessing import Process, Pipe
import pygame
import time

def ps4_joystick_handler(pipe):
    """Subprocess function to handle PS4 joystick."""
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        pipe.send({"error": "No joystick detected"})
        return

    joy = pygame.joystick.Joystick(0)
    joy.init()
    pipe.send({"status": "connected", "name": joy.get_name()})

    try:
        while True:
            if pipe.poll():  # Check for messages from parent
                command = pipe.recv()
                if command == "STOP":
                    print("PS4 process stopping...")
                    break  # Exit the loop

            pygame.event.pump()  # Poll joystick events
            # Get joystick axes (e.g., left stick: axis 0 & 1, right stick: axis 2 & 3)
            rx = round(joy.get_axis(2)*1.4,3)  # Right stick horizontal
            ry = round(joy.get_axis(3)*0.6,3)  # Right stick horizontal
            if abs(rx) < 0.05 : 
                rx = 0
            if (abs(ry) < 0.1):
                ry =0
            
            axis_data = {
                "rx": rx,
                "ry": ry,
            }

            pipe.send(axis_data)  # Send data to parent
            time.sleep(0.1)

    finally:
        pygame.quit()   
        print("PS4 process exited cleanly.")
