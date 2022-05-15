from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QGridLayout,
    QFrame,
    QVBoxLayout
)
from PyQt5.QtCore import QRect,Qt
from PyQt5.QtGui import QPainter, QBrush, QPen
from time import time, sleep, strftime, localtime
from brainflow.board_shim import BoardShim, BrainFlowInputParams
import sys, random, threading, datetime
import circle_stimuli as Stim
import numpy as np
import pandas as pd
import argparse, socket, pickle

# Trial Settings
START_DELAY_S = 20 # 20 Seconds
NUM_TRIALS = 5 # 5 Trials
INDICATOR_TIME_VALUE_S = 5 # 5 Seconds
TRIAL_BREAK_TIME = 120 # 120 second
STIM_PERIOD_TRIALS = 12 # 12 for the 12 stimuli per trial
STIM_TIME = 5

color_code_order = []
color_freq_order = []

def display_procedure(stop, board, args):

    if testing:
        START_DELAY_S = 1 
        NUM_TRIALS = 2
        INDICATOR_TIME_VALUE_S = 1
        TRIAL_BREAK_TIME = 1
        STIM_PERIOD_TRIALS = 3
        STIM_TIME = 1
    else:
        START_DELAY_S = 20 # 20 Seconds
        NUM_TRIALS = 5 # 5 Trials
        INDICATOR_TIME_VALUE_S = 5 # 5 Seconds
        TRIAL_BREAK_TIME = 120 # 120 second
        STIM_PERIOD_TRIALS = 12 # 12 for the 12 stimuli per trial
        STIM_TIME = 5    
        
    f = open("ODC-DEMO/demo_data/" + filename + ".txt", 'a')  # modify depending on CWD
    f.write(f"Session at {datetime.datetime.now()} \n\n")
    start_time = time()
    board.start_stream(450000, args)
    sleep(1)
    startDelay = START_DELAY_S
    for x in range(startDelay):
        label.setText(labelTxt(f"Starting in {str(startDelay-x)}"))
        sleep(1)
    order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    for trial in range(NUM_TRIALS):  # number of trials (5 times)
        print("=====Trial "+str(trial+1)+"=====")
        f.write("\n=====Trial "+str(trial+1)+"=====\n")
        
        # each trial will have a different order of stimulus
        random.shuffle(order)
        print(order)
        
        color_code_order.append(0)
        color_freq_order.append(0)
        board.insert_marker(0.666) # insert marker for start AS WELL AS BETWEEN TRIALS

        for stimPeriod in range(STIM_PERIOD_TRIALS):
            color_code_order.append(0)
            color_freq_order.append(0)
            # just for testing otherwise the thread keeps running if you close the window
            if stop():
                break
            currentStim = stim[order[stimPeriod]]
            stimLabel = preStimIndicators[order[stimPeriod]]

            # log color and hz to terminal
            color = str(currentStim.rValue)+"," + \
                str(currentStim.gValue)+","+str(currentStim.bValue)
            if color == "255,255,255":
                color = "white"
                colorCode = "01"
            elif color == "0,0,255":
                color = "blue"
                colorCode = "02"
            elif color == "0,255,0":
                color = "green"
                colorCode = "03"
            print(f"{color}\t{currentStim.freqHertz}Hz")

            # log code to file
            f.write(f"{currentStim.id:02} " + colorCode +
                    f" {currentStim.freqHertz:02}\n")
            color_code_order.append(colorCode)
            color_freq_order.append(currentStim.freqHertz)

            # indicate stimuli to focus on / display indicator
            currentStim.toggleIndicator(True)
            label.setText(labelTxt(f"Keep you eyes where the red circle is."))
            
            for x in range(int(INDICATOR_TIME_VALUE_S)):
                stimLabel.setText(labelTxt(str(INDICATOR_TIME_VALUE_S - x)))
                sleep(1)
            stimLabel.setText(labelTxt(""))
            
            currentStim.toggleIndicator(False)
            board.insert_marker(0.666)   # insert marker for in between flashes (null)
            
            for x in range(STIM_PERIOD_TRIALS):
                stim[x].toggleOn()
            sleep(STIM_TIME)  # set length of simulation period (5s)
            board.insert_marker(0.666)   # insert marker for stimuli flash (individual)   
      
            # turn off all stimuli and prepare for next trial
            for x in range(STIM_PERIOD_TRIALS):
                stim[x].toggleOff()
        
            # Corresponding timestamp creation
            session_timestamp = []
            timestamp_rows = np.shape(data[data_index])[0] 

            # One-time millisecond extraction
            ms = repr(start_time).split('.')[1][:3]

            for each_timestamp_index in range(timestamp_rows):

                # Convert Unix time to desired timestamp format
                formatted_start_time = time.strftime("%Y-%m-%d %H:%M:%S.{} %Z".format(ms), time.localtime(start_time))[:23]
                session_timestamp.append( formatted_start_time )
                
                # Add 8ms to formatted_start_time 
                ms = int(ms) + 4

                # Work-around for floating point error from adding 8 ms
                if ms > 999:
                    rem_ms = str(ms - 1000)
                    start_time += 1  
                    ms = '00' + rem_ms
                else:
                    ms = str(ms)
                    if len(str(ms)) == 1:
                        ms = '00' + ms
                    elif len(str(ms)) == 2:
                        ms = '0' + ms
                    else:
                        pass

            timestamp.append(session_timestamp)
            data_index += 1            

        # just for testing otherwise the thread keeps running if you close the window
        if stop():
            break
        
        for x in range(int(TRIAL_BREAK_TIME)):
            label.setText(
                labelTxt(f"Time before next trial: ({TRIAL_BREAK_TIME-x})"))
            sleep(1)

    color_code_order.append(0)
    color_freq_order.append(0)
    data = board.get_board_data().transpose()

    label.setText(
                labelTxt(f"Trials finished"))
    print("all trials finished")
    f.write("Session finished.\n\n")
    f.close()
    print(color_code_order)
    print(board.board_id)

    board.stop_stream()
    if not testing:
        duration = time()-start_time
        generate_test_report(board, duration, data, color_code_order, color_freq_order)
    df = post_process(data, start_time, color_code_order, color_freq_order, board.board_id)
    try:
        if testing:
            df.to_csv("test.csv", index=False)
        else:
            df.to_csv("ODC-DEMO/demo_data/" + filename + ".csv", index=False)
    except:
        print('Post data processing and CSV Export failed')
    finally:
        Cyton_Board_End(board)

def labelTxt(text):
    return f'<h1 style="text-align:center; color: white">{text}</h1>'

def post_process(data, start_time, color_code, color_freq, boardId):
    print(boardId)
    
    split_indices = np.where(data==0.666)[0]

    if boardId == 0:
        timetime = data[:,22:23]
        data = np.delete(data, 0,1)
        data = np.delete(data, range(8,23), 1)
    elif boardId == -1:
        timetime = data[:,30:31]
        data = np.delete(data, 0,1)
        data = np.delete(data, range(8,31), 1)
    # GTech Unicorn
    else:
        print("good")
        timetime = data[:,17:18]
        # data = np.delete(data, 0,1)
        zzz = data[:,7:18]
        yyy = data[:,0:7]
        print(zzz.shape)
        print(yyy.shape)
        
        data = np.delete(data, range(8,19), 1)
        print(data.shape)

    timexxx = []
    for i in range(len(timetime)):
        timexxx.append(datetime.datetime.fromtimestamp(timetime[i][0]))
    # OpenBCI Setting
    
    print(data.shape)

    xx = np.array(timexxx)
    print(xx.shape)

    wowow = np.array(timexxx).reshape(-1,1)

    # VirtualBoard Setting  
    # data = np.delete(data, range(8,31), 1)
    data = np.concatenate((wowow, data), axis=1)
    data = np.split(data, split_indices)

    # Create header row
   
    header = []
    header.append("time")
    for i in range(1, 9):
        header.append('CH{}'.format(i))
    
    for i in data:
        print(np.shape(i))

    # Convert data blocks from NumPy arrays to pandas DataFrames
    for i in range(len(data)):
        data[i] = pd.DataFrame(data[i], columns=header)

    print(len(color_code))
    print(len(color_freq))
    

    # Put color code and frequency columns together with data blocks
    for data_block, code, freq in zip(data, color_code, color_freq):
        data_block.loc[0, 'Color Code'] = code
        data_block.loc[0, 'Frequency'] = freq
    
    # Combine to 1 DataFrame
    print(len(data))
    for j in range(len(data)):
        print(data[j].shape, "  ", j)
        data[j] = data[j].to_numpy()
        print(np.shape(data[j]), "  ", j)
    for i in range(0, len(data)-1):
        data[i+1] = np.concatenate((data[i], data[i+1]), axis=0)

    df_data = data[-1]

    # timestamp = []
    # ms = repr(start_time).split('.')[1][:3]
    # for i in range(df_data.shape[0]):
    #     # Convert Unix time to desired timestamp format
    #     formatted_start_time = strftime("%Y-%m-%d %H:%M:%S.{} %Z".format(ms), localtime(start_time))[:23]
    #     timestamp.append( formatted_start_time )

    #     # Increment by 4ms for 250Hz
    #     # Increment by 8ms for 125Hz
    #     ms = int(ms) + 4
    #     # Work-around for floating point error from adding millisecond
    #     if ms > 999:
    #         rem_ms = str(ms - 1000)
    #         start_time += 1  
    #         ms = '00' + rem_ms
    #     else:
    #         ms = str(ms)
    #         if len(str(ms)) == 1: 
    #             ms = '00' + ms
    #         elif len(str(ms)) == 2:
    #             ms = '0' + ms
    #         else:
    #             pass    

    # mergeable_timestamp = []
    # # Add timestamp column
    # for i in timestamp:
    #     mergeable_timestamp.append([i])
    # df_all = np.concatenate((mergeable_timestamp, df_data), axis=1)
    # header.insert(0, 'Timestamp')
    header.append('Color Code')
    header.append('Frequency')
    df_all = pd.DataFrame(df_data, columns=header)
    
    #print(mergeable_timestamp)
    #print(df_all.head())
    #df_time = pd.DataFrame(timestamp, columns=['Timestamp'])
    #df_all = pd.merge(df_time, df_data.reset_index(drop=True), how="inner", left_index=True, right_index=True)\\

    return df_all

def generate_test_report(board, duration, data, color_code_order, color_freq_order):
    tf = open("ODC-DEMO/test_report.txt", 'w')  
    tf.write("Size of Data List: ")
    tf.write(str(np.shape(data)))
    tf.write("\n")
    tf.write("Size of Color Code List: ")
    tf.write(str(len(color_code_order)))
    tf.write("\n")
    tf.write("Size of Color Freq List: ")
    tf.write(str(len(color_freq_order)))
    tf.write("\n\n")
    tf.write("Channel Names: ")
    for i in board.get_eeg_names(0):
        tf.write(i)
        tf.write(", ")
    tf.write("\n\n")
    tf.write("Channel Numbers: ")
    for i in board.get_eeg_channels(0):
        tf.write(str(i))
        tf.write(", ")
    tf.write("\n\n")
    tf.write("Number of Channels: ")
    tf.write(str(board.get_num_rows(0)))
    tf.write("\n\n") 
    tf.write("Marker Channel: ")
    tf.write(str(board.get_marker_channel(0)))
    tf.write("\n")
    tf.write("Data Acquisition Duration: ")
    tf.write(str(duration))
    tf.write("\n\n")
    tf.write("Expected Samples: ")
    tf.write(str(board.get_sampling_rate(0)*duration)) 
    tf.write("\n")
    tf.write("Received Samples: ")
    tf.write(str(np.shape(data)[0]))
    tf.write("\n")
    tf.close()

def post_process( data, timestamp, color_code, color_freq ):

    header = ['Time']
    for i in range(1, 17):
        header.append('CH{}'.format(i))

    for i in range(np.shape( timestamp )[0]):
        data[i] = np.c_[ timestamp[i] , data[i]  ]
    
    for i in range(len(data)):
        # Color code order going out of range
        data[i] = pd.DataFrame(data[i], columns=header)
        data[i].loc[0, 'Color Code'] = color_code[i]
        data[i].loc[0, 'Frequency'] = color_freq[i]
    
    df_all = pd.concat(data)
    df_all.index.name = 'Count'
    return df_all

class Stimuli(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 900)

        self.frame = QFrame(self, objectName="frame") # ensures correct aspect ratio of grid
        global stim
        stim = []

        # white stims
        stim.append(Stim.CircleFlash(20, 255, 255, 255, 1))
        stim.append(Stim.CircleFlash(18, 255, 255, 255, 2))
        stim.append(Stim.CircleFlash(16, 255, 255, 255, 3))
        stim.append(Stim.CircleFlash(14, 255, 255, 255, 4))
        stim.append(Stim.CircleFlash(12, 255, 255, 255, 5))
        stim.append(Stim.CircleFlash(10, 255, 255, 255, 6))
        stim.append(Stim.CircleFlash(8, 255, 255, 255, 7))
        stim.append(Stim.CircleFlash(6, 255, 255, 255, 8))

        # blue stims
        stim.append(Stim.CircleFlash(11, 0, 0, 255, 9))
        stim.append(Stim.CircleFlash(7, 0, 0, 255, 10))

        # green stims
        stim.append(Stim.CircleFlash(9, 0, 255, 0, 11))
        stim.append(Stim.CircleFlash(5, 0, 255, 0, 12))

        # append stimulis to grid in random order
        random.shuffle(stim)

        # create array of indicators
        global preStimIndicators
        preStimIndicators = []
        for x in range(12):
            preStim = QLabel(labelTxt(""))
            preStimIndicators.append(preStim)   
        self.gridLayout = QGridLayout(self.frame)
        # self.gridLayout.addWidget(QLabel(), 3, 0)
        for row in range(3):
            for col in range(4):
                stimNum = row*4+col
                self.gridLayout.addWidget(preStimIndicators[stimNum], row*2+3, col*2)
                if (col != 3):
                    self.gridLayout.addWidget(QLabel(), row*2+3, col*2+1)

                stim[stimNum].toggleOff()
                self.gridLayout.addWidget(stim[stimNum], row*2+4, col*2)
        self.gridLayout.setSpacing(10)

    # resizes grid during window resize
    def resizeEvent(self, event): 
        super().resizeEvent(event)

        l = min(self.width(), self.height())
        center = self.rect().center()

        rect = QRect(0, 0, int(l*(7/6)), l) # 5 x 3 ratio
        rect.moveCenter(center)
        self.frame.setGeometry(rect)

        # self.gridLayout.setColumnMinimumWidth(1, int(l/12)) # 3 additional columns fill space to make it a 4x3 grid 
        # self.gridLayout.setColumnMinimumWidth(3, int(l/12))
        # self.gridLayout.setColumnMinimumWidth(5, int(l/12))

def Cyton_Board_Config(purpose):
    
    BoardShim.enable_dev_board_logger()

    parser = argparse.ArgumentParser()
    # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False, default=0)
    parser.add_argument('--ip-port', type=int, help='ip port', required=False, default=0)
    parser.add_argument('--ip-protocol', type=int, help='ip protocol, check IpProtocolType enum', required=False, default=0)
    parser.add_argument('--ip-address', type=str, help='ip address', required=False, default='')
    parser.add_argument('--serial-port', type=str, help='serial port', required=False, default='')
    parser.add_argument('--mac-address', type=str, help='mac address', required=False, default='')
    parser.add_argument('--other-info', type=str, help='other info', required=False, default='')
    parser.add_argument('--streamer-params', type=str, help='streamer params', required=False, default='')
    parser.add_argument('--serial-number', type=str, help='serial number', required=False, default='')
    parser.add_argument('--board-id', type=int, help='board id, check docs to get a list of supported boards', required=True)
    parser.add_argument('--file', type=str, help='file', required=False, default='')
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.ip_port = args.ip_port
    params.serial_port = args.serial_port
    params.mac_address = args.mac_address
    params.other_info = args.other_info
    params.serial_number = args.serial_number
    params.ip_address = args.ip_address
    params.ip_protocol = args.ip_protocol
    params.timeout = args.timeout
    params.file = args.file
    
    # Cyton Board Object
    board = BoardShim(args.board_id, params)

    # Start Acquisition
    board.prepare_session()

    # if purpose=true we're running the whole thing
    # else we're just running the demo
    if purpose:
        board.start_stream(45000, args.streamer_params)
        return board
    else:
        return [board, args.streamer_params]

def Cyton_Board_End(board):
    board.release_session()
    return

if __name__ == '__main__':
    # File and GUI config
    x = datetime.datetime.now()

    global filename 
    filename =  f"{x.strftime('%j')}_{x.strftime('%Y')}_{x.strftime('%f')}" #day of year, year, millisecond

    file = open("ODC-DEMO/demo_data/" + filename + ".txt", "x") # create log 

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('Flashing Stim 1')
    window.setStyleSheet("background-color: black;")

    layout = QVBoxLayout()

    # global label
    label = QLabel(labelTxt("ODC-DEMO"))
    label.setFixedHeight(100)
    layout.addWidget(label)
    print("Test")
    grid = Stimuli() # stimuli grid widget
    
    layout.addWidget(grid)
    window.setLayout(layout)
    
    # BCI Config
    board_details = Cyton_Board_Config(False)

    global testing
    testing = False
    stopThread = False
    x = threading.Thread(target=display_procedure, args=(lambda: stopThread, board_details[0], board_details[1]))
    x.start()

    window.setFixedSize(1000, 900) # initial window size
    window.show()
    
    try:
        sys.exit(app.exec_())
    except SystemExit:
        stopThread = True
        file.close()
        print('Closing Window...')

