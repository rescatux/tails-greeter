#!/usr/bin/python
#
# Copyright 2012 Tails developers <tails@boum.org>
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

class OptionsWindow(TranslatableWindow):
    """Display a pre-login window"""

    def __init__(self, greeter):
        self.greeter = greeter

        builder = gtk.Builder()
        builder.set_translation_domain(GdmGreeter.__appname__)
        builder.add_from_file(os.path.join(GdmGreeter.GLADE_DIR, "optionswindow.glade"))
        builder.connect_signals(self)
        self.entry_password = builder.get_object("password_entry")
        self.entry_password2 = builder.get_object("password_entry2")
        self.warning_label = builder.get_object("warning_label")
        self.warning_image = builder.get_object("warning_image")
        self.warning_image.hide()

        TranslatableWindow.__init__(self, builder.get_object("options_dialog"))
        self.window.set_visible(False)

        self.entry_password.set_visibility(False)
        self.entry_password2.set_visibility(False)

    def save_password(self):
        """obtain, verify and store root access password"""
        auth_password = self.entry_password.get_text()
        test_password = self.entry_password2.get_text()
        if test_password == auth_password:
            self.greeter.login()
            self.greeter.rootaccess.password = self.entry_password.get_text()
        else:
            self.warning_label.set_markup(_('<i>Passwords do not match</i>'))
            self.warning_image.show()

    def cb_login_clicked(self, widget, data=None):
        """Login button click handler"""
        self.save_password()

    def key_press_event_cb(self, widget, event=None):
        """Handle key press"""
        if event:
            if event.keyval == gtk.keysyms.Return:
                self.save_password()

