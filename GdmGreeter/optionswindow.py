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
"""Second screen

"""

import logging, gtk, os
import GdmGreeter
from GdmGreeter.language import TranslatableWindow
from helpwindow import HelpWindow

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
        self.warning_area = builder.get_object("warning_area")
        self.camouflage_checkbox = builder.get_object("camouflage_checkbox")
        self.macspoof_checkbox = builder.get_object("macspoof_checkbox")
        self.macspoof_checkbox.set_active(True)

        TranslatableWindow.__init__(self, builder.get_object("options_dialog"))
        self.window.set_visible(False)

        self.warning_area.hide()
        self.entry_password.set_visibility(False)
        self.entry_password2.set_visibility(False)

    # Help callback handler
    cb_doc_handler = HelpWindow.cb_doc_handler

    def set_password(self):
        """Set root access password"""
        password = self.entry_password.get_text()
        if password:
            self.greeter.rootaccess.password = password

    def set_camouflage(self):
        """Set camouflage theme"""
        if self.camouflage_checkbox.get_active():
            self.greeter.camouflage.os = 'winxp'

    def set_macspoof(self):
        """Set macspoof status"""
        self.greeter.physical_security.macspoof = self.macspoof_checkbox.get_active()

    def validate_options(self):
        """Validate the selected options"""
        auth_password = self.entry_password.get_text()
        test_password = self.entry_password2.get_text()
        passwords_match = test_password == auth_password
        if not passwords_match:
            self.warning_area.show()
        return passwords_match

    def set_options_and_login(self):
        """Activate the selected options if they are valid"""
        if self.validate_options():
            self.greeter.login()
            self.set_password()
            self.set_camouflage()
            self.set_macspoof()

    def cb_login_clicked(self, widget, data=None):
        """Login button click handler"""
        self.set_options_and_login()

    def key_press_event_cb(self, widget, event=None):
        """Handle key press"""
        if event:
            if event.keyval in [ gtk.keysyms.Return, gtk.keysyms.KP_Enter ]:
                if self.entry_password.is_focus():
                    self.entry_password2.grab_focus()
                elif self.window.get_focus().__class__.__name__ == "Label":
                    # The only labels that we allow to be focused are
                    # the help links, for which Return will activate
                    # the link.
                    return
                else:
                    self.set_options_and_login()

    def delete_event_cb(self, widget, event=None):
        """Ignore delete event (Esc)"""
        return True
