import machine

#Simple script to turn on LED on board

led = machine.Pin("LED", machine.Pin.OUT)
led.off()
led.on()
