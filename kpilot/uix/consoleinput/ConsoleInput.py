from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder

#uilder.load_file(r"uix\consoleinput\consoleinput.kv")

class ConsoleInput(TextInput):
    pass
    def on_focus(self, value, *kwargs):
        app = App.get_running_app()
        if self.focus:
            self.opacity = 0.7
#            Clock.schedule_once(lambda dt: self.select_all())
        else:
            self.opacity = 0.2
#            self.text = ">>>"
            Clock.schedule_once(lambda dt: App.get_running_app()._keyboard_init())
        super(ConsoleInput,self).on_focus(value, *kwargs)

    def _key_down(self, key, repeat=False):
        return super(ConsoleInput,self)._key_down(key, repeat)
        #4 history processing
