# script for reading sensors (must be start on Raspberry)
from smbus import SMBus
import analog_hall_lib
import time
import socket
import struct

HOST_NAME = ''
PORT = 40090
EXIT = False


def connect():
    sock = socket.socket()
    sock.bind((HOST_NAME, PORT))
    sock.listen(1)
    new_sock, address = sock.accept()
    print('connected:', address)
    return new_sock


if __name__ == "__main__":
    conn = connect()
    bus = SMBus(1)
    sens = analog_hall_lib.AnHall(bus)

    try:
        # Thread of send values to client
        while not EXIT:
            sensor_values = sens.read_all_sensors()

            length_message = len(sensor_values)
            length_send = struct.pack('i', length_message)
            conn.send(length_send)
            for i in range(length_message):
                send_values = struct.pack('f', sensor_values[i])
                conn.send(send_values)

            time.sleep(0.2)
    except KeyboardInterrupt:
        EXIT = True
    except ConnectionResetError:
        EXIT = True
    except BrokenPipeError:
        EXIT = True
