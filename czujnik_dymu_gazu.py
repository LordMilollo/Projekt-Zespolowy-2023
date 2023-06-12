from machine import Pin, ADC
import utime
from math import exp, log


class MQ2(object):
    ATTEMPTS_IN_CYCLE = 1
    MAX_VOLTAGE = 65535
    BASE_RESISTANCE = 9.83
    DELAY = 500
    ACCURATE_MEASUREMENT = 2

    def __init__(self, pin_num, board_resistance=10, base_voltage=3.3,
                 measurement=ACCURATE_MEASUREMENT):
        self.base_voltage = base_voltage
        self.board_resistance = board_resistance
        self.measurement = measurement
        self.pin_num = ADC(pin_num)
        self.last_measurement = utime.ticks_ms()
        self.resistance = -1
        self.temp_resistance = None
        self.data_is_accurate = False

    def calibration(self, resistance=-1):
        if resistance == -1:
            resistance = 0
            for _ in range(0, self.ATTEMPTS_IN_CYCLE + 1):
                resistance += self.resistance_calculation(self.pin_num.read_u16())
                utime.sleep_ms(self.ATTEMPTS_IN_CYCLE)
                resistance = resistance / (self.BASE_RESISTANCE * self.ATTEMPTS_IN_CYCLE)
        self.resistance = resistance

    def resistance_calculation(self, raw_voltage):
        voltage_ratio = raw_voltage / self.MAX_VOLTAGE
        sensor_voltage = voltage_ratio * self.base_voltage
        sensor_resistance = (self.base_voltage - sensor_voltage) / sensor_voltage * self.board_resistance
        return sensor_resistance

    def read_resistance(self):
        if self.measurement == self.ACCURATE_MEASUREMENT:
            total_resistance = 0
            for _ in range(self.ATTEMPTS_IN_CYCLE):
                raw_voltage = self.pin_num.read_u16()
                resistance = self.resistance_calculation(raw_voltage)
                total_resistance += resistance
                utime.sleep_ms(self.ATTEMPTS_IN_CYCLE)
            average_resistance = total_resistance / self.ATTEMPTS_IN_CYCLE
            self.temp_resistance = average_resistance
            self.data_is_accurate = True
            self.last_measurement = utime.ticks_ms()
        else:
            raw_voltage = self.pin_num.read_u16()
            total_resistance = self.resistance_calculation(raw_voltage)
            self.data_is_accurate = False
        return total_resistance

    def read_scaled(self, x, y):
        return exp((log(self.read_ratio()) - y) / x)

    def read_ratio(self):
        return self.read_resistance() / self.resistance


class MQ2Sensor(MQ2):
    def __init__(self, pin_num, board_resistance=10, base_voltage=3.3,
                 measurement=MQ2.ACCURATE_MEASUREMENT):
        super().__init__(pin_num, board_resistance, base_voltage, measurement)

    def read_smoke_data(self):
        smoke_data = self.read_scaled(-0.45, 2.95)
        return smoke_data

    def read_lpg_data(self):
        smoke_data = self.read_scaled(-0.38, 3.21)
        return smoke_data

    def read_methane_data(self):
        smoke_data = self.read_scaled(-0.42, 3.54)
        return smoke_data

    def read_hydrogen_data(self):
        hydrogen_data = self.read_scaled(-0.48, 3.32)
        return hydrogen_data


MQ2_PIN = 26
BASE_VOLTAGE = 3.3

mq2 = MQ2Sensor(MQ2_PIN, BASE_VOLTAGE)

mq2.calibration()

while True:
    smoke = mq2.read_smoke_data()
    lpg = mq2.read_lpg_data()
    methane = mq2.read_methane_data()
    hydrogen = mq2.read_hydrogen_data()

    print('Dym: ', smoke, ' LPG: ', lpg, ' Metan: ', methane, ' Wodór: ', hydrogen)
    utime.sleep(0.5)
