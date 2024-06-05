# ComsTerm - Distributed Systems Graphical User Interface

## Intro
ComsTerm came up as a need for other projects, mainly robotics / audio. I needed a way to live inspect data streams and and call rpc functions on embedded and distributed devices. 
I often found myself writing  patches of coded to deal with sockets and streaming and processing of data.
ComsTerm is an ongoing project as my projects requeiremtes change however i do aim to steadily drive it down towards something stable. 

## Problem Statement

I Found the ROS2 Learning curve too steep to take alongside the  C++ curve. Back to basics and decided to build what i need when i need it. Using the right tool for the job and a modular incremental approach. Plus ROS2 ive found to be hard to get working on low memory devices like pi zeros 

Cheap Wifi modules are a great way to add higherlevel distributed control  to many simple "robotics projects. Even better is they are powerful enough for some extra onboard pre processing. ESP32's RPiZero2W ect. 
Many robotics computing systems can be through of as data pipelines, with sensors, mcus, offload accelerators, onboard performance metrics and users providing the input data streams. What makes the Robot is how this data is interpreted and acted upon. 

System Monitoring is key to development.

## Design Methodology
ComsTerm, Communications Terminal, Acts as s data visualizer for a robotic system. Providing insights into the operation of complex systems. Mainly a learning exercise in distributed realtime systems. 

Collection of applications written as needed. Applications use common modular components to interact with each other, spawn processes, write to device drivers ect. 

Pub Sub Architecture allows multiple processes/apps exchange data. **Investigate Shared Memory**

Apps may have 3 Methods of Usage. 
* GUI
* Command Line parameters - for launch scripts
* TUI

Apps Are Black Box Nodes which explicitly provide a PUB | SUB   map. 


Simple explicit **RPC framework**, easily execute and pass data to different programs. - ***Embedded AT CMD style***
Nodes all have the following basic PUB | SUB | CMD topics 

CMD Topics are Subscriptions to the global "cmd bus". 

Type | Topic | Format | Description|
-----|-------|--------|------------| 
PUB  |NODE_ID/CMD_RET|CMD_ID RET| Return Value of a command
SUB  |CMD/NODE_ID    | CMD_ID PARAM| Command NODE_ID to execute CMD_ID with PARAMs

Nodes all have the following basic COMMAND

CMD_ID | Description |
-------| ----------- |
ID | Returns Node Id, (Device Id if Hardware Node)
PUBS| Returns table of PUBs
SUBS|  Returns table of SUBs
CMDs|  Returns table of CMDs

Apps further subscribe to topics a data inputs, process and publish over topics. 
Apps and any Node maintain a protocol for its PUBs and CMDs parameters in the maps.
The map can be queried though the commands, and returned through CMD Ret.
This is used for verifying user input. 

Multiple simple  components can either be used independently, demanding each their own process, or a more complex App can group these together under a single process, thus potential improving memory usage. 

## Architecture

### Core Applications

#### **Device Manager**
Interacts with custom hardware devices (USART, CAN ) using firmware defined protocols. 

**Devices** Identify custom hardware with firmware id. Protocol for device is loaded. 
CMD Protocol is AT CMD style. Hardware capable of duplex data transmission  have PUB topics and protocols loaded. 
These are independent Sub-Apps which can be used standalone or as part of another App. 

Opens, Scans, Closes device files, Parses, Publishes data over ZMQ 

#### **Console** 
Terminal UI text console for veiwing live topic data streams, multiple topics added in coloums. ***(grepable?)***. 


### System

ZMQ used for PUB-SUB Socket middleware. Communication is done over IPC UNIX domain socket. ***ipc:///tmp/COMSTERM***

GUI implemented with pyQt6 for quick development. **Find better wy to intergrate zmq and qt loop**. Each GUI has own worker thread that bridges the zmq qt loops. 








