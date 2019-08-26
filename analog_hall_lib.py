# script must be on Raspberry

from smbus import SMBus
from i2chandling import i2c_detect
import time

"""
The default configuration of configuration register, except for the multiplexer,
which is configured to work with one of four sensors.
List since configuration occurs on the I2C bus in packets of two bytes.
"""
SENSOR_NUM0 = [0x44, 0xE3]
SENSOR_NUM1 = [0x54, 0xE3]
SENSOR_NUM2 = [0x64, 0xE3]
SENSOR_NUM3 = [0x74, 0xE3]
correct_address_list = [0x48, 0x49, 0x4A, 0x4B]


class AnHall:

    def __init__(self, bus,
                 adc_addresses=None,
                 adc_auto_search=True,
                 ):
        self.bus = bus

        self.adc_addresses = 0
        if adc_auto_search:
            self.adc_addresses = list(set(correct_address_list) & set(i2c_detect(bus)))
            if self.adc_addresses == 0:
                print("Addresses not found, please try again or enter addresses manually")
                return -1
        else:
            self.adc_addresses = adc_addresses
        print("ADC addresses:", self.adc_addresses)

        if len(self.adc_addresses) > 4:
            print("Too much I2C-devices.\n"
                  "Please pass the list of desired addresses with length no more than 4 like parameter "
                  "'adc_addresses' and set flag 'adc_auto_search' as False.")
            return -1

        for el in self.adc_addresses:
            # 1 - Config Register address
            self.bus.write_i2c_block_data(el, 1, SENSOR_NUM0)

    # This function changes the configuration register of a single ADC with number 'adc_num' to reading sensor with
    # number 'sens_num'
    def switch_sens(self, adc_num, sens_num):
        if sens_num == 0:
            self.bus.write_i2c_block_data(self.adc_addresses[adc_num], 1, SENSOR_NUM0)
        if sens_num == 1:
            self.bus.write_i2c_block_data(self.adc_addresses[adc_num], 1, SENSOR_NUM1)
        if sens_num == 2:
            self.bus.write_i2c_block_data(self.adc_addresses[adc_num], 1, SENSOR_NUM2)
        if sens_num == 3:
            self.bus.write_i2c_block_data(self.adc_addresses[adc_num], 1, SENSOR_NUM3)

    def read_all_sensors(self):
        adc_values = [float(0) for i in range(4 * len(self.adc_addresses))]
        res_list = [float(0) for i in range(4 * len(self.adc_addresses))]
        adc_val_counter = 0

        for adc_num in range(len(self.adc_addresses)):
            for sens_num in range(4):
                self.switch_sens(adc_num, sens_num)
                time.sleep(0.00001)
                adc_values[adc_val_counter] = self.bus.read_i2c_block_data(self.adc_addresses[adc_num], 0, 2)
                adc_val_counter += 1
        self.switch_sens(0, 0)

        for n in range(len(adc_values)):
            res_list[n] = (adc_values[n][0] << 8) + adc_values[n][1]
            res_list[n] = ((2048 * res_list[n] / 32767) - 1020) / (-11)
        return res_list

    def read_sensor(self, sensor_num):
        if sensor_num > (4 * len(self.adc_addresses) - 1) or sensor_num < 0:
            print("А sensor with this number does not exist.")
            return -1

        adc_num = sensor_num // 4
        sens_num = sensor_num % 4
        self.switch_sens(adc_num, sens_num)
        # 0 - number of ADC register with sensor data,
        # 2 - two bytes are read from the sensor.
        adc_value = self.bus.read_i2c_block_data(self.adc_addresses[adc_num], 0, 2)

        res = (adc_value[0] << 8) + adc_value[1]
        res = ((2048 * res / 32767) - 1020) / (-11)
        return res
