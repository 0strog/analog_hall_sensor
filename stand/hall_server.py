import socket
import struct
import threading
import RPi.GPIO as GPIO
import time
from smbus import SMBus
import analog_hall_lib

EXIT = False  # ending all threads

PIN_STEP = 20
PIN_DIR = 21
PIN_OPTIC_SENSOR = 22

stepper_speed = 50
moving_direction = False
DIRECTION_CHANGED = False
driver_commands = {
                    "to home": 13,
                    "increase speed": 17,
                    "decrease speed": 25
                    }


def init_socket():
    sock_in = socket.socket()
    sock_in.bind(('', 40090))
    sock_in.listen(1)
    conn, addr = sock_in.accept()
    print('connected:', addr)
    return conn


def change_stepper_speed(cmd):
    cmd.ChangeFrequency(stepper_speed)


def receive_commands():
    global sock, driver_commands, stepper_speed, pwm, EXIT

    while not EXIT:
        client_message = sock.recv(4)

        if client_message != b'':
            driver_command = struct.unpack('i', client_message)

            if driver_command == driver_commands["increase speed"]:
                stepper_speed += 10
                change_stepper_speed()
                print("CURRENT SPEED", stepper_speed)

            elif driver_command == driver_commands["decrease speed"]:
                stepper_speed -= 10
                change_stepper_speed()
                print("CURRENT SPEED", stepper_speed)

            elif driver_command == driver_commands["home"]:
                moving_direction = 1
                GPIO.output(PIN_DIR, moving_direction)

        else:
            EXIT = True

        time.sleep(0.01)


def send_values(values_list, mv_direction):
    b_message = struct.pack('12f?', *values_list, mv_direction)
    sock.send(b_message)


def callback_optic_sensor(_):
    global old_optic_sensor_value, optic_sensor_value, moving_direction, DIRECTION_CHANGED

    optic_sensor_value = GPIO.input(PIN_OPTIC_SENSOR)
    if optic_sensor_value != old_optic_sensor_value:
        if optic_sensor_value == 1:
            moving_direction = not moving_direction
            GPIO.output(PIN_DIR, moving_direction)
            DIRECTION_CHANGED = True
        old_optic_sensor_value = optic_sensor_value


def init_gpio():
    # GPIO.BCM/GPIO.BOARD определяют распиновку.
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(PIN_STEP, GPIO.OUT)
    GPIO.setup(PIN_DIR, GPIO.OUT)
    GPIO.setup(PIN_OPTIC_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def start_pwm():
    # Запускаю генерацию шим на STEP пине
    res = GPIO.PWM(PIN_STEP, stepper_speed)
    res.start(50)
    return res


if __name__ == "__main__":
    try:
        init_gpio()
        pwm = start_pwm()
        GPIO.output(PIN_DIR, moving_direction)
        GPIO.add_event_detect(PIN_OPTIC_SENSOR, GPIO.BOTH, callback=callback_optic_sensor)

        bus = SMBus(1)
        sens = analog_hall_lib.AnHall(bus)

        sock = init_socket()

        receive_commands_thread = threading.Thread(target=receive_commands)
        receive_commands_thread.start()

        while not EXIT:
            if DIRECTION_CHANGED:
                # Добавляю 1 чтоб отличать сообщение о направление когда направление изменилось
                # от сообщения когда не изменилось
                DIRECTION_CHANGED = False

            sensor_values = sens.read_all_sensors()
            send_values(sensor_values, moving_direction)

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
        print("CLEAN")
