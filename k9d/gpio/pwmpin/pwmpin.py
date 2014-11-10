import os
class pwmpin(object):
    def __init__ (self, kpinid, frequency = 50, duty = 50):
        self._kpinid = kpinid
        self._freq = frequency
        self._duty = duty
        self._period = 100000
        self._pulse = 50000
        self._export ()
        self.freq = frequency

    def __del__ (self):
        self._unexport()
    
    def _export (self):
        kpinid = self._kpinid
        iopath='/sys/class/soft_pwm/pwm' + str(kpinid)
        if not os.path.exists(iopath):
            f = open('/sys/class/soft_pwm/export','w')
            f.write(str(kpinid))
            f.close()

    def _unexport (self):
        kpinid = self._kpinid
        iopath='/sys/class/soft_pwm/pwm' + str(kpinid)
        if os.path.exists(iopath):
            f = open('/sys/class/soft_pwm/unexport','w')
            f.write(str(kpinid))
            f.close()

    def _setperiod (self):
        kpinid = self._kpinid
        iopath='/sys/class/soft_pwm/pwm' + str(kpinid)
        if os.path.exists(iopath):
            f = open(iopath + '/period','w')
            f.write(str(self._period))
            f.close()

    def _setpulse (self):
        kpinid = self._kpinid
        iopath='/sys/class/soft_pwm/pwm' + str(kpinid)
        print iopath
        if os.path.exists(iopath):
            f = open(iopath + '/pulse','w')
            f.write(str(self._pulse))
            f.close()

    @property
    def period (self):
        return self._period

    @period.setter
    def period (self,period):
        self._period = int(period)
        if (self._duty != -1): self._duty = -1
        if (self._freq != -1): self._freq = -1
        return self._setperiod()

    @property
    def pulse (self):
        return self._pulse

    @pulse.setter
    def pulse (self,pulse):
        self._pulse = int(pulse)
        if (self._duty != -1): self._duty = -1
        return self._setpulse()


    @property
    def freq (self):
        return self._freq

    @freq.setter
    def freq (self, freq):
        self._freq = freq
        self._period = int ((1./freq) * 1000000)
        self._setperiod()
        self.duty=self._duty


    @property
    def duty (self):
        return self._duty

    @duty.setter
    def duty (self, duty):
        self._duty = duty
        self._pulse = int((duty / 100.) * self._period  )
        self._setpulse()

