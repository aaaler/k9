This package provides class to control the GPIO on Olinuxino A20.
Current release does no support any peripheral functions.

Example
=======

Typical usage::
    
    #!/usr/bin/env python

    import A20_GPIO as GPIO
    
    x - connector name
    y - pin number

    #init module
    GPIO.init()
    
    #configure module
    GPIO.setcfg(PINx_y, GPIO.OUTPUT)
    GPIO.setcfg(PINx_y, GPIO.INPUT)
        
    #read the current GPIO configuration
    config = GPIO.getcfg(PINx_y)
    
    #set GPIO high
    GPIO.output(PINx_y, GPIO.HIGH)
    
    #set GPIO low
    GPIO.output(PINx_y, GPIO.LOW)
    
    #read input
    state = GPIO.input(PINx_y)
    
    #cleanup 
    GPIO.cleanup()
    

Warning
=======

    Before using this tool it is HIGHLY RECOMENDED to check Olinuxino 
    A20 schematic. 

