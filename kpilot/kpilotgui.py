from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.uix.slider import Slider
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line , Rectangle, Point, GraphicException
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.spinner import Spinner


import sys
import pilot
import time



Builder.load_string("""
<Widget>:
#    canvas.after:
#        Line:
#            rectangle: self.x+1,self.y+1,self.width-1,self.height-1
#            dash_offset: 5
#            dash_length: 3

<Label>:
    canvas.before:
        Color:
            rgba: 0.5, 0.5, 0.5, 0.4
        Rectangle:
            pos: self.pos
            size: self.size

    background_color: (0.3, 0.3, 0.3, 1)        
<MainTabs>:
    size_hint: 1, 1
    pos_hint: {'center_x': .5, 'center_y': .5}
    do_default_tab: False
    log_box: log_box
    servo1: servo1
    servo2: servo2
    servo1label: servo1label
    servo2label: servo2label
    statslabel: statslabel
    label1:label1
    joy1:joy1
    cal_trackrotate:cal_trackrotate
    cal_trackmove:cal_trackmove
    bVid:bVid
    fpvideo:fpvideo

    TabbedPanelItem:
        text: 'Control'
        border: [1, 1, 1, 1]


        FloatLayout:
            Video:
                id:fpvideo
                source: 'http://192.168.0.99:8080/?action=stream'
                state: 'stop'
                opacity: 0

            BoxLayout:    
                BoxLayout:
                    size_hint: .2, 1
                    orientation: 'vertical'        
                    Label:
                        text: 'l1'
                        id: label1
                        size_hint: 1, .7
                        halign: 'right'
                        valign: 'top'
                        font_size: '13sp'
                        text_size: self.size
                        background_color: (1, 1, 1, 1)        
                    Label:
                        text: 'Head ^v'
                        size_hint: 1, .05
                        pos_hint: {'center_x': 0.5, 'top':1}
                        id: servo1label
                        font_size: '14sp'
                    Slider:
                        id: servo1
                        step: 2
                        size_hint: 1, 1
                        range: 1, 180
                        value: 90
                        on_value: root.SetServo1()
                        orientation: 'vertical'
                        pos_hint: {'center_x': 0.5}

                BoxLayout:
                    orientation: 'vertical'        
                    BoxLayout:
                        orientation: 'horizontal'        
                        size_hint: (1, None)
                        height: '10mm'
                        ToggleButton:
                            id:bVid
                            size: '10mm','10mm'
                            size_hint: (None, None)
                            text: '|>'
                            on_press: root.VideoPlayerButton ()
                            opacity: 0.5
                        Spinner:
                            text:'Camera ???'
                            values: ('854x480@25','1024x576@25', '1280x720@25','1920x1080@25','854x480@15','1024x576@15', '1280x720@15','1920x1080@15')
                            size_hint: (None, None)
                            size: '30mm','10mm'
                            id: bCam
                            on_text: print 'Camera:' + self.text
                            opacity: 0.5
                        Spinner:
                            text:'Sonar ???'
                            values: ('Failsafe 0.2','Failsafe 0.4', 'Failsafe off','Sonar off')
                            size_hint: (None, None)
                            size: '30mm','10mm'
                            id: bSon
                            on_text: print 'Sonar:' + self.text
                            opacity: 0.5

                    BoxLayout:
                        orientation: 'horizontal'        
                        size_hint: (1, None)
                        height: '30sp'
                        Label:
                            text: 'Head <>'
                            size: '80sp','30sp'
                            size_hint: (None, None)
                            id: servo2label
                            halign: 'right'
                            valign: 'middle'
                            font_size: '14sp'
                            text_size: self.size

                        Slider:
                            id: servo2
                            step: 2
                            size_hint: (1, None)
                            height: '30sp'
                            range: 50, 105
                            value: 90		        
                            on_value: root.SetServo2() 
                            orientation: 'horizontal'
                            pos_hint: {'center_x': 0.5, 'top':1}
                            background_color: (0, 0, 0, 1)
                    Label:
                        text: '--'
                        id: statslabel
                        font_size: '14sp'
                        size_hint: 1, .05
                        text_size: self.size
                        halign: 'right'
                    Joystick:
                        size_hint: 1, 1 
                        id: joy1			
                        border: [1, 1, 1, 1]
                        on_pos: root.TracksMove ()
                        on_touch_up: root.TracksStop ()


    TabbedPanelItem:
        text: 'Log'
        BoxLayout:
            orientation: 'vertical'
            TextInput:
                background_color: (1, 1, 1, .5)        
                size_hint: 1, .7
                readonly: True
                font_size: 16   
                id: log_box        
    TabbedPanelItem:
        text: 'Calibration'
        GridLayout:
            size_hint: 1, 1
            rows: 5
            cols: 2
            Label:
                text: 'Tracks move'
                size_hint: 1, 1
            Slider:
                id: cal_trackmove
                step: 1
                size_hint: 1, 1
                range: 1, 255
                value: 255
                orientation: 'horizontal'
            Label:
                text: 'Tracks rotate factor'
                size_hint: 1, 1
            Slider:
                id: cal_trackrotate
                step: 1
                size_hint: 1, 1
                range: 1, 100
                value: 100
                orientation: 'horizontal'
            Label:
                text: 'Dead zone'
                size_hint: 1, 1
            Slider:
                id: cal_trackdeadzone
                step: 1
                size_hint: 1, 1
                range: 1, 255
                value: 200
                orientation: 'horizontal'
                disabled: True
            TouchLiveSlider:
                size_hint: 1, 0.2
                index: 1
                min: 0 
                value: 50
                max: 100
                step: 1
            TouchLiveSlider:
                size_hint: 1, 0.2
                index: 1
                min: 0 
                value: 50
                max: 100
                step: 1
                color: (1, 0, 0, 1)
            TouchLiveSlider:
                size_hint: 1, 0.1
                index: 1
                min: 0 
                value: 50
                max: 100
                step: 1



            
<Joystick>:
    joycap:joycap
    coordslabel:coordslabel
    canvas:
        Color:
            rgba: 0, 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0, 1, 0, .1
        Rectangle:
            pos: self.x, self.center_y - (self.height*self.deadzone)
            size: self.width , (self.height*self.deadzone*2)
        Rectangle:
            pos: self.center_x - (self.width*self.deadzone), self.y
            size: self.width*0.1, self.height 
        Color:
            rgba: 1, 1, 1, .7
        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1


    Label:
        id: joycap
        text: '+'
        size: '10mm', '10mm'
    Label:
        id: coordslabel
        text: '--'
        x: self.parent.x 
        y: self.parent.y
        font_size: '14sp'
        height:'18sp'
        width:'150sp'
        halign: 'left'
        text_size: self.size

<TouchLiveSlider>:
    canvas:
        Clear
        Color:
            rgba: self.color
        Line:
            rectangle: self.x+3,self.y+3,self.width-3,self.height-3
            width: 2
        Color:
            rgba: self.color
        Rectangle:
            pos: self.x+7, self.y+7
            size: (self.width-11) * (self.value_normalized if self.orientation == 'horizontal' else 1), (self.height -  11) * (self.value_normalized if self.orientation == 'vertical' else 1)


""")

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

    def TracksStop (self):
        pilot.send ("TRACKS 0 0")

    def SetServo1 (self, smth=""): 
        pilot.send ("SERVO 1 %0d" % self.servo1.value)
#        self.servo1label.text = "Head ^%03dv" % self.servo1.value

    def SetServo2 (self, smth=""): 
        pilot.send ("SERVO 2 %0d" % self.servo2.value)
#        self.servo2label.text = "Head <%03d>" % self.servo2.value

    def VideoPlayerButton (self):
        if self.bVid.state == 'normal':
          self.log_box.text += "video stop \n"
          self.bVid.text = '|>'
          self.fpvideo.state = 'stop'
          self.fpvideo.opacity = 0          
        elif self.bVid.state == 'down':
          self.log_box.text += "video start \n"                    
          self.bVid.text = '||'
          self.fpvideo.state = 'play'
          self.fpvideo.opacity = 1          
        return True

    def logupdate(self, dt):
        while pilot.udpreader(): pass
        try: 
            self.label1.text = "Li-ion: %0.2fV\n +5: %0.2fV\n"  % (float(pilot.stats['A3'])*0.009774078,float(pilot.stats['A2'])*0.0096850)
            self.label1.text += "dT: %0.2fs.\nSonar: %0.2fM\n" % (pilot.statsdtime, float(pilot.stats['Son'])/1000)
            self.label1.text += "CPU BAT: {:d}% \n{:d}mA \nExt: {:d}mA \nState: {}".format(pilot.stats['cpu_bcap'],pilot.stats['cpu_bcur'],pilot.stats['cpu_accur'],pilot.stats['cpu_bstate']) 
            self.statslabel.text = "L: {:+.2f} R: {:+.2f}".format(pilot.stats['trackr'], pilot.stats['trackl'])
            self.servo1label.text = "Head ^%03dv" % int(pilot.stats['S1'])
            self.servo2label.text = "Head <%03d>" % int(pilot.stats['S2'])
#            self.servo1.value = int(pilot.stats['S1'])
#bad idea really, undefined behavior.

        except KeyError as e: self.statslabel.text = "not yet " + e.message
#        while len(pilot.udpinmsgs) > 0 :
#            try: self.log_box.text = pilot.udpinmsgs.pop(0) + "\n"
#            except UnicodeDecodeError: self.log_box.text += "[...]"
        
class Joystick(Widget):
#StencilView

    jx = 0.;
    jy = 0.;
    deadzone = NumericProperty(.05); 
    pos = ListProperty([0, 0])
    def on_height(self, pos, smth='123'):
        self.resetcap(); 
    def on_width(self, pos, smth='123'):
        self.resetcap(); 

    def on_touch_down(self, touch):
      if self.collide_point(touch.x,touch.y):
          touch.grab(self)
          ud = touch.ud
          ud['group'] = g = str(touch.uid)
          with self.canvas:
            ud['color'] = Color (0.7,0.7,0.7,0.5, group=g)
            ud['lines'] = (
              Rectangle(pos=(touch.x, self.y), size=(1, self.height), group=g),
              Rectangle(pos=(self.x, touch.y), size=(self.width, 1), group=g)
              )
          self.movecap(touch)
          return True

    def on_touch_move(self, touch):
        if touch.grab_current == self:
          if touch.x > self.width + self.x: touch.x = self.width + self.x
          if touch.x < self.x: touch.x = self.x
          if touch.y > self.height + self.y: touch.y = self.height + self.y
          if touch.y < self.y: touch.y = self.y
          ud = touch.ud
          ud['lines'][0].pos = touch.x, self.y
          ud['lines'][1].pos = self.x, touch.y
          self.movecap(touch);
          return True

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            self.resetcap();
            touch.ungrab(self)
            ud = touch.ud
            self.canvas.remove_group(ud['group'])
            return True


    def on_pos(self,joy,pos):
        pass

    def resetcap(self):
      self.joycap.center_x = self.center_x;
      self.joycap.center_y = self.center_y;
      self.jx = 0.;
      self.jy = 0.;
      self.coordslabel.text = "x:%0.3f y: %0.3f" % (self.jx ,self.jy) 
      self.pos = (self.jx ,self.jy)

    def movecap(self, touch):
      if touch.x > self.center_x - (self.width*self.deadzone) and touch.x < self.center_x + (self.width*self.deadzone):
        touch.x = self.center_x
      if touch.y > self.center_y - (self.height*self.deadzone) and touch.y < self.center_y + (self.height*self.deadzone):
        touch.y = self.center_y;
      self.joycap.center_x = touch.x;
      self.joycap.center_y = touch.y;
      self.jx = ((touch.x - self.x) - self.width/2)/self.width*2
      self.jy = ((touch.y - self.y) - self.height/2)/self.height*2

      self.coordslabel.text = "x:%0.3f y: %0.3f" % (self.jx ,self.jy) 
      self.pos = (self.jx ,self.jy)

class TouchLiveSlider(Slider):
    '''Custom slider class for having his index and custom graphics defined in
    the .kv
    '''
    index = NumericProperty(0)
    color = (82./255,217./255,87./255,1)        
    

class kPilotApp(App):   
    mainform = ObjectProperty()
    def build(self):
        self.mainform = MainTabs()
        pilot.init()
        Clock.schedule_interval(self.mainform.logupdate, .1)
#        Clock.schedule_interval(pilot.udpreader, .05)
        self.mainform.log_box.text = "Running client on Python " + sys.version + "\n"
        self.mainform.log_box.text += "K-9 Greets the master :-)\n"
        return self.mainform
    def on_pause(self):
      # Here you can save data if needed
      # called on android background or standby
        Config.set('graphics', 'height', 'Window.height')
        Config.set('graphics', 'width', 'Window.width')        
        Config.write()
        return True

    def on_stop(self):
        Config.set('graphics', 'height', Window.height)
        Config.set('graphics', 'width', Window.width)        
        Config.write()
        return True

if __name__ == '__main__':
    kPilotApp().run()