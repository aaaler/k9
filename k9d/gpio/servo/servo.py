from gpio.pwmpin import pwmpin

class servo (pwmpin):
    def __init__ (self, kpinid, pos = 90, minp = 544, maxp = 2400):
        super(servo,self).__init__(kpinid, frequency = 50, duty = 1)
        self._pos = pos
        self._minp = minp
        self._maxp = maxp
        self._delta = maxp - minp
        self.pulse = self._pos2pulse(pos)

    def _pos2pulse (self, pos):
        return self._minp + ( (pos/255.) * self._delta)

    @property
    def pos (self):
        return self._pos

    @pos.setter
    def pos (self,pos):
        self.pulse = self._pos2pulse(pos)
        return True



