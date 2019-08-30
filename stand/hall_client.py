import socket
import struct
import keyboard
import matplotlib.pyplot as plt
import time
import threading

EXIT = False  # ending all threads

SENSORS_NUMBER = 12
values = [float(0) for i in range(SENSORS_NUMBER)]

sock = socket.socket()
sock.connect(('192.168.0.192', 40090))

mv_direction = False
driver_commands = {
    "to home": 13,
    "increase speed": 17,
    "decrease speed": 25
}


def send_command(command):
    message = driver_commands[command]
    sock.send(struct.pack("i", message))


def receive_values():
    global sock, values, mv_direction, EXIT

    while not EXIT:
        server_message = sock.recv(4 * SENSORS_NUMBER + 1)

        if server_message != b'':
            data = struct.unpack('12f?', server_message)

            values = data[:SENSORS_NUMBER]
            mv_direction = data[-1]

            time.sleep(0.001)
        else:
            print("receive thread is end")
            EXIT = True


# возвращает список цветов в количестве SENSORS_NUMBER в формате rgb
def colormap_init():
    global SENSORS_NUMBER, EXIT
    colors = [hex(i * 12345) for i in range(SENSORS_NUMBER)]

    for i in range(len(colors)):
        colors[i] = colors[i][2:]
        if len(colors[i]) < 6:
            while len(colors[i]) < 6:
                colors[i] = '0' + colors[i]
        colors[i] = '#' + colors[i]
    return colors


def plot_vals():
    global values, EXIT, SENSORS_NUMBER, mv_direction
    scale_x_max = 30

    fig, ax = plt.subplots()
    plt.xlim(0, scale_x_max)
    colormap = colormap_init()

    old_data = [0 for i in range(SENSORS_NUMBER)]
    start_time = time.time()
    old_time = 0

    while not EXIT:
        if mv_direction == False:
            curr_time = time.time() - start_time
            curr_data = values

            while curr_time > scale_x_max:
                scale_x_max += 30
                plt.xlim(0, scale_x_max)

            for i in range(SENSORS_NUMBER):
                plt.plot([old_time, curr_time],
                         [old_data[i], curr_data[i]],
                         colormap[i]
                         )
            plt.pause(0.0001)
            old_time = curr_time
            old_data = curr_data
        else:
            plt.pause(0.001)

        time.sleep(0.01)


receive_values_thread = threading.Thread(target=receive_values)
plot_vals_thread = threading.Thread(target=plot_vals)
receive_values_thread.start()
plot_vals_thread.start()

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

    time.sleep(0.01)

print("exit")
