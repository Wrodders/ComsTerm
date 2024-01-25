# Robot Graphical User Interface

The GUI provides a centralized system for running commands and receiving data form the robot. 

The whole system is structured under a Pub/Sub data stream + Req/Rep Command pattern. 

Written in Python using PYQT5 it provides 3 main components: 
### Console: 
Receives data over topics

### Commander:  
Sends commands to a device or runs CLI tools. Can also control the GUIs parameters and settings. 

Once a Device Binds to the GUI it can send the ID command which returns the available commands for a device and the protocols of the data it publishes under topics. This allows for a Data and Command Graph to be built dynamically. 

### ViewPort
Emmbeded simple graphical CLI tools like Plotter & VidStream into the GUI. 

