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

import logging, gtk

from GdmGreeter.language import TranslatableWindow

class AutologinWindow(TranslatableWindow):
    """Display a pre-login window"""
    name = 'autologin'
    primary = False
    auth_password = None
# default TAILS credentials
    logon_password = 'amnesia'
    user = 'amnesia'

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service')
        TranslatableWindow.__init__(self, *args, **kwargs)

    def get_pass(self, widget = None):
        """Returns password"""
        widget = self.widget('password_entry_field')
        auth_password = widget.get_text()
        self.service.AnswerQuery(self.logon_password)
        return auth_password

    def key_press_event_cb(self, widget, event=None):
        """Handle key press"""
        if event and event.keyval == gtk.keysyms.Return:
            self.get_pass(widget)

    def proceed_login(self):
        """Autologin attempt"""
        logging.debug('BeginAutoLogin attempt')
        self.service.BeginAutoLogin(self.user)

    def show_user(self, text):
        """dummy function"""
        logging.debug('called to show user %s', text)
        self.service.AnswerQuery(self.user)

    def show_pass(self, text):
        """dummy function"""
        logging.debug('called to show user %s', text)
