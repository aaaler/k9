from time import sleep
from A20_GPIO import *

#initialize module
init()

#set pin as output
if getcfg(PIN3_7) == INPUT:
    setcfg(PIN3_7, OUTPUT)

while True:
    sleep(0.5)
    output(PIN3_7, HIGH)
    sleep(0.5)
    output(PIN3_7, LOW)
    
