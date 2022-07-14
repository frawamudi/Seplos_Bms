import RPi.GPIO as GPIO
import time

led = 18
switch = 31

GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT)
GPIO.setup(switch, GPIO.IN)

for i in range(10):
#while True:
    GPIO.output(led, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(led, GPIO.LOW)

