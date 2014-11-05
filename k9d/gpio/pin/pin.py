
class pin(object):
    from pyA20.gpio import port
    from pyA20.gpio import connector
    from pyA20.gpio import gpio as gpio

    def __init__ (self, pin_id, direction = 1, value = 0):
        self._pinid = pin_id
        self._direction = direction
        self._value = value
        gpio.init()
        gpio.setcfg (pin_id, dir)
        gpio.output (pin_id, value)

    @property
    def value (self):
        if self._direction == 0: #input
            self._value = gpio.input(self._pinid)
        return self._value

    @value.setter
    def value (self, value):
        if self._direction == 1: #output
            self._value = value
            gpio.output (self._pinid, value)
            return True
        else        
            return False

    @property
    def direction (self):
        return self._direction

    @direction.setter
    def direction (self, direction):
        if self._direction != direction: #changes needed?
            self._direction = direction
            gpio.setcfg (self._pinid, dir)
            return True
        else        
            return False
    
