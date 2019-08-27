import matplotlib.pyplot as plt
import socket
import time
import threading
import struct
import xlrd, xlwt
import keyboard
import os


host = '192.168.0.192'
user = 'pi'
secret = 'raspberry'
port = 22

'''client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# Подключение
client.connect(hostname=host, username=user, password=secret, port=port)
stdin, stdout, stderr = client.exec_command('sudo python3 py_code/magnet_sensor_stand.py')
# print(stdout.readlines())'''
# Глобальный выход. Прерывает все потоки
EXIT = 0

# Значения осей x y z магнитного датчика
value_x = [0, 0, 0, 0]
value_y = 0
value_z = 0
value_t = 0

lag = 1

sock = socket.socket()
sock.connect(('192.168.0.192', 9090))


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


STATE = 0
# Поток приема сообщений
def start_recv_thread():
    global value_x, value_y, value_z, EXIT, tt, STATE
    x = [0, 0, 0, 0]
    while not EXIT:
        readed_message = sock.recv(100)
        if readed_message != b'':
            # print(readed_message)
            data = struct.unpack('12di', readed_message)
            # print(data)

            x[0] = data[2]*0.098
            x[1] = data[5]*0.098
            x[2] = data[8]*0.098
            x[3] = data[11]*0.098

            moving_direction = data[12]
            if moving_direction == 1:
                STATE = 0
            elif moving_direction == 2:
                STATE = 2

            value_x = x

            data_cash[0].append(value_x[0])
            data_cash[1].append(value_x[1])
            data_cash[2].append(value_x[2])
            data_cash[3].append(value_x[3])

        else:
            EXIT = 1


t = threading.Thread(target=start_recv_thread)
t.start()
old_x = [0, 0, 0, 0]
old_y = 0
old_z = 0
old_t = 0

timer = 0

sheet_number = 0
wb = xlwt.Workbook()
ws = wb.add_sheet('Data magnet')
ws.write(0, 0, 'Датчик 1')
ws.write(0, 1, 'Датчик 2')
ws.write(0, 2, 'Датчик 3')
ws.write(0, 3, 'Датчик 4')
current_file_number = find_last_number() + 1
file_name = "./results/result" + str(current_file_number) + ".xls"
wb.save(file_name)
print("FILE SAVED")

data_cash = [[], [], [], []]

command_dictionary = {
    "to home": 13,
    "increase speed": 17,
    "decrease speed": 25
}


def send_message(command):
    message = command_dictionary[command]
    sock.send(struct.pack("i", message))


def median_filter():
    if len(data_cash[0]) < 4:
        return None

    last_element_number = len(data_cash[0]) - 1
    data = [data_cash[0][last_element_number-3:], data_cash[1][last_element_number-3:], data_cash[2][last_element_number-3:], data_cash[3][last_element_number-3:]]

    result = []
    for data_list in data:
        sorted_list = sorted(data_list)
        median_value = (sorted_list[1] + sorted_list[2])/2
        result.append(median_value)
    return result


start_time = time.time()
old_time = start_time

buffer = [[], [], [], []]

tt = 0
tt_list = []
while not EXIT:
    current_time = time.time() - start_time
    # Обрезаем до 3 знаков после запятой
    current_time = float("{0:.3f}".format(current_time))

    #print("t", timer)
    #print("value_x: ", value_x)
    #print("old_x: ", old_x)
    if STATE == 1:
        x = median_filter()

        if x is None:
            continue

        tt_list.append(tt)

        tt += lag
        for j in range(len(x)):
            if x[j] == 0:
                x[j] = old_x[j]

        # Строка, столбец, данные
        for column in range(4):
            # print("current_time: ", current_time)
            #ws.write(int(tt), column, x[column])
            pass

        plt.plot([tt - lag, tt], [old_x[0], x[0]], 'r')
        plt.plot([tt - lag, tt], [old_x[1], x[1]], 'g')
        plt.plot([tt - lag, tt], [old_x[2], x[2]], 'b')
        plt.plot([tt - lag, tt], [old_x[3], x[3]], 'y')

        buffer[0].append(x[0])
        buffer[1].append(x[1])
        buffer[2].append(x[2])
        buffer[3].append(x[3])

        old_time = current_time
        old_x = x[:]

        plt.text(1, 0, '1', fontsize=18, bbox=dict(edgecolor='r', color='r'), rotation=0)
        plt.text(5, 0, '2', fontsize=18, bbox=dict(edgecolor='g', color='g'), rotation=0)
        plt.text(10, 0, '3', fontsize=18, bbox=dict(edgecolor='b', color='b'), rotation=0)
        plt.text(15, 0, '4', fontsize=18, bbox=dict(edgecolor='y', color='y'), rotation=0)

        plt.ylabel('Величина')
        plt.xlabel('Время')

        plt.grid(True)
        plt.pause(0.01)

    elif STATE == 2:
        plt.pause(0.01)

    elif STATE == 0:
        plt.cla()
        plt.plot(tt_list, buffer[0], 'p')
        plt.plot(tt_list, buffer[1], 'p')
        plt.plot(tt_list, buffer[2], 'p')
        plt.plot(tt_list, buffer[3], 'p')
        tt = 0
        tt_list = []
        buffer = [[], [], [], []]
        STATE = 1
        plt.plot([0, 75], [0, 0], 'w')

    if keyboard.is_pressed('q'):
        EXIT = 1
        print("EXIT")

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
        ws = wb.add_sheet('Data magnet ' + str(sheet_number))
        sheet_number += 1
        ws.write(0, 0, 'Датчик 1')
        ws.write(0, 1, 'Датчик 2')
        ws.write(0, 2, 'Датчик 3')
        ws.write(0, 3, 'Датчик 4')

        for i in range(len(buffer)):
            for j in range(len(buffer[i])):
                ws.write(j+1, i, buffer[i][j])

        wb.save(file_name)

'''
##########################
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)

axpos = plt.axes([0.2, 0.1, 0.65, 0.03])

spos = Slider(axpos, 'Pos', 0.1, 3000)


def update(val):
    pos = spos.val
    ax.axis([pos, pos + 10, -1, 1])
    fig.canvas.draw_idle()

spos.on_changed(update)
##########################'''

wb.save(file_name)
print("FILE SAVED")
plt.show()
#client.close()
# pscp -pw raspberry magnet_sensor_stand.py pi@192.168.0.192:/home/pi/py_code/magnet_sensor_stand.py
