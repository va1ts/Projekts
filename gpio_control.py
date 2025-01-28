import RPi.GPIO as GPIO

# GPIO Setup (assuming fan is connected to GPIO pin 17)
GPIO.setmode(GPIO.BCM)
fan_pin = 18
GPIO.setup(fan_pin, GPIO.OUT)

def activate_fan():
    GPIO.output(fan_pin, GPIO.HIGH)  # Turn on fan
    print("Fan activated.")

def deactivate_fan():
    GPIO.output(fan_pin, GPIO.LOW)  # Turn off fan
    print("Fan deactivated.")
