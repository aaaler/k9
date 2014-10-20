from kivy.properties import  NumericProperty, ListProperty, BooleanProperty
from kivy.uix.slider import Slider
from kivy.lang import Builder


Builder.load_file(r"uix\fancyslider\fancyslider.kv")


class FancySlider(Slider):
    '''Custom slider class for custom graphics defined in
    the .kv
    '''

    color = (82./255,217./255,87./255,0.5)
    filled = BooleanProperty (True)
    borderwidth = NumericProperty(1.5)
