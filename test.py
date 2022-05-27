import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import numpy as np
import math as math





CurrentPos= np.array([1,1])
TargetPos = np.array([])

def onclick(event):
    global TargetPos; CurrentPos
    if event.button == 1:
        TargetPos = [event.xdata, event.ydata]
        xval= [CurrentPos[0], TargetPos[0]]
        yval= [CurrentPos[1], TargetPos[1]]
        

        #clear frame
        plt.clf()
        plt.grid()
        plt.xlim([-10, 10])
        plt.ylim([-10, 10])
        plt.plot(xval,yval, ":")
        plt.scatter(CurrentPos[0],CurrentPos[1],c="blue"); # mantain curretn postion
        plt.scatter(TargetPos[0],TargetPos[1],c='red'); # target position
        plt.draw() #redraw




def onpress(event):
    global CurrentPos; TargetPos

    if event.key == 'a':
    #clear frame
        plt.clf()
        plt.grid()
        plt.xlim([-10, 10])
        plt.ylim([-10, 10])

    #update current position
    CurrentPos = [TargetPos[0], TargetPos[1]]

    #plot current position
    plt.scatter(CurrentPos[0],CurrentPos[1],c="blue"); # plot new curretn postion
    plt.draw()



fig,ax=plt.subplots(figsize=(6, 6))
plt.grid()
plt.xlim([-10, 10])
plt.ylim([-10, 10])
plt.subplots_adjust( bottom = 0.2)
ax.scatter(CurrentPos[0],CurrentPos[1],c="b"); 

fig.canvas.mpl_connect('button_press_event',onclick)
fig.canvas.mpl_connect('key_press_event',onpress)













plt.show()
plt.draw()