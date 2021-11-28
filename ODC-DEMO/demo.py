import sys
import os
#might to change following line fron where you are in the repo, works for me but might not on another workspace? - Ivan
sys.path.append(os.path.abspath('mind-speech-interface-ssvep/SSVEP-Interface/Pages'))
import circle_stimuli as Stim

import time
import random
import threading


from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QGridLayout,

)

def thread_function(stop):
    print("start")
    
    order = [0,1,2,3,4,5,6,7,8,9,10,11]
 
    for trial in range(2):
        print("=====Trial "+str(trial+1)+"=====")
        random.shuffle(order)
        print(order)
        for stimPeriod in range(13):
            
            if stop():
                print("thread ended")
                break

            time.sleep(0.5) #allow previously turned on stim to be on for x seconds

            if stimPeriod > 0: #if not first stim, turn off prev stim
                stim[order[stimPeriod-1]].toggleOff()
            
            time.sleep(0.5) #x second break before turning on next stim

            if stimPeriod < 12:
                currentStim = stim[order[stimPeriod]]
                currentStim.toggleOn()
                
                color = str(currentStim.rValue)+","+str(currentStim.gValue)+","+str(currentStim.bValue)
                if color == "255,255,255":
                    color = "white"
                elif color == "0,0,255":
                    color = "blue" 
                elif color == "0,255,0":
                    color = "green"
                print(f"{color}\t{currentStim.freqHertz}Hz")

        time.sleep(1) #x second break before next trial
    print ("all trials finished")            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = QWidget()
    demo.setWindowTitle('Flashing Stim 1')

    layout = QGridLayout()

    demo.setStyleSheet("background-color: black;")
    titleLabel = QLabel('<h1 style="text-align:center; color: white">ODC-DEMO</h1>')
    layout.addWidget(titleLabel, 0, 0, 1, 4)

    global stim
    stim = []

    #white stims
    stim.append(Stim.CircleFlash(20,255,255,255))
    stim.append(Stim.CircleFlash(18,255,255,255))
    stim.append(Stim.CircleFlash(16,255,255,255))
    stim.append(Stim.CircleFlash(14,255,255,255))
    stim.append(Stim.CircleFlash(12,255,255,255))
    stim.append(Stim.CircleFlash(10,255,255,255))
    stim.append(Stim.CircleFlash(8,255,255,255))
    stim.append(Stim.CircleFlash(6,255,255,255))
    
    #blue stims
    stim.append(Stim.CircleFlash(11,0,0,255))
    stim.append(Stim.CircleFlash(7,0,0,255))

    #green stims
    stim.append(Stim.CircleFlash(9,0,255,0))
    stim.append(Stim.CircleFlash(5,0,255,0))


    random.shuffle(stim)

    for row in range (3):
        for col in range (4):
            stimNum = row*4+col
            stim[stimNum].toggleOff()
            layout.addWidget(stim[stimNum],row+1,col)
            

    
    demo.setLayout(layout)
    demo.resize(500, 500)
    demo.show()

    stopThread = False
    x = threading.Thread(target=thread_function, args=(lambda: stopThread,))
    x.start()
    


    try:
        sys.exit(app.exec_())
    except SystemExit:
        stopThread = True
        print('Closing Window...')


