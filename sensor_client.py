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

SCALE_X_MAX = 30  # секунд (по идее)
SCALE_X_MIN = 0
SCALE_Y_MAX = 15  # милитесла (по идее)
SCALE_Y_MIN = -10


def wait_key():
    global EXIT
    while not keyboard.is_pressed('q'):
        time.sleep(0.05)
    print("You are exit")
    EXIT = True


def get_values(sock):
    # getting value from the sensor
    message_length = sock.recv(4)
    message_length = struct.unpack('i', message_length)[0]
    sensor_values = []
    for i in range(message_length):
        sensor_values.append(sock.recv(4))
        sensor_values[i] = struct.unpack('f', sensor_values[i])[0]
    return sensor_values


sock = socket.socket()
sock.connect((LOCALHOST, PORT))

fig, ax = plt.subplots()
plt.axis([SCALE_X_MIN, SCALE_X_MAX, SCALE_Y_MIN, SCALE_Y_MAX])

th = threading.Thread(target=wait_key)
th.start()

# block of graphic
sens_num = 16

colormap = [hex(i*1048575) for i in range(12)]
for i in range(len(colormap)):
    colormap[i] = colormap[i][2:]
    if len(colormap[i]) < 6:
        while len(colormap[i]) < 6:
            colormap[i] = '0' + colormap[i]
    colormap[i] = '#' + colormap[i]

data_old = [0 for i in range(12)]
timepoint_start = time.clock()
timepoint_old = SCALE_X_MIN
timepoint_now = SCALE_X_MIN
while not EXIT:

    data_now = get_values(sock)

    # scaling graphic
    if timepoint_now > SCALE_X_MAX:
        timepoint_start = time.clock()
        timepoint_now -= SCALE_X_MAX
        timepoint_old = 0
        plt.clf()
        plt.axis([SCALE_X_MIN, SCALE_X_MAX, SCALE_Y_MIN, SCALE_Y_MAX])
    timepoint_now = time.clock() - timepoint_start

    if sens_num == 16:
        plt.plot([timepoint_old, timepoint_now], [data_old, data_now], colormap)
        plt.pause(0.001)
    elif sens_num >= 0 or sens_num <= 15:
        plt.plot([timepoint_old, timepoint_now], [data_old[sens_num], data_now[sens_num]], colormap[sens_num])
        plt.pause(0.001)
    timepoint_old = timepoint_now
    data_old = data_now
plt.show()
