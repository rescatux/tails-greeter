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
from GdmGreeter.language import Translatable, LDICT
from GdmGreeter.langselect import LangselectWindow
from GdmGreeter.autologin import AutologinWindow
from GdmGreeter import GLADE_DIR, __appname__

class CommunityGreeterApp(GtkApp, GdmGreeter):
    """Custom greeter instance"""
    app_name  = __appname__
    glade_dir = GLADE_DIR
    lgen = None
    windows   = [ AutologinWindow, LangselectWindow ]

    def __init__(self, *args, **kwargs):
        GtkApp.__init__(self, *args, **kwargs)
        GdmGreeter.__init__(self)
        self.scr = gdk.display_get_default().get_screen(self.display.number)
        self.lang = None
        self.login = None
        self.user = None
        self.language = 'en_GB.UTF-8'
        self.session = None
        self.layout = None
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
                logging.debug("Translating %s to %s", window.name, LDICT[unicode(self.language)].split('_')[0])
                window.translate_to(LDICT[unicode(self.language)].split('_')[0])
        return window

    def translate_to(self, lang):
        """Translate all windows to target language"""
        if not self.translated and self.ready:
            self.language = lang
            self.translated = True
        for window in self._loaded.values():
            if isinstance(window, Translatable):
                logging.debug("I18n window %s to %s", window.name, LDICT[unicode(self.language)].split('_')[0])
                window.translate_to(LDICT[unicode(self.language)].split('_')[0])

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
        if not self.login:
            self.login = self.load_window('autologin', service = self.obj)
        self.lgen = Popen(["tails-locale-gen", LDICT[unicode(self.language)]], stdout = PIPE)
        logging.debug('spawned locale generator with %s pid', self.lgen.pid)
        self.lang.window.destroy()
        if self.postponed:
            self.login.show_user(self.postponed_text)

    def SelectedUserChanged(self, username):
        """legacy user selection change handler"""

    def SelectLanguage(self, lang):
        """The user wants to change languages"""
        # Translate all windows in the login screen
        self.translate_to(lang)
        # Make sure the session is set correctly.
        if self.user:
            GdmGreeter.SelectLanguage(self, lang)

    def DefaultLanguageNameChanged(self, lang):
        """default language name changed"""
        self.language = lang

    def DefaultLayoutNameChanged(self, layout):
        """default layout name changed"""
        self.layout = str(layout)

    def DefaultSessionNameChanged(self, session):
        """default session name changed"""
        self.session = str(session)

    def InfoQuery(self, text):
        """Server wants to ask the user for something"""
        if self.login:
            self.login.show_user(text)
        else:
            self.postponed = True
            self.postponed_text = text

    def SecretInfoQuery(self, text):
        """Server wants to ask for some secrate info"""
        self.login.show_pass(text)

    def FinishProcess(self):
        """We're done, quit gtk app"""
        (lout, lerr) = self.lgen.communicate()
        logging.debug('locale generation finished, return code %s', self.lgen.returncode)
        logging.info("Finished.")
        gtk.main_quit()

if __name__ == "__main__":
    logging.info("Started.")
    app = CommunityGreeterApp()
    gtk.main()

