#!/usr/bin/env python
import A20_GPIO as GPIO
import time
from optparse import OptionParser
#init module
GPIO.init()

p={
'LED': GPIO.PIN3_6,
'PWM': GPIO.PIN3_8,
'DIRA': GPIO.PIN3_10,
'DIRB':  GPIO.PIN3_12}

usage = "usage: %prog [options] action \n actions: fwd rev stop"
parser = OptionParser(usage)
(options, args) = parser.parse_args()

if len(args) != 1:
        parser.error("incorrect number of arguments")



#init ports:
for pin in p.values() :
  GPIO.setcfg(pin, GPIO.OUTPUT) #all out
  GPIO.output(pin, GPIO.LOW) #all low

time.sleep (0.5)
GPIO.output(p['LED'], GPIO.HIGH)


if args[0] == 'fwd':
  GPIO.output(p['DIRA'], GPIO.HIGH)
  GPIO.output(p['PWM'], GPIO.HIGH)
elif args[0] == 'rev':
  GPIO.output(p['DIRB'], GPIO.HIGH)
  GPIO.output(p['PWM'], GPIO.HIGH)
elif args[0] == 'stop':
  GPIO.output(p['PWM'], GPIO.LOW)

else :
  parser.error("actions: fwd rev stop")

GPIO.cleanup ();

