#!/usr/bin/env python
import A20_GPIO as GPIO
import time
from optparse import OptionParser
#init module
GPIO.init()

p={
'LED': GPIO.PIN3_7}

usage = "usage: %prog [options] halfperiodtime"
parser = OptionParser(usage)
(options, args) = parser.parse_args()

if len(args) != 1:
        parser.error("incorrect number of arguments")



#init ports:
for pin in p.values() :
  GPIO.setcfg(pin, GPIO.OUTPUT) #all out
  GPIO.output(pin, GPIO.LOW) #all low

time.sleep (0.5)
pt= time.time();
#print "time"+repr(pt)+"\n"
hp=float(args[0])
generating = 1
while generating :
  GPIO.output(p['LED'], GPIO.HIGH)
  time.sleep (hp)
  GPIO.output(p['LED'], GPIO.LOW)
  time.sleep (hp)
  t= time.time();
  d= t - pt
  pt=t
#  print "diff "+repr(d)+" \t clear "+repr(d-2*hp)+" seconds\n"


print "bye!\n"

GPIO.cleanup ();
