import matplotlib.pyplot as plt
import socket
import time
import threading
import struct
import xlrd, xlwt
import keyboard
import os


LOCALHOST = '192.168.0.192'
USER = 'pi'
SECRET = 'raspberry'
PORT = 40090
EXIT = False  # Глобальный выход. Прерывает все потоки

SENS_NUMBERS_MAX = 12

stepper_speed = 0
moving_direction = False

SENSOR_VALUES = []  # используется для хранения значений, которые будут рисоваться на графике
SENSOR_VALUES_BUFFER = [[] for i in range(SENS_NUMBERS_MAX)]  # используется для хранения значений, которые будут записываться в файл при сохранении

SCALE_X_MAX = 30
SCALE_X_MIN = 0
SCALE_Y_MAX = 1  # милитесла (по идее)
SCALE_Y_MIN = -1

command_dictionary = {
    "to home": 13,
    "increase speed": 17,
    "decrease speed": 25
}


# Не оч понял, как это работает, надо ещё позалипать
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
for i in range(SENS_NUMBERS_MAX):
    ws.write(0, i, 'Датчик ' + str(i))

print("Please enter the distance from the sensors to the surface")
distance_to_surface = str(input())
ws.write(0, 12, 'Расстояние от датчиков до поверхности: ' + distance_to_surface)

current_file_number = find_last_number() + 1
file_name = "./results/result" + str(current_file_number) + ".xls"
wb.save(file_name)
print("FILE SAVED")


def socket_init():
    initialisable_socket = socket.socket()
    initialisable_socket.connect((LOCALHOST, PORT))
    return initialisable_socket


def send_command(command):
    message = command_dictionary[command]
    sock.send(struct.pack("i", message))


# Поток считывания ключей
def wait_key():
    global EXIT, sheet_number, ws
    while not keyboard.is_pressed('q'):
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

            # Если надо использовать перезапись клеток ставится флаг cell_overwrite_ok
            # worksheet = workbook.add_sheet("Sheet 1", cell_overwrite_ok=True)
            ws = wb.add_sheet('Data Hall ' + str(sheet_number))
            sheet_number += 1
            for i in range(SENS_NUMBERS_MAX):
                ws.write(0, i, 'Датчик ' + str(i))
                for j in range(len(SENSOR_VALUES_BUFFER[i])):
                    ws.write(j + 1, i, SENSOR_VALUES_BUFFER[i][j])

            wb.save(file_name)
        time.sleep(0.01)
    print("EXIT")
    EXIT = True


# Поток приема сообщений
def start_recv_thread():
    global sock, EXIT, stepper_speed, moving_direction, SENSOR_VALUES, SENSOR_VALUES_BUFFER
    while not EXIT:
        readable_message = sock.recv(12)
        if readable_message != b'':
            values = []
            data = struct.unpack('i?i', readable_message)
            stepper_speed = data[0]
            moving_direction = data[1]
            if moving_direction == False:
                for i in range(data[2]):
                    values.append(struct.unpack('f', sock.recv(4))[0])
                    SENSOR_VALUES_BUFFER[i].append(values[i])
                SENSOR_VALUES = values
            else:
                SENSOR_VALUES = []
                SENSOR_VALUES_BUFFER = [[] for i in range(SENS_NUMBERS_MAX)]
        else:
            print("receive thread is end")
            EXIT = True


# Цветовая палитра для графиковz
def colormap_init():
    # Здесь просто создаётся список разных цветов в формате rgb
    # (число, на которое умножается i в следующей строке взято случайно, чтобы цвета были различимы
    # и в диапазоне кодировки RGB (кажется от 0 до 0xFFFFFF))
    colors = [hex(i * 12345) for i in range(SENS_NUMBERS_MAX)]
    for i in range(len(colors)):
        colors[i] = colors[i][2:]
        if len(colors[i]) < 6:
            while len(colors[i]) < 6:
                colors[i] = '0' + colors[i]
        colors[i] = '#' + colors[i]
    return colors


sock = socket_init()

# Инициализация и запук потоков
key_thread = threading.Thread(target=wait_key)
values_thread = threading.Thread(target=start_recv_thread)
key_thread.start()
values_thread.start()

fig, ax = plt.subplots()
# plt.axis([SCALE_X_MIN, SCALE_X_MAX, SCALE_Y_MIN, SCALE_Y_MAX])
plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
# plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

# ********--------Отрисовка графика--------********
colormap = colormap_init()
data_old = [0 for i in range(SENS_NUMBERS_MAX)]
data_now = []
distance_old = 0
timepoint_start = time.clock()
timepoint_old = SCALE_X_MIN
while not EXIT:
    timepoint_now = time.time() - timepoint_start
    if len(SENSOR_VALUES) != 0:
        data_now = SENSOR_VALUES
        stepper_linear_velocity = stepper_speed * (80.11 / 200) * 0.001
        distance_now = stepper_linear_velocity * timepoint_now

        # обновление оси X
        if distance_now > SCALE_X_MAX:
            SCALE_X_MAX += 30
            plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
        ''''# обновление шкалы ОY графика
        if max(data_now) > SCALE_Y_MAX:
            SCALE_Y_MAX = max(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)
        if min(data_now) < SCALE_Y_MIN:
            SCALE_Y_MIN = min(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)'''

        plt.plot([distance_old, distance_now],
                 [data_old[i], data_now[i]],
                 colormap[i]
                 )
        # plt.text(i, 0, str(i), fontsize=18, bbox=dict(color=colormap[i]), rotation=0)
        plt.pause(0.0001)

        timepoint_old = timepoint_now
        distance_old = distance_now
        data_old = data_now

    else:
        plt.pause(0.001)

wb.save(file_name)
print("FILE SAVED")
plt.show()
