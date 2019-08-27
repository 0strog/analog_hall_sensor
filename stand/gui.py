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

# Глобальный выход. Прерывает все потоки
EXIT = False

SENS_NUMBERS_MAX = 12

# Принимаются из потока чтения сокета и используются в потоке отрисовки гафика
stepper_speed = 0
moving_direction = False

SENSOR_VALUES = []
SENSOR_VALUES_BUFFER = [[] for i in range(SENS_NUMBERS_MAX)]

# Размеры осей
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
    sock.connect((LOCALHOST, PORT))
    return initialisable_socket


def send_message(command):
    message = command_dictionary[command]
    sock.send(struct.pack("i", message))


# Поток считывания ключей
def wait_key():
    global EXIT, sheet_number, ws
    while not keyboard.is_pressed('q'):
        if keyboard.is_pressed('h'):
            send_message("to home")
            print("Вернуться к точке старта")

        if keyboard.is_pressed('x'):
            send_message("increase speed")
            print("Скорость увеличена")

        if keyboard.is_pressed('z'):
            send_message("decrease speed")
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

    print("EXIT")
    EXIT = True


STATE = 0
# Поток приема сообщений
def start_recv_thread():
    global sock, EXIT, stepper_speed, moving_direction, SENSOR_VALUES, SENSOR_VALUES_BUFFER
    while not EXIT:
        readable_message = sock.recv(100)
        if readable_message != b'':
            values = []
            data = struct.unpack('i?i', readable_message)
            stepper_speed = data[0]
            moving_direction = data[1]
            if moving_direction == True:
                for i in range(SENS_NUMBERS_MAX):
                    values.append(struct.unpack('f', sock.recv(4))[0])
                    SENSOR_VALUES_BUFFER[i].append(values[i])
                SENSOR_VALUES = values
            else:
                SENSOR_VALUES = []
                SENSOR_VALUES_BUFFER = [[] for i in range(SENS_NUMBERS_MAX)]
        else:
            EXIT = True


# Цветовая палитра для графиков
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

key_thread = threading.Thread(target=wait_key)
values_thread = threading.Thread(target=start_recv_thread)

key_thread.start()
values_thread.start()

fig, ax = plt.subplots()
# plt.axis([SCALE_X_MIN, SCALE_X_MAX, SCALE_Y_MIN, SCALE_Y_MAX])
plt.xlim(SCALE_X_MIN, SCALE_X_MAX)
plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

# ********--------Отрисовка графика--------********
# Если планируется читать один сенсор, то значение sens_num от 0 до SENS_NUMBERS_MAX-1 позволят
# нам читать сенсор с соответственным номером,
# а, если значение sens_num = SENS_NUMBERS_MAX, то будут читаться все датчики
# !!!Пока программа разработана для режима чтения всех датчиков!!!
sens_num = SENS_NUMBERS_MAX
colormap = colormap_init()
data_old = [0 for i in range(SENS_NUMBERS_MAX)]
data_now = []
timepoint_start = time.clock()
timepoint_old = SCALE_X_MIN
while not EXIT:
    timepoint_now = time.time() - timepoint_start
    if len(SENSOR_VALUES) != 0:
        data_now = SENSOR_VALUES

        # обновление шкалы ОY графика
        if max(data_now) > SCALE_Y_MAX:
            SCALE_Y_MAX = max(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)
        if min(data_now) < SCALE_Y_MIN:
            SCALE_Y_MIN = min(data_now)
            plt.ylim(SCALE_Y_MIN, SCALE_Y_MAX)

        # 
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

    else:
        plt.pause(0.01)

wb.save(file_name)
print("FILE SAVED")
plt.show()