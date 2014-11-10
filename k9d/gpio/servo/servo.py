from gpio.pwmpin import pwmpin

class servo (pwmpin):
    def __init__ (self, kpinid, pos = 90, minp = 544, maxp = 2400):
        self._pos = pos
        self._minp = minp
        self._maxp = mmaxp
        self._delta = maxp - minp
        super(servo,self).__init__(kpinid, frequency = 50, duty = 0)
        self.pulse = self._pos2pulse(pos)

    def _pos2pulse (self, pos):
        return self._min + ( (pos/255.) * self._delta)

    @property
    def pos (self):
        return self._pos

    @pos.setter
    def setpos (self,pos)
        self.pulse = self._pos2pulse(pos)



