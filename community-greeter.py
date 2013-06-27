#!/usr/bin/python
#
# Copyright 2012-2013 Tails developers <tails@boum.org>
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
GDM greeter for Tails project using gtk
"""

import logging, logging.config
from gi.repository import Gtk
import sys, os

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

from pipes import quote

import GdmGreeter.config
import GdmGreeter.rootaccess
import GdmGreeter.camouflage
import GdmGreeter.persistence

from GdmGreeter.services import GdmGreeterService
from GdmGreeter.language import TranslatableWindow
from GdmGreeter.langpanel import LangPanel
from GdmGreeter.persistencewindow import PersistenceWindow
from GdmGreeter.optionswindow import OptionsWindow
from GdmGreeter import GLADE_DIR, __appname__

class CommunityGreeterApp(GdmGreeterService):
    """Tails greeter main controller

    This class is the greeter dbus service"""

    app_name  = __appname__
    glade_dir = GLADE_DIR

    def __init__(self, *args, **kwargs):
        GdmGreeterService.__init__(self)
        self.language = 'en_US.UTF-8'
        self.session = None
        self.forced = False
        self.layout = None
        self.postponed = False
        self.postponed_text = None
        self.ready = False
        self.translated = False
        self.persistence = GdmGreeter.persistence.PersistenceSettings()
        self._loaded_windows = []
        self.localisationsettings = GdmGreeter.language.LocalisationSettings(self)
        self.langpanel = self.load_window(LangPanel, self)
        self.persistencewindow = self.load_window(PersistenceWindow, self)
        self.optionswindow = self.load_window(OptionsWindow, self)
        self.rootaccess = GdmGreeter.rootaccess.RootAccessSettings()
        self.camouflage = GdmGreeter.camouflage.CamouflageSettings()

    def load_window(self, window_class, *args, **kwargs):
        """When loading a window, also translate it"""
        window = window_class(*args, **kwargs)
        self._loaded_windows.append(window)
        if isinstance(window, TranslatableWindow) and self.language:
            window.translate_to(self.language.split('_')[0])
        return window

    def translate_to(self, lang):
        """Translate all windows to target language"""
        logging.debug("translating to %s" % lang)
        if self.ready:
            self.language = lang
        for window in self._loaded_windows:
            if isinstance(window, TranslatableWindow):
                logging.debug("translating %s to %s" % (window, lang))
                window.translate_to(lang)

    def login(self):
        """Login GDM to the server"""
        # XXX: check that we already sent the username?
        self.obj.AnswerQuery(GdmGreeter.config.LPASSWORD)

    def Ready(self):
        """Server is ready"""
        self.langpanel.window.show()
        self.persistencewindow.window.show()
        GdmGreeterService.Ready(self)
        self.ready = True
        logging.warn("greeter is ready.")

    def SelectLanguage(self, lang):
        """The user wants to change languages"""
        # Translate all windows in the login screen
        self.translate_to(lang)
        # Apply chosen language
        GdmGreeterService.SelectLanguage(self, lang)

    def SelectLayout(self, layout):
        """The user wants to change layout"""
        # Apply chosen layout
        #GdmGreeterService.SelectLayout(self, layout)
        pass

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
        # XXX: I think that server actually wants username
        logging.debug("got infoquery: %s", text)
        self.obj.AnswerQuery(GdmGreeter.config.LUSER)

    def SecretInfoQuery(self, text):
        """Server wants to ask for some secret info"""
        # XXX
        if self.forced:
            self.obj.AnswerQuery(GdmGreeter.config.LPASSWORD)
        else:
            # XXX
            logging.debug('got SecretInfoQuery: %s', text)

    def ForcedLogin(self):
        """Immediate login"""
        # XXX
        logging.debug('forced login: skipping all widgets...')
        self.forced = True
        self.obj.SelectLanguage('en_US.UTF-8')
        if self.postponed:
            self.obj.AnswerQuery(GdmGreeter.config.LUSER)

    def FinishProcess(self):
        """We're done, quit gtk app"""
        logging.info("Finished.")
        Gtk.main_quit()

if __name__ == "__main__":
    logging.info("Started.")
    app = CommunityGreeterApp()
    Gtk.main()

