#
# IBus-BoGo - The Vietnamese IME for IBus
#
# Copyright (c) 2012- Long T. Dam <longdt90@gmail.com>,
#                     Trung Ngo <ndtrung4419@gmail.com>
#
# This file is part of IBus-BoGo Project
# IBus-BoGo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IBus-BoGo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IBus-BoGo.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import GObject
from gi.repository import IBus
from gi.repository import Pango
import sys
import getopt
import time
import BoGo

# syntactic sugar
keysyms = IBus
modifier = IBus.ModifierType

import time
time_delay = 0.01

CHARSET_UTF8 = 0
CHARSET_TCVN3 = 1

class Engine(IBus.Engine):
    __gtype_name__ = 'EngineBoGo'

    def __init__(self):
        super(Engine, self).__init__()
        self.__charset_list = ["UTF8","TCVN3"]
        self.__init_props()
        self.commit_result = self.commit_utf8
        self.reset_engine()
        print "You are running BoGo IBus Engine"


    # The "do_" part is PyGObject's way of overriding base's functions
    def do_process_key_event(self, keyval, keycode, state):
        """Implement IBus.Engine's process_key_event default signal handler.
        
        Args:
            keyval - The keycode, transformed through a keymap, stays the
                same for every keyboard
            keycode - Keyboard-dependant key code
            state - The state of modifier keys like Shift, Control, etc.
        Return:
            True - if successfully process the keyevent
            False - otherwise
            
        This function gets called whenever a key is pressed.
        """
        # ignore key release events
        is_press = ((state & IBus.ModifierType.RELEASE_MASK) == 0)
        if not is_press:
            return False

        if self.is_character(keyval):
            if state & (modifier.CONTROL_MASK | modifier.MOD1_MASK) == 0:
                print "Character entered: " + chr(keyval)
                self.isFakeBackspace = True

                self.old_string = self.new_string
                self.new_string = self.process_key(keyval)
                print "Old string:", self.old_string
                print "New string:", self.new_string
                self.n_backspace, self.string_to_commit = \
                  self.get_nbackspace_and_string_to_commit()
                print "Number of fake backspace: ", self.n_backspace
                print "String to commit:", self.string_to_commit
                self.commit_fake_backspace(self.n_backspace)
                time.sleep(time_delay)
                self.commit_result()
                return True

        if self.string_to_commit:
            if keyval == keysyms.Return or keyval == keysyms.Escape or\
               keyval == keysyms.space:
                self.reset_engine()
                return False

            if keyval == keysyms.BackSpace:
                self.remove_last_char()
                return False

        self.reset_engine()
        return False

    def reset_engine(self):
        self.string_to_commit = u""
        self.new_string = u""
        self.old_string = u""
        self.n_backspace = 0

    def commit_utf8(self):
        self.commit_text(IBus.Text.new_from_string(self.string_to_commit))
    def commit_tcvn3(self):
        tcvn3_string = BoGo.utf8_to_tcvn3(self.string_to_commit)
        self.commit_text(IBus.Text.new_from_string(tcvn3_string))

    def process_key(self, keyval):
        uni_keyval = unichr(keyval)
        if self.old_string:
            print BoGo.process_key(self.old_string, uni_keyval)
            return BoGo.process_key(self.old_string, uni_keyval)
        else:
            #self.new_string = uni_keyval
            return uni_keyval

    def remove_last_char(self):
        self.new_string = self.new_string[:-1]

    def commit_fake_backspace(self,n_backspace):
        for i in range(n_backspace):
            self.forward_key_event(keysyms.BackSpace, 14, 0)

    def get_nbackspace_and_string_to_commit(self):
        if (self.old_string):
            length = len(self.old_string)
            for i in range(length):
                if self.old_string[i] != self.new_string[i]:
                    _nbackspace = length - i
                    _stringtocommit = self.new_string[i:]
                    return _nbackspace, _stringtocommit
            return 0, self.new_string[length:]
        else:
             return 0, self.new_string
        # Classical method:
        # return len(self.old_string) + 1, self.new_string

    def is_character(self, keyval):
        if keyval in xrange(33,126):
            return True
        else:
            return False

    def do_focus_in(self):
        """Implements IBus.Engine's forcus_in's default signal handler.
        
        Called when the input client widget gets focus.
        """
        self.register_properties(self.__prop_list)

    def do_focus_out(self):
        """Implements IBus.Engine's forcus_out's default signal handler.
        
        Called when the input client widget loses focus.
        """
        self.reset_engine()

    def do_property_activate(self, prop_name, state):
        if state == IBus.PropState.CHECKED:
            if prop_name == None:
                return
            elif prop_name == "UTF8":
                self.commit_result = self.commit_utf8
                print "UTF8"
            elif prop_name == "TCVN3":
                self.commit_result = self.commit_tcvn3
                print "TCVN3"

    def __init_charset_prop_menu(self):
        charset_prop_list = IBus.PropList()
        for charset in self.__charset_list:
            charset_prop_list.append(
                IBus.Property(key = charset,
                              prop_type = IBus.PropType.RADIO,
                              label = IBus.Text.new_from_string(charset),
                              icon = '',
                              tooltip = IBus.Text.new_from_string(charset),
                              sensitive = True,
                              visible = True,
                              state = IBus.PropState.UNCHECKED,
                              sub_props = None))

        charset_prop_menu = IBus.Property(
            key = "charset",
            prop_type = IBus.PropType.MENU,
            label = IBus.Text.new_from_string("Charset"),
            icon = "gtk-preferences",
            tooltip = IBus.Text.new_from_string("Choose charset"),
            sensitive = True,
            visible = True,
            state = IBus.PropState.UNCHECKED,
            sub_props = charset_prop_list)
        return charset_prop_menu

    def __init_props(self):
        self.__prop_list = IBus.PropList()
        self.__charset_prop_menu = self.__init_charset_prop_menu()
        self.__prop_list.append(self.__charset_prop_menu)
