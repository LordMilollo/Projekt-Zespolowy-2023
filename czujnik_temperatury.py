import utime
from rp2 import PIO, asm_pio
from machine import Pin
from twilio.rest import Client

DHT11_PIN = 15
DELAY = 100
SM_DELAY = 10000


@asm_pio(set_init=(PIO.OUT_HIGH), autopush=True, push_thresh=8)
def DHT11_PIO():
    mov(y, 1)
    pull()
    mov(x, osr)
    set(pindirs, 1)
    set(pins, 0)
    label('start')
    jmp(x_dec, 'start')
    set(pindirs, 0)

    set(x, 31)
    label("phase_A")
    jmp(pins, "goto_B")
    jmp(x_dec, "phase_A")

    label("Error")
    in_(y, 1)
    jmp("Error")

    label("goto_B")
    set(x, 31)
    label("phase_B")
    jmp(x_dec, "Stage_B")
    jmp('Error')
    label("Stage_B")
    jmp(pin, "phase_B")

    set(x, 31)
    label('phase_C')
    jmp(pin, 'goto_D')
    jmp(x_dec, 'phase_C')
    jmp('Error')

    label('goto_D')
    set(x, 31)
    label('phase_D')
    jmp(x_dec, 'Stage_D')
    jmp('Error')
    label('Stage_D')
    jmp(pin, 'phase_D')

    set(x, 31)
    label('phase_E')
    jmp(pin, 'goto_F')
    jmp(x_dec, 'phase_E')
    jmp('Error')

    label('goto_F')
    nop()[20]
    in_(pins, 1)
    set(x, 31)
    jmp('phase_D')


class DHT11Sensor:
    def __init__(self, PIN, state_machine_ID=0):
        self.PIN = PIN
        self.state_machine_ID = state_machine_ID
        self.PIN.init(PIN.IN, PIN.PULL_UP)
        self.state_machine = rp2.StateMachine(self.state_machine_ID)

    def read_data(self):
        utime.sleep_ms(DELAY)

        self.state_machine.init(DHT11_PIO, freq=500000, set_base=self.PIN, in_base=self.PIN, out_base=self.PIN,
                                jmp_pin=self.PIN)
        self.state_machine.put(SM_DELAY)
        self.state_machine.active(1)

        values = [self.state_machine.get() for _ in range(5)]
        self.state_machine.active(0)

        checksum = sum(values[:4])
        if (checksum & 0xff) == values[4]:
            humidity = values[0] + values[1] / 10
            temperature = values[2] + values[3] / 10
            return temperature, humidity
        else:
            return None, None


dht11 = DHT11Sensor(Pin(DHT11_PIN))

is_temp_sms_sent = False
is_hum_sms_sent = False

while True:
    is_sms_sent = False
    temperature, humidity = dht11.read_data()
    if temperature is None:
        print("Wystąpił błąd")

    else:
        print('Temperatura: ', temperature, '°C', ' Wilgotność powietrza: ', humidity, '%')
        utime.sleep(3)

    if temperature > 40:
        while not is_temp_sms_sent:
            is_temp_sms_sent = True
            account_sid = "AC74df43473c214b4cb92f7f8f2daa050d"
            auth_token = "f5a625baecba793e98efc191bc1ba714"
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body='Uwaga! Zarejestrowano wysoką temperaturę: '+str(temperature)+'°C',
                from_='+14066257191',
                to='+48<numer_telefonu>'
            )

    if humidity > 85:
        while not is_hum_sms_sent:
            is_hum_sms_sent = True
            account_sid = "AC74df43473c214b4cb92f7f8f2daa050d"
            auth_token = "f5a625baecba793e98efc191bc1ba714"
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body='Uwaga! Zarejestrowano wysoką wilgotność: '+str(humidity)+'%',
                from_='+14066257191',
                to='+48<numer_telefonu>'
            )
