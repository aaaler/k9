from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder

#uilder.load_file(r"uix\consoleinput\consoleinput.kv")

class ConsoleInput(TextInput):
    def __init__(self, **kwargs):
        self._history = [];
        self._history_counter = 0;
        super(ConsoleInput,self).__init__(**kwargs)

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
        if key[2] == 'cursor_up': 
            if self.text != '' and self._history_counter == 0: self._history.append(self.text)
            his_len = len(self._history)
            if his_len > 0:
                self._history_counter -= 1
                if self._history_counter < -his_len : self._history_counter = -his_len
                self.text = self._history[self._history_counter]

        if key[2] == 'cursor_down': 
            if self.text != '' and self._history_counter == 0: self._history.append(self.text)
            his_len = len(self._history)
            if his_len > 0:
                self._history_counter += 1
                if self._history_counter >= 0  : 
                    self._history_counter = 0
                    self.text = ''
                else:
                    self.text = self._history[self._history_counter]


        return super(ConsoleInput,self)._key_down(key, repeat)

    def on_text_validate(self, **kwargs):
        self._history_counter = 0;
        if self.text != '' :
            self._history.append(self.text)
            self.text = '' 
        return super(ConsoleInput,self).on_text_validate(**kwargs)