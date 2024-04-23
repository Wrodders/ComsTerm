# ComsTerm - Distributed Systems Graphical User Interface

## Intro
ComsTerm came up as a need for other projects, mainly robotics / audio, i often found myself writing  patches of coded to deal with sockets and streaming displaying of data.

ComsTerm is an ongoing project as my projects requeiremtes change however i do aim to steadily drive it down towards something stable. 

 
## Architecture

Devices: 
* Act as endpoints to hardware connected devices.
* Run an IO loop in a thread and communicate with the physical device over its defined medium, Serial, UPP/TCP, ect. 
* Maintains a structure of all Publishing Topics and Commands supported by device.
* Publishes valid messages over IPC through deviceID/message.
* Processes Commands through a Queue - Only one "Master".
* Parses Messages according to the defined protocol.
  

GUI Components:
* UI elements for displaying multi-modal data in different formats.
* Dynamic sub/unsub from all available topics in graph.
* Individual Windows - Act as HMI model UI
* Worker I/O thread bridges to Zmq


## Installation

### Requirements
* python 3
* git
* 


```bash

git clone https://github.com/Wrodders/ComsTerm
cd ComsTerm

```


