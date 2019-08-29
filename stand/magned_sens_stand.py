#!/usr/bin/python
# -*- coding:utf-8 -*-
from smbus import SMBus
import analog_hall_lib
import RPi.GPIO as GPIO
import time
import socket
import struct
import threading

EXIT = False  # Глобальный выход. Прерывает все потоки

PIN_STEP = 20
PIN_DIR = 21
PIN_OPTIC_SENSOR = 22

stepper_speed = 20

command_dictionary = {
    "to home": 13,
    "increase speed": 17,
    "decrease speed": 25
}


def init_socket():
    sock = socket.socket()
    sock.bind(('', 40090))
    sock.listen(1)
    conn, addr = sock.accept()

    print('connected:', addr)
    return conn


old_optic_sensor_value = 0
optic_sensor_value = 0
moving_direction = False
DIRECTION_CHANGED = False


def callback_optic_sensor(_):
    global old_optic_sensor_value, optic_sensor_value, moving_direction, DIRECTION_CHANGED
    optic_sensor_value = GPIO.input(PIN_OPTIC_SENSOR)
    # print("moving direction!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!: ", moving_direction)
    if optic_sensor_value != old_optic_sensor_value:
        if optic_sensor_value == 1:
            moving_direction = not moving_direction
            print("change moving direction: ", moving_direction)
            GPIO.output(PIN_DIR, moving_direction)
            DIRECTION_CHANGED = True
        old_optic_sensor_value = optic_sensor_value


def sock_send(values):
    global stepper_speed, moving_direction
    data_arr_length = len(values)
    byte_speed_direction_length = struct.pack('i?i',
                                              stepper_speed,
                                              moving_direction,
                                              data_arr_length
                                              )
    sock.send(byte_speed_direction_length)
    if moving_direction == False:
        for sens_num in range(data_arr_length):
            time.sleep(0.001)
            sock.send(struct.pack('f', values[sens_num]))
    time.sleep(0.01)


def start_recv_thread():
    global stepper_speed, moving_direction
    while not EXIT:
        readed_message = sock.recv(4)
        cmd = struct.unpack('i', readed_message)[0]
        if cmd == command_dictionary["increase speed"]:
            stepper_speed += 10
            change_stepper_speed()
            print("CURRENT SPEED", stepper_speed)
        if cmd == command_dictionary["decrease speed"]:
            stepper_speed -= 10
            if stepper_speed <= 0:
                stepper_speed = 0.01
            change_stepper_speed()
            print("CURRENT SPEED", stepper_speed)
        if cmd == command_dictionary["to home"]:
            moving_direction = True
            GPIO.output(PIN_DIR, moving_direction)
        time.sleep(0.001)


def change_stepper_speed():
    pwm.ChangeFrequency(stepper_speed)


if __name__ == "__main__":
    try:
        # GPIO.BCM/GPIO.BOARD определяют распиновку.
        GPIO.setmode(GPIO.BCM)

        '''GPIO.setup(PIN_STEP, GPIO.OUT)
        GPIO.setup(PIN_DIR, GPIO.OUT)'''
        GPIO.setup(PIN_OPTIC_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Запускаю генерацию шим на STEP пине
        '''pwm = GPIO.PWM(PIN_STEP, stepper_speed)
        pwm.start(50)
        GPIO.output(PIN_DIR, moving_direction)'''
        GPIO.add_event_detect(PIN_OPTIC_SENSOR, GPIO.BOTH, callback=callback_optic_sensor)

        # I2C шина
        bus = SMBus(1)

        # Socket
        sock = init_socket()
        print("SOCK INITED")

        recv_thread = threading.Thread(target=start_recv_thread)
        recv_thread.start()

        sens = analog_hall_lib.AnHall(bus)

        while not EXIT:
            if DIRECTION_CHANGED:
                # Добавляю 1 чтоб отличать сообщение о направление когда направление изменилось
                # от сообщения когда не изменилось
                DIRECTION_CHANGED = False
            sensor_values = sens.read_all_sensors()
            sock_send(sensor_values)

            time.sleep(0.1)

    except KeyboardInterrupt:
        EXIT = True
    except ConnectionResetError:
        EXIT = True
    except BrokenPipeError:
        EXIT = True
    except OSError as error:
        print("SOMETHING GOING WRONG. CODE EXIT")
        print(error)

    finally:
        GPIO.cleanup()
        sock.close()
        EXIT = 1
        print("CLEAN UP")
