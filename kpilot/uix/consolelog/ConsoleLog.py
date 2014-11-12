from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import  NumericProperty, ListProperty, ObjectProperty
from kivy.lang import Builder
from kivy.graphics import Color, Ellipse, Line , Rectangle, Point, GraphicException
from kivy.uix.boxlayout import BoxLayout

import io
import time


Builder.load_file("uix\consolelog\consolelog.kv")
class LogRecord (Label):
    def __init__(self, *args, **kwargs):
        self.createtime = time.time()
        super(LogRecord, self).__init__(**kwargs)
    pass

class ConsoleLog(BoxLayout):

    def __init__(self, *args, **kwargs):
        self.records = []
        self.streampos = 0
        self.maxrec = 40
        self.decaytime = 60
        self.orientation = 'vertical'
#        Clock.schedule_interval(self.refresh, 5)
        super(ConsoleLog, self).__init__(**kwargs)
    
    def AddRecord (self, record):
        line = record.strip("\n")
        if line.find('DEBUG') > 0:
           color = "AAAAAA"
        elif line.find('INFO') > 0:
           color = "AAFFAA"
        elif line.find('WARN') > 0:
           color = "EEEE99"
        elif line.find('ERROR') > 0:
           color = "FF3300"
        elif line.find('CRIT') > 0:
           color = "FF3300"
        else:
           color = "FFFFFF"
        line = u"[color={}]{}[/color]".format(color,line)
        label = LogRecord(text=line)
        self.records.append(label)
        self.add_widget(label)
        return True;

    def initstream (self):
        self.stream = io.StringIO()
        self.streampos = 0
        Clock.schedule_interval(self.refresh, 0)
        Clock.schedule_interval(self.checkdecay, 0.5)
        return self.stream
   
    def checkdecay (self, *args):
        now = time.time()
        for record in self.records:
            age = now - record.createtime
            if self.opacity != 0 and age > self.decaytime :
                opacity = 1 - (age - self.decaytime)/100
                record.opacity = opacity
                if record.opacity < 0.05: self.remove_widget(record)
                

    def refresh (self, *args):
        self.stream.seek(self.streampos)
        record = self.stream.readline()
        if record != '' : 
            self.AddRecord (record)
            while len(self.records) > self.maxrec:
               self.remove_widget(self.records.pop(0))

        self.streampos = self.stream.tell()

