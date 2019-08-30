import socket
import struct
import keyboard
import matplotlib.pyplot as plt
import time
import threading
import os
import xlwt

EXIT = False  # ending all threads

SENSORS_NUMBER = 12  # количество читаемых датчиков
values = [float(0) for i in range(SENSORS_NUMBER)]  # переменная для чтения данных с датчика
values_buffer = [[] for i in range(SENSORS_NUMBER)]  # буфер заполняемый данными с датчика и используемый для записи
# данных в файл, сейчас привязан ко времени (а не к пройденному расстоянию)

sock = socket.socket()
sock.connect(('192.168.0.192', 40090))

mv_direction = False
DIRECTION_CHANGED = False  # флаг для фиксирования изменения направления (используется только в потоке отрисовки
# графика, но сделан глобальным для будущих применений)
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
    global values, values_buffer, EXIT, SENSORS_NUMBER, mv_direction, DIRECTION_CHANGED
    scale_x_max = 30

    fig, ax = plt.subplots()
    plt.xlim(0, scale_x_max)
    colormap = colormap_init()

    old_data = [0 for i in range(SENSORS_NUMBER)]
    start_time = time.time()
    old_time = 0

    while not EXIT:
        if mv_direction == False:
            # при изменении направления движения график очищается и мастабируется по оси X, очищается буфер с данными
            # и обновляются времена
            if DIRECTION_CHANGED:
                DIRECTION_CHANGED = False
                plt.cla()
                plt.xlim(0, scale_x_max)
                values_buffer = [[] for i in range(SENSORS_NUMBER)]
                start_time = time.time()
                old_time = 0

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
                values_buffer[i].append(curr_data[i])
            plt.pause(0.0001)
            old_time = curr_time
            old_data = curr_data
        else:
            plt.pause(0.001)
            # При изменении направления... просто фиксируем изменение направления
            if not DIRECTION_CHANGED:
                DIRECTION_CHANGED = True

        time.sleep(0.01)


# Далее набор функций и блок переменных, скопипасченных с Дамира, для записи данных в файл
def find_last_number():
    folder = (os.listdir(path="./results"))
    minimum = 0
    for names in folder:
        target_name = list(set(names) & set('result'))
        if len(target_name) == 6:
            number = (int(names.split('t')[1].split('.')[0]))
            if minimum < number:
                minimum = number
    return minimum


sheet_number = 0
wb = xlwt.Workbook()
ws = wb.add_sheet('Data Hall')
for i in range(SENSORS_NUMBER):
    ws.write(0, i, 'Датчик %i' % i)

current_file_number = find_last_number() + 1
file_name = "./results/result" + str(current_file_number) + ".xls"
wb.save(file_name)
print("FILE SAVED")


receive_values_thread = threading.Thread(target=receive_values)  # поток приема данных с датчика
plot_vals_thread = threading.Thread(target=plot_vals)  # поток отрисовки данных с датчика
receive_values_thread.start()
plot_vals_thread.start()

print("Введите расстояние от датчика до металла (Дамир, если захочешь удалить это приглашение, оно начинается в "
      "строке 146)")
sensor_distance = int(input())

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

    if keyboard.is_pressed('v'):
        print("Страница сохранена")

        # Если надо использовать перезапись клеток ставится флаг cell_overwrite_ok worksheet = workbook.add_sheet(
        # "Sheet 1", cell_overwrite_ok=True)
        ws = wb.add_sheet('Data magnet ' + str(sheet_number))
        sheet_number += 1

        for i in range(len(values_buffer)):
            ws.write(0, i, 'Датчик %i' % i)
            for j in range(len(values_buffer[i])):
                ws.write(j+1, i, values_buffer[i][j])
        ws.write(0, len(values_buffer), str(sensor_distance))

        wb.save(file_name)

    time.sleep(0.1)

sock.close()
print("exit")
