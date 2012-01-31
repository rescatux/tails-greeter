#!/usr/bin/python
#
# Copyright 2011 Max <govnototalitarizm@gmail.com>
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
Greeter program for GDM using gtk (nothing else works)
"""

import logging, gtk, gettext, os
_ = gettext.gettext
import GdmGreeter
from GdmGreeter.language import TranslatableWindow
# default Tails credentials
LPASSWORD = 'live'
LUSER = 'amnesia'

class AutologinWindow(TranslatableWindow):
    """Display a pre-login window"""
    name = 'autologin'
    primary = False
    auth_password = None

    def __init__(self, service):
        self.service = service

        builder = gtk.Builder()
        builder.set_translation_domain(GdmGreeter.__appname__)
        builder.add_from_file(os.path.join(GdmGreeter.GLADE_DIR, "autologin.glade"))
        builder.connect_signals(self)
        self.entry_password = builder.get_object("password_entry_field")
        self.entry_password2 = builder.get_object("password_entry_field2")
        self.label_header = builder.get_object("header_label")

        TranslatableWindow.__init__(self, builder.get_object("autologin"))

        self.entry_password.set_visibility(False)
        self.entry_password2.set_visibility(False)

    def get_pass(self, widget = None):
        """obtain password (button click handler)"""
        self.auth_password = self.entry_password.get_text()
        test = self.entry_password2.get_text()
        if test == self.auth_password:
            self.service.AnswerQuery(LPASSWORD)
        else:
            self.label_header.set_text(_('Password mismatch!'))

    def key_press_event_cb(self, widget, event=None):
        """Handle key press"""
        if event:
            if event.keyval == gtk.keysyms.Return:            
                self.get_pass(widget)

    def proceed_login(self):
        """Autologin attempt"""
        logging.debug('BeginAutoLogin attempt')
        self.service.BeginAutoLogin(LUSER)

    def show_user(self, text):
        """dummy function"""
        logging.debug('show user called with %s', text)
        self.service.AnswerQuery(LUSER)

    def show_pass(self, text):
        """dummy function"""
        logging.debug('show pass called with %s', text)
