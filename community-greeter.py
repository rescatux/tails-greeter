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
import tailsgreeter.gdmclient

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

import tailsgreeter.config
import tailsgreeter.rootaccess
import tailsgreeter.camouflage
import tailsgreeter.persistence

from tailsgreeter.language import TranslatableWindow
from tailsgreeter.langpanel import LangPanel
from tailsgreeter.persistencewindow import PersistenceWindow
from tailsgreeter.optionswindow import OptionsWindow
from tailsgreeter import GLADE_DIR, __appname__

class CommunityGreeterApp():
    """Tails greeter main controller

    This class is the greeter dbus service"""

    app_name  = __appname__
    glade_dir = GLADE_DIR

    def __init__(self, *args, **kwargs):
        self.language = 'en_US.UTF-8'
        self.session = None
        self.forced = False
        self.postponed = False
        self.postponed_text = None
        self._usermanager_ready = False
        self._gdmserver_ready = False
        self.ready = False
        self.translated = False
        self._loaded_windows = []
        
        # Load models
        self.gdmclient = tailsgreeter.gdmclient.GdmClient(
            server_ready_cb=self.server_ready,
            session_opened_cb = self.close_app
        )
        self.persistence = tailsgreeter.persistence.PersistenceSettings()
        self.localisationsettings = tailsgreeter.language.LocalisationSettings(
            usermanager_loaded_cb = self.usermanager_loaded
        )
        self.rootaccess = tailsgreeter.rootaccess.RootAccessSettings()
        self.camouflage = tailsgreeter.camouflage.CamouflageSettings()

        # Load views
        self.langpanel = self.load_window(LangPanel, self)
        self.persistencewindow = self.load_window(PersistenceWindow, self)
        self.optionswindow = self.load_window(OptionsWindow, self)

	logging.debug("loaded windows: %s" % self._loaded_windows)
        
    def load_window(self, window_class, *args, **kwargs):
        """When loading a window, also translate it"""
        logging.debug("loading window %s" % window_class)
        window = window_class(*args, **kwargs)
        self._loaded_windows.append(window)
        if isinstance(window, TranslatableWindow) and self.language:
            logging.debug("found translatable window")
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
        self.gdmclient.do_login(tailsgreeter.config.LUSER)

    def server_ready(self):
        """Server is ready"""
        logging.debug("Entering server_ready")
        self._gdmserver_ready = True
        self.localisationsettings.set_layout('us')
        self.maybe_show_ui()

    def usermanager_loaded(self):
        """UserManager is ready"""
        logging.debug("Entering usermanager_loaded")
        self._usermanager_ready = True
        self.localisationsettings.set_locale('en_US')
        self.maybe_show_ui()

    def maybe_show_ui(self):
        """Show UI if server and usermanager are both ready"""
        logging.debug("Entering maybe_show_ui")
        if self._gdmserver_ready and self._usermanager_ready:
            self.ready = True
            logging.info("tails-greeter is ready.")
            self.langpanel.window.show()
            self.persistencewindow.window.show()
        else:
            logging.debug("Something is not ready; not showing UI yet")

    def close_app(self):
        """We're done, quit gtk app"""
        logging.info("Finished.")
        Gtk.main_quit()

if __name__ == "__main__":
    logging.info("Started.")
    app = CommunityGreeterApp()
    Gtk.main()

