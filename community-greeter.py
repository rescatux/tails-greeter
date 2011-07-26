#!/usr/bin/python
#
# Copyright 2011 Max <govnototalitarizm@gmail.com>
# Copyright 2011 Martin Owens
#
# This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>
#
"""
GDM greeter for TAILS project using gtk
"""

import logging, logging.config
import gtk, sys

from gtk import gdk

def print_log_record_on_error(func):
    """Wrapper to determine failed logging instance"""
    def wrap(self, *args, **kwargs):
        """internal logging wrapper"""
        try:
            return func(self, *args, **kwargs)
        except:
            print >> sys.stderr, "Failed log message=%r with args=%r " % (getattr(self, 'msg', '?'), getattr(self, 'args', '?'))
            raise
    return wrap

logging.config.fileConfig('tails-logging.conf')
logging.LogRecord.getMessage = print_log_record_on_error(logging.LogRecord.getMessage)

from gtkme import GtkApp
from subprocess import Popen, PIPE
from GdmGreeter.services import GdmGreeter
from GdmGreeter.language import Translatable, ln_cc
from GdmGreeter.langselect import LangselectWindow
from GdmGreeter.layout import LayoutWindow
from GdmGreeter.autologin import AutologinWindow, LPASSWORD, LUSER
from GdmGreeter import GLADE_DIR, __appname__

def translate_window(window, language):
    """translate window to given language"""
    logging.debug("Translating %s to %s", window.name, ln_cc(language).split('_')[0])
    window.translate_to(ln_cc(language).split('_')[0])

class CommunityGreeterApp(GtkApp, GdmGreeter):
    """Custom greeter instance"""
    app_name  = __appname__
    glade_dir = GLADE_DIR
    lgen = None
    windows   = [ AutologinWindow, LangselectWindow, LayoutWindow ]

    def __init__(self, *args, **kwargs):
        GtkApp.__init__(self, *args, **kwargs)
        GdmGreeter.__init__(self)
        self.scr = gdk.display_get_default().get_screen(self.display.number)
        self.lang = None
        self.login = None
        self.language = 'en_GB.UTF-8'
        self.session = None
        self.forced = False
        self.layout = None
        self.layout_widget = None
        self.postponed = False
        self.postponed_text = None
        self.ready = False
        self.translated = False

    def load_window(self, *args, **kwargs):
        """When loading a window, also translate it"""
        window = GtkApp.load_window(self, *args, **kwargs)
        if isinstance(window, Translatable) and self.language:
            if '_' in self.language:
                lang = self.language.split('_')[0]
                logging.debug("Translating %s to %s", window.name, lang)
                window.translate_to(lang)
            else:
                translate_window(window, self.language)
        return window

    def translate_to(self, lang):
        """Translate all windows to target language"""
        if self.ready:
            self.language = lang
        for window in self._loaded.values():
            if isinstance(window, Translatable):
                translate_window(window, lang)

    def Ready(self):
        """Sever is ready"""
        if not self.lang:
            self.lang = self.load_window('langselect')
        else:
            self.login.window.set_sensitive(True)
            self.login.show_user('')
        GdmGreeter.Ready(self)
        self.ready = True
        logging.warn("server is ready.")

    def SwitchVisibility(self):
        """Switch language and login windows visibility"""
        if not self.layout_widget:
            logging.debug('loading layout')
            self.layout_widget = self.load_window('layout')
            self.lgen = Popen(["tails-locale-gen", ln_cc(self.language)], stdout = PIPE)
            logging.debug('spawned locale generator with %s pid', self.lgen.pid)
            self.lang.window.destroy()
        elif not self.login:
            logging.debug('loading login')
            self.login = self.load_window('autologin', service = self.obj)
            self.layout_widget.destroy()
            if self.login:
                if self.postponed:
                    self.login.show_user(self.postponed_text)

    def SelectLanguage(self, lang):
        """The user wants to change languages"""
        # Translate all windows in the login screen
        self.translate_to(lang)
        # Apply chosen language
        GdmGreeter.SelectLanguage(self, lang)

    def DefaultLanguageNameChanged(self, lang):
        """default language name changed"""
        logging.debug('DefaultLanguageNameChanged to %s', lang)
        self.language = lang

    def DefaultLayoutNameChanged(self, layout):
        """default layout name changed"""
        logging.debug('DefaultLayoutNameChanged to %s', layout)
        self.layout = str(layout)

    def DefaultSessionNameChanged(self, session):
        """default session name changed"""
        logging.debug('DefaultSessionNameChanged to %s', session)
        self.session = str(session)

    def InfoQuery(self, text):
        """Server wants to ask the user for something"""
        if self.forced:
    	    self.obj.AnswerQuery(LUSER)
        elif self.login:
            self.login.show_user(text)
        else:
            self.postponed = True
            self.postponed_text = text

    def SecretInfoQuery(self, text):
        """Server wants to ask for some secrate info"""
        if self.forced:
    	    self.obj.AnswerQuery(LPASSWORD)
    	else:
    	    self.login.show_pass(text)

    def ForcedLogin(self):
        """Immediate login"""
        logging.debug('forced login: skipping all widgets...')
        self.forced = True
        if self.postponed:
    	    self.obj.AnswerQuery(LUSER)

    def FinishProcess(self):
        """We're done, quit gtk app"""
        if self.lgen:
            (lout, lerr) = self.lgen.communicate()
            logging.debug('locale generation finished, return code %s', self.lgen.returncode)
        logging.info("Finished.")
        gtk.main_quit()

if __name__ == "__main__":
    logging.info("Started.")
    app = CommunityGreeterApp()
    gtk.main()

