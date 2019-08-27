# script for interacting with raspberry
import socket
import struct
import time
import matplotlib.pyplot as plt
import keyboard
import threading

# socket connection data
LOCALHOST = '192.168.0.192'
PORT = 40090

EXIT = False  # for end program
SENSOR_VALUES = []

# axes size
SCALE_X_MAX = 30  # секунд (по идее)
SCALE_X_MIN = 0
SCALE_Y_MAX = 1  # милитесла (по идее)
SCALE_Y_MIN = -1

SENS_NUMBERS_MAX = 12

# func of ending program
def wait_key():
    global EXIT
    while not keyboard.is_pressed('q'):
        time.sleep(0.01)
    print("You are exit")
    EXIT = True


# func of reading sensor data from socket
def get_values():
    global sock
    global EXIT
    global SENSOR_VALUES
    while not EXIT:
        values = []
        message_length = sock.recv(4)  # get number of sensors
        message_length = struct.unpack('i', message_length)[0]
        for i in range(message_length):
            values.append(struct.unpack('f', sock.recv(4))[0])  # get values from sensors
        SENSOR_VALUES = values


def socket_init():
    initialisable_socket = socket.socket()
    sock.connect((LOCALHOST, PORT))
    return initialisable_socket


def colormap_init():
    colors = [hex(i * 12345) for i in range(12)]
    for i in range(len(colors)):
        colors[i] = colors[i][2:]
        if len(colors[i]) < 6:
            while len(colors[i]) < 6:
                colors[i] = '0' + colors[i]
        colors[i] = '#' + colors[i]
    return colors


sock = socket_init()

key_thread = threading.Thread(target=wait_key)
values_thread = threading.Thread(target=get_values)

key_thread.start()
values_thread.start()

fig, ax = plt.subplots()
# plt.axis([SCALE_X_MIN, SCALE_X_MAX, SCALE_Y_MIN, SCALE_Y_MAX])
plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

# block of graphic
sens_num = SENS_NUMBERS_MAX
colormap = colormap_init()
data_old = [0 for i in range(SENS_NUMBERS_MAX)]
data_now = []
timepoint_start = time.clock()
timepoint_old = SCALE_X_MIN
timepoint_now = SCALE_X_MIN
while not EXIT:

    if len(SENSOR_VALUES) != 0:
        data_now = SENSOR_VALUES

        # scaling axes
        if timepoint_now > SCALE_X_MAX:
            timepoint_old = 0
            plt.cla()
            timepoint_start = time.clock()
            plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
        timepoint_now = time.clock() - timepoint_start
        if max(data_now) > SCALE_Y_MAX:
            SCALE_Y_MAX = max(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)
        if min(data_now) < SCALE_Y_MIN:
            SCALE_Y_MIN = min(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

        # reading sensors
        if sens_num == SENS_NUMBERS_MAX:
            for i in range(SENS_NUMBERS_MAX):
                plt.plot([timepoint_old, timepoint_now], [data_old[i], data_now[i]], colormap[i])
                plt.text(i, 0, str(i), fontsize=18, bbox=dict(color=colormap[i]), rotation=0)
            plt.pause(0.00001)
        elif sens_num >= 0 or sens_num < SENS_NUMBERS_MAX:
            plt.plot([timepoint_old, timepoint_now], [data_old[sens_num], data_now[sens_num]])
            plt.text(sens_num, 0, str(sens_num), fontsize=18, bbox=dict(color=colormap[sens_num]), rotation=0)
            plt.pause(0.00001)

        timepoint_old = timepoint_now
        data_old = data_now
