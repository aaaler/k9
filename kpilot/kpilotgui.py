from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line , Rectangle, Point, GraphicException
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.spinner import Spinner
import time
import sys


import pilot
from joystick import Joystick
from fancyslider import FancySlider




class MainTabs(TabbedPanel):
    log_box = ObjectProperty()
    speed = ObjectProperty()
    rot_speed = ObjectProperty()
    statslabel = ObjectProperty()
    label1 = ObjectProperty()
    fpvideo = ObjectProperty()
    bVid = ObjectProperty()

    def TracksMove (self):
        pilot.send ("TRACKS %0.2f %0.2f" % (self.joy1.pos[0],self.joy1.pos[1]))
#        print ("TRACKS %0.2f %0.2f" % (self.joy1.pos[0],self.joy1.pos[1]))

    def TracksStop (self):
        pilot.send ("TRACKS 0 0")
#        print ("Tracks stop")

    def SetServo1 (self, smth=""): 
        pilot.send ("SERVO 1 %0d" % self.servo1.value)
#        self.servo1label.text = "Head ^%03dv" % self.servo1.value

    def SetServo2 (self, smth=""): 
        pilot.send ("SERVO 2 %0d" % self.servo2.value)
#        self.servo2label.text = "Head <%03d>" % self.servo2.value

    def VideoPlayerButton (self, *args):
        if self.bVid.state == 'normal':
          self.log_box.text += "video stop \n"
          self.bVid.text = '|>'
          self.fpvideo.state = 'stop'
          self.fpvideo.source = ''
          self.fpvideo.opacity = 0          
        elif self.bVid.state == 'down':
          self.log_box.text += "video start \n"                    
          self.fpvideo.source = 'http://192.168.0.99:8080/?action=stream'
          self.bVid.text = '||'
          self.fpvideo.state = 'play'
          self.fpvideo.opacity = 1          
        return True

    def SetCamera (self):    
      if self.bCam.text == 'Camera off': 
        pilot.send ("CAM OFF")
        self.bVid.state = 'normal'
        self.VideoPlayerButton (self)
      else:  
        pilot.send ("CAM RES " + self.bCam.text) 
        self.bVid.state = 'normal'
        self.VideoPlayerButton (self)
        self.bVid.state = 'down'
        Clock.schedule_once(self.VideoPlayerButton, 4)



    def logupdate(self, dt):
        while pilot.udpreader(): pass
        try: 
            self.label1.text = "Li-ion: %0.2fV\n +5: %0.2fV\n"  % (float(pilot.stats['A3'])*0.009774078,float(pilot.stats['A2'])*0.0096850)
            self.label1.text += "CPU BAT: {:d}% \n{:d}mA \nExt: {:d}mA \nState: {}\n".format(pilot.stats['cpu_bcap'],pilot.stats['cpu_bcur'],pilot.stats['cpu_accur'],pilot.stats['cpu_bstate']) 
            self.label1.text += "stat:{:.2f}s {:d}b\nSonar: {:.2f}M\n".format(pilot.statsdtime,pilot.stats['size'], float(pilot.stats['Son'])/1000)
            self.label1.text += "Wifi: {} {} {}\n".format(pilot.stats['wifi_br'],pilot.stats['wifi_lq'],pilot.stats['wifi_sl'])

            self.statslabel.text = "L: {:+.2f} R: {:+.2f}".format(pilot.stats['trackr'], pilot.stats['trackl'])
            self.servo1label.text = "Head ^%03dv" % int(pilot.stats['S1'])
            self.servo2label.text = "Head <%03d>" % int(pilot.stats['S2'])
#            self.servo1.value = int(pilot.stats['S1'])
#bad idea really, undefined behavior.

        except KeyError as e: self.statslabel.text = "not yet " + e.message
#        while len(pilot.udpinmsgs) > 0 :
#            try: self.log_box.text = pilot.udpinmsgs.pop(0) + "\n"
#            except UnicodeDecodeError: self.log_box.text += "[...]"
        

class kPilotApp(App):   
    mainform = ObjectProperty()
    desktop = BooleanProperty()
    def build(self):
        self.mainform = MainTabs()
        pilot.init()
        self.desktop = bool(Config.get('kivy', 'desktop'))
        Clock.schedule_interval(self.mainform.logupdate, .1)
#        Clock.schedule_interval(pilot.udpreader, .05)
        self.mainform.log_box.text = "Running client on Python " + sys.version + "\n"
        self.mainform.log_box.text += "K-9 Greets the master :-)\n"
        return self.mainform
    def on_pause(self):
      # Here you can save data if needed
      # called on android background or standby
        return True

    def on_stop(self):
        if self.desktop:
          Config.set('graphics', 'height', Window.height)
          Config.set('graphics', 'width', Window.width)        
        Config.write()
        return True

if __name__ == '__main__':
    kPilotApp().run()