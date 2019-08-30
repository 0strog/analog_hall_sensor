import socket
import struct
import keyboard
import matplotlib.plot as plt

EXIT = False  # ending all threads

SENSORS_NUMBER = 12
values = [float(0) for i in range(SENSORS_NUMBER)]

sock = socket.socket()
sock.connect(('192.168.0.192', 9090))

moving_direction = False
driver_commands = {
                    "to home": 13,
                    "increase speed": 17,
                    "decrease speed": 25
                    }


def send_command(command):
    message = driver_commands[command]
    sock.send(struct.pack("i", message))

def receive_values():
    global sock, values, moving_direction

    while not EXIT:
        server_message = sock.recv(4*SENSORS_NUMBER + 1)

        if server_message != b'':
            data = struct.unpack('12f?', server_message)

            values = data[:SENSORS_NUMBER]
            moving_direction = data[-1]


while not EXIT:


    if keyboard.is_pressed('q'):
        EXIT = 1
        print("EXIT")

    if keyboard.is_pressed('h'):
        send_command("to home")
        print("Вернуться к точке старта")

    if keyboard.is_pressed('x'):
        send_command("increase speed")
        print("Скорость увеличена")

    if keyboard.is_pressed('z'):
        send_command("decrease speed")
        print("Скорость уменьшена")

print("exit")
plt.show()