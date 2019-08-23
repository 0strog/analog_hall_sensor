# script for contain some functions for i2c bus

def i2c_detect(bus):
    i2c_addresses_list = []
    for i in range(3, 128):
        try:
            bus.read_byte(i)
            i2c_addresses_list.append(i)
        except OSError:
            pass
    return i2c_addresses_list
