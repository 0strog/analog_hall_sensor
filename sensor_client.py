# script for interacting with raspberry
import socket
import struct
import time
import matplotlib.pyplot as plt
import keyboard
import threading

LOCALHOST = '192.168.0.192'
PORT = 40090

EXIT = False
SENSOR_VALUES = []

SCALE_X_MAX = 30  # секунд (по идее)
SCALE_X_MIN = 0
SCALE_Y_MAX = 1  # милитесла (по идее)
SCALE_Y_MIN = -1


def wait_key():
    global EXIT
    while not keyboard.is_pressed('q'):
        time.sleep(0.01)
    print("You are exit")
    EXIT = True


def get_values():
    # getting value from the sensor
    global sock
    global EXIT
    global SENSOR_VALUES
    while not EXIT:
        values = []
        message_length = sock.recv(4)
        message_length = struct.unpack('i', message_length)[0]
        for i in range(message_length):
            values.append(struct.unpack('f', sock.recv(4))[0])
        SENSOR_VALUES = values


sock = socket.socket()
sock.connect((LOCALHOST, PORT))

key_thread = threading.Thread(target=wait_key)
key_thread.start()

values_thread = threading.Thread(target=get_values)
values_thread.start()

fig, ax = plt.subplots()
# plt.axis([SCALE_X_MIN, SCALE_X_MAX, SCALE_Y_MIN, SCALE_Y_MAX])
plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

# block of graphic
sens_num = 16

colormap = [hex(i*12345) for i in range(12)]
for i in range(len(colormap)):
    colormap[i] = colormap[i][2:]
    if len(colormap[i]) < 6:
        while len(colormap[i]) < 6:
            colormap[i] = '0' + colormap[i]
    colormap[i] = '#' + colormap[i]
data_old = [0 for i in range(12)]
data_now = []
timepoint_start = time.clock()
timepoint_old = SCALE_X_MIN
timepoint_now = SCALE_X_MIN
while not EXIT:

    if len(SENSOR_VALUES) != 0:
        data_now = SENSOR_VALUES

        # scaling x axe
        if timepoint_now > SCALE_X_MAX:
            timepoint_old = 0
            plt.cla()
            timepoint_start = time.clock()
            plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
        timepoint_now = time.clock() - timepoint_start
        # scaling y axe
        if max(data_now) > SCALE_Y_MAX:
            SCALE_Y_MAX = max(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)
        if min(data_now) < SCALE_Y_MIN:
            SCALE_Y_MIN = min(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

        if sens_num == 16:
            for i in range(12):
                plt.plot([timepoint_old, timepoint_now], [data_old[i], data_now[i]], colormap[i])
                plt.text(i, 0, str(i), fontsize=18, bbox=dict(color=colormap[i]), rotation=0)
            plt.pause(0.00001)

        elif sens_num >= 0 or sens_num <= 15:
            plt.plot([timepoint_old, timepoint_now], [data_old[sens_num], data_now[sens_num]])
            plt.pause(0.001)

        timepoint_old = timepoint_now
        data_old = data_now
