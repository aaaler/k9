from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder
from kivy.clock import Clock
from joystick import Joystick
import sys
import pilot
import time



Builder.load_string("""

<MainTabs>:
    size_hint: 1, 1
    pos_hint: {'center_x': .5, 'center_y': .5}
    do_default_tab: False
    log_box: log_box
    speed: speed
    rot_speed: rot_speed
    servo1: servo1
    servo2: servo2
    servo1label: servo1label
    servo2label: servo2label
    statslabel: statslabel
    label1:label1
    label2:label2

    BoxLayout:
        orientation: 'vertical'
        BoxLayout:            
            BoxLayout:
                size_hint: .2, 1
                orientation: 'vertical'        
                Label:
                    text: 'Head ^v'
                    size_hint: .2, .05
                    pos_hint: {'center_x': 0.5, 'top':1}
                
                Slider:
                    id: servo1
                    step: 2
                    size_hint: .5, 1
                    range: 1, 180
                    value: 90
                    on_value: root.SetServo1()
                    orientation: 'vertical'
                    pos_hint: {'center_x': 0.5}

                Label:
                    id: servo1label
                    text: '00'
                    size_hint: .2, .05
                    pos_hint: {'center_x': 0.5, 'top':1}
            

            BoxLayout:
                orientation: 'vertical'        
                Label:
                    text: 'Head <>'
                    size_hint: .8, .07
                    pos_hint: {'center_x': 0.5,'y':1}
                Slider:
                    id: servo2
                    step: 2
                    size_hint: .7, .07
                    range: 50, 105
                    value: 90
                    on_value: root.SetServo2() 
                    orientation: 'horizontal'
                    pos_hint: {'center_x': 0.5, 'top':1}
                Label:
                    text: '00'
                    id: servo2label
                    size_hint: .8, .05
                    pos_hint: {'center_x': 0.5,'y':1}
                Label:
                    text: '--'
                    id: statslabel
                    font_size: 16
                    size_hint: .8, .05
                    pos_hint: {'center_x': 0.5,'y':1}
                    
                TextInput:
                    size_hint: 1, .7
                    readonly: True
                    font_size: 16   
                    id: log_box        
		    

        GridLayout:
            size_hint: 1, .3
            rows: 3
            cols: 3
            Label:
                text: ''
                id: label1
                size_hint: .2, .2
            Button:
                text: 'FWD'
                size_hint: .2, .2
                on_press: root.TrackButtonDown("FWD")
                on_release: root.TrackButtonUp("FWD")
            Slider:
                id: speed
                step: 2
                size_hint: .2, .2
                range: 150, 255
                value: 190
                on_value: root.SetSpeeds ()
            Button:
                text: '<<'
                size_hint: .2, .2
                on_press: root.TrackButtonDown("LEFT")
                on_release: root.TrackButtonUp("LEFT")
            Button:
                text: 'STOP'
                on_press: root.TrackButtonDown("STOP")
                size_hint: .2, .2
            Button:
                text: '>>'
                size_hint: .2, .2
                on_press: root.TrackButtonDown("RIGHT")
                on_release: root.TrackButtonUp("RIGHT")
            
            Label:
                text: ''
                id:label2
                size_hint: .2, .2
            Button:
                text: 'REV'
                size_hint: .2, .2
                on_press: root.TrackButtonDown("REV")
                on_release: root.TrackButtonUp("REV")
          
            Slider:
                id: rot_speed
                step: 2
                size_hint: .2, .2
                range: 150, 255
                value: 190
                on_value: root.SetSpeeds ()


            

""")

class MainTabs(TabbedPanel):
    log_box = ObjectProperty()
    speed = ObjectProperty()
    rot_speed = ObjectProperty()
    statslabel = ObjectProperty()
    label1 = ObjectProperty()
    label2 = ObjectProperty()
    
    def TrackButtonDown (self, cmd): 
        pilot.direction = cmd
        self.SetSpeeds (self)    

    def SetSpeeds (self, smth=""): 
        pilot.speed = int (self.speed.value)
        pilot.rotspeed = int (self.rot_speed.value)
    
    def TrackButtonUp (self, cmd):
        if pilot.direction == cmd : 
            pilot.send ("STOP")
            pilot.direction = "";
    

    def SetServo1 (self, smth=""): 
        pilot.send ("SERVO 1 " + str(self.servo1.value))
        self.servo1label.text = str(self.servo1.value)

    def SetServo2 (self, smth=""): 
        pilot.send ("SERVO 2 " + str(self.servo2.value))
        self.servo2label.text = str(self.servo2.value)

                    

        

    def logupdate(self, dt):
        while pilot.udpreader(): pass
        try: 
            self.label1.text = "Li-ion: " + "%0.2f" % (float(pilot.stats['A3'])*0.0106535) + "V"
            self.label2.text = " +5: " + "%0.2f" % (float(pilot.stats['A2'])*0.0096850) + "V"
            self.statslabel.text = "S1:" + str(pilot.stats['S1']) + " S2:" + str(pilot.stats['S2']) + " dT:" + "%0.4f" % pilot.statsdtime + " Sonar: " + str(pilot.stats['Son'])
        except KeyError: self.statslabel.text = "not yet"
        while len(pilot.udpinmsgs) > 0 :
            try: self.log_box.text = pilot.udpinmsgs.pop(0) + "\n"
            except UnicodeDecodeError: self.log_box.text += "[...]"
        

        

class kPilotApp(App):   
    def build(self):
        mainform = MainTabs()
        pilot.init()
        Clock.schedule_interval(mainform.logupdate, .1)
#        Clock.schedule_interval(pilot.udpreader, .05)
        mainform.log_box.text = "Running client on Python " + sys.version + "\n"
        mainform.log_box.text += "K-9 Greets the master :-)\n"
        return mainform

if __name__ == '__main__':
    kPilotApp().run()