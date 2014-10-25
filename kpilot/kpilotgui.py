import time
import sys
import logging
import io
import cPickle as pickle
import string

from kivy.app import App
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

import pilot
from uix.joystick import Joystick
from uix.fancyslider import FancySlider
from uix.consoleinput import ConsoleInput




class RootLayout(FloatLayout):
    mainview_log = ObjectProperty()
    speed = ObjectProperty()
    rot_speed = ObjectProperty()
    statslabel = ObjectProperty()
    label1 = ObjectProperty()
    fpvideo = ObjectProperty()
    bVid = ObjectProperty()
    log = ObjectProperty()
    console_input  = ObjectProperty()
    logstream = io.StringIO()
#    logstream = ObjectProperty()
    
#    def on_logstream(self, *args):
#        self.mainview_log.text = self.logstream.getvalue()

    def ConsoleCmd (self, data):
        data = unicode (data,'utf-8');
        if data == "" : return False
        self.log.debug (u"Console input {}".format(data))
        request = data.split(' ');
        cmd = request.pop(0).lower() 
        cmd = cmd.strip("\n")
        if (data[0:1] == '-'):
            pilot.send ("SAY "+pickle.dumps(data[1:]))
            self.log.info (u"Pronouncing {}".format(data[1:])) 
        elif cmd == 'q' or cmd == 'quit':
            App.get_running_app().stop()
        elif cmd == 'send':
            pkt = ' '.join(request)
            pilot.send (pkt)
            self.log.info (u"Sent: {}".format(pkt))

        else:
            self.log.info (u"Unknown command '{}'".format(cmd.encode('unicode_escape')))

        self.console_input.text = ''
        return True

    def TracksMove (self):
        pilot.send ("TRACKS %0.2f %0.2f" % (self.joy1.pos[0],self.joy1.pos[1]))       

    def TracksStop (self):
        pilot.send ("TRACKS 0 0")

    def SetServo1 (self, smth=""): 
        pilot.send ("SERVO 1 %0d" % self.servo1.value)
#        self.servo1label.text = "Head ^%03dv" % self.servo1.value

    def SetServo2 (self, smth=""): 
        pilot.send ("SERVO 2 %0d" % self.servo2.value)
#        self.servo2label.text = "Head <%03d>" % self.servo2.value

    def VideoPlayerButton (self, *args):
        if self.bVid.state == 'normal':
          self.log.info (u"Video player stoping")
          self.bVid.text = '|>'
          self.fpvideo.state = 'stop'
          self.fpvideo.source = ''
          self.fpvideo.opacity = 0          
        elif self.bVid.state == 'down':
          self.log.info (u"Video player starting")
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
        self.log.info (u"Camera off requested")
      else:  
        pilot.send ("CAM RES " + self.bCam.text) 
        self.bVid.state = 'normal'
        self.VideoPlayerButton (self)
        self.bVid.state = 'down'
        Clock.schedule_once(self.VideoPlayerButton, 4)
        self.log.info (u"Camera requested with {} resolution".format(self.bCam.text))


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
        logbuffer = u""
        
        for line in (self.logstream.getvalue()).split(u"\n")[-15:]:
          if line.find('DEBUG') > 0:
             color = "AAAAAA"
          elif line.find('INFO') > 0:
             color = "AAFFAA"
#          elif line.find('NOTICE') > 0:
#             color = "AAAAFF"         
          elif line.find('WARN') > 0:
             color = "EEEE99"
          elif line.find('ERROR') > 0:
             color = "FFAAAA"
          elif line.find('CRIT') > 0:
             color = "FFAAAA"
          else:
             color = "FFFFFF"
          if line != "": logbuffer += u"[color={}]{}[/color]\n".format(color,line)

        self.mainview_log.text = logbuffer[:-1] #last char is always cr

#        while len(pilot.udpinmsgs) > 0 :
#            try: self.log_box.text = pilot.udpinmsgs.pop(0) + "\n"
#            except UnicodeDecodeError: self.log_box.text += "[...]"
        

class kPilotApp(App):   
    mainform = ObjectProperty()
    desktop = BooleanProperty()
    printset = set(string.printable)

    def __init__(self, **kwargs):
        super(kPilotApp, self).__init__(**kwargs)
        self._keyboard_init()

    def _keyboard_init(self):
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down = self._on_keyboard_down)

    def _keyboard_closed(self):
        self.mainform.log.debug (u"Keyboard closed")
        self._keyboard.unbind(on_key_down = self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if set(text).issubset(self.printset) and text != "\r":
            self.mainform.console_input.text += text
        self.mainform.console_input.focus = True

        return True



    def build(self):
        #init config
        self.desktop = bool(Config.get('kivy', 'desktop'))
        #init gui
        self.mainform = RootLayout()
        #init logger
        self.mainform.logstream = io.StringIO()
        self.mainform.logstreamhandler = logging.StreamHandler(self.mainform.logstream)
        self.mainform.logstreamhandler.setFormatter(logging.Formatter("%(asctime)s [%(name)s#%(levelname)s]: %(message)s","%H:%M:%S"))
        self.mainform.logstreamhandler.setLevel(logging.INFO)
        self.mainform.consoleloghandler = logging.StreamHandler(sys.stdout)
        self.mainform.consoleloghandler.setFormatter(logging.Formatter("%(asctime)s [%(name)s#%(levelname)s]: %(message)s"))
        self.mainform.consoleloghandler.setLevel(logging.DEBUG)
        self.mainform.log = logging.getLogger('Pilot')
        self.mainform.log.setLevel(logging.DEBUG)
        self.mainform.log.addHandler(self.mainform.logstreamhandler)
        self.mainform.log.addHandler(self.mainform.consoleloghandler)
        #init backend
        pilot.init(self.mainform.log)
        #init sheduler
        Clock.schedule_interval(self.mainform.logupdate, .1)
#        Clock.schedule_interval(pilot.udpreader, .05)


        self.mainform.log.info (u"Running client on Python " + sys.version)
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
