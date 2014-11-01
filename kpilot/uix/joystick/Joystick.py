from kivy.uix.widget import Widget
from kivy.properties import  NumericProperty, ListProperty
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line , Rectangle, Point, GraphicException
from contextlib import contextmanager

import pygame
import sys, os



Builder.load_file("uix\joystick\joystick.kv")

class Joystick(Widget):
#StencilView?

    jx = 0.;
    jy = 0.;
    deadzone = NumericProperty(.05); 
    pos = ListProperty([0, 0])

    def __init__(self, *args, **kwargs):
        self.hwx = 0.
        self.hwy = 0.

        pass

        super(Joystick, self).__init__(**kwargs)

    def hwjoystick_refresh(self, *args):
        pygame.event.pump()
        newhwx = self.hwjoystick.get_axis(0)
        newhwy = -self.hwjoystick.get_axis(1)
        if newhwx != self.hwx or newhwy != self.hwy:
            self.hwx = newhwx
            self.hwy = newhwy

            self.joycap.center_x = self.x+(self.width*((self.hwx + 1)/2))
            self.joycap.center_y = self.y+(self.height*((self.hwy + 1)/2))
            self.jx = self.hwx
            self.jy = self.hwy
            if abs(self.hwx) < self.deadzone:
              self.jx = 0
            if abs(self.hwy) < self.deadzone:
              self.jy = 0
            self.coordslabel.text = "x:%0.3f y: %0.3f" % (self.hwx ,self.hwy) 
            self.pos = (self.jx ,self.jy)
        pass

    def hwjoystick_init(self,hwjoystick):
        self.hwjoystick = hwjoystick
        Clock.schedule_interval(self.hwjoystick_refresh, 0.01)        
        pass
    def hwjoystick_stop (self):
        Clock.unschedule(self.hwjoystick_refresh)
        self.hwjoystick = False
    def on_height(self, pos, *args):
        self.resetcap(); 
    def on_width(self, pos, *args):
        self.resetcap(); 
    def on_pos(self, pos, *args):
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

