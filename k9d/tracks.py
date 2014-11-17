import time
from threading import Timer
import gpio

class Tracks(object):
    def __init__ (self, _1a, _1b, _1pwm, _2a, _2b, _2pwm, cal_min = 50, freq = 50):
        self.cal_min = cal_min
        self._1a = gpio.pin (_1a)
        self._1b = gpio.pin (_1b)
        self._2a = gpio.pin (_2a)
        self._2b = gpio.pin (_2b)
        self._1pwm = gpio.pwmpin (_1pwm, freq, 0)
        self._2pwm = gpio.pwmpin (_2pwm, freq, 0)
        self._freq = freq 
        self.tracktimeout = time.time()
        self.trackl = 0.
        self.trackr = 0.
        self.fwd_obstacle_failsafe = False
        self.stoptimer = None
        self.vectorx = 0. 
        self.vectory = 0.
    
    def __del__ (self):
        self.neutral()

    def vector (self,X,Y) :
        fX = float(X);
        fY = float(Y);
        timeout = 100 #not impl.
        self.tracktimeout = time.time() + (int(timeout)/1000)
        if fX == 0. and fY == 0. :
            self.neutral()
            trackl = 0.
            trackr = 0.
        else:
            if self.stoptimer:
                self.stoptimer.cancel()
                self.stoptimer = None

            if fY > 0:
            #8 <LFWD> <LREV> <LPWM> <RFWD> <RREV> <RPWM>;
                trackl = fY + (fX*fY)
                trackr = fY - (fX*fY)
            elif fY < 0:
                trackl = fY + (fX*fY)
                trackr = fY - (fX*fY)
            elif fY == 0:
                trackl = fY + fX
                trackr = fY - fX
            if trackr > 1: trackr = 1
            if trackl > 1: trackl = 1
            if trackr < -1: trackr = -1
            if trackl < -1: trackl = -1
            if self.fwd_obstacle_failsafe:
                if trackr > 0: trackr = 0
                if trackl > 0: trackl = 0
         
        #        out="8 %0d %0d %0d %0d %0d %0d;" % (self.trackl>0,self.trackl<0,abs(self.trackr)*(255-self.cal_track_min)+self.cal_track_min,self.trackr>0,self.trackr<0,abs(self.trackl)*(255-self.cal_track_min)+self.cal_track_min)
            self.set(trackl, trackr)
            
        self.trackl = trackl
        self.trackr = trackr
        self.vectorx = fX
        self.vectory = fY
        return True

    def set (self,  trackl, trackr):
        self._1a.value = (trackr > 0)
        self._1b.value = (trackr < 0)
        self._2a.value = (trackl > 0)
        self._2b.value = (trackl < 0)      
        self._1pwm.duty = abs(trackr)*(100-self.cal_min)+self.cal_min
        self._2pwm.duty = abs(trackl)*(100-self.cal_min)+self.cal_min
        
        
    def stop (self):
        if self.stoptimer:
            self.stoptimer.cancel()
            self.stoptimer = None
        self.stoptimer = Timer (1, self.neutral)
        self.brake()

    def neutral (self):
        if self.stoptimer: self.stoptimer = None
        self._1a.value = 0
        self._1b.value = 0
        self._2a.value = 0
        self._2b.value = 0
        self._1pwm.duty = 0
        self._2pwm.duty = 0


    def brake (self):
        self._1a.value = 1
        self._1b.value = 1
        self._2a.value = 1
        self._2b.value = 1
        self._1pwm.duty = 100
        self._2pwm.duty = 100

    def freq (self,fr):
        self._1pwm.freq = fr
        self._2pwm.freq = fr
        self._freq = fr
        
