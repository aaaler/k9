#!/usr/bin/env python
import A20_GPIO as GPIO
import time
import os

#init module
GPIO.init()
#configure module
pins = 76 #number of gpio's

for root, dirs, filenames in os.walk('/sys/class/gpio/'):
    for d in dirs:
        if d=='gpiochip1': continue
        print d


#GPIO.setcfg(GPIO.PIN#, GPIO.OUTPUT)
#GPIO.setcfg(GPIO.PIN#, GPIO.INPUT)
#read the current GPIO configuration
#config = GPIO.getcfg(GPIO.PIN#)
#set GPIO high
#GPIO.output(GPIO.PIN#, GPIO.HIGH)
#set GPIO low
#GPIO.output(GPIO.PIN#, GPIO.LOW)
#read input
#state = GPIO.input(GPIO.PIN#)
#cleanup

for x in range (1,100):
  GPIO.output(GPIO.PIN3_6, GPIO.LOW)
  time.sleep (0.2)
  GPIO.output(GPIO.PIN3_6, GPIO.HIGH)
  time.sleep (0.2)
GPIO.cleanup()

