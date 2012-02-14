#!/usr/bin/python
#
# Copyright 2012 Tails developers <tails@boum.org>
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
import logging, gtk, gettext, os
_ = gettext.gettext
import GdmGreeter
from GdmGreeter.language import TranslatableWindow

class PersistenceWindow(TranslatableWindow):
    """First greeter screen"""

    def __init__(self, greeter):
        self.greeter = greeter

        builder = gtk.Builder()
        builder.set_translation_domain(GdmGreeter.__appname__)
        builder.add_from_file(os.path.join(GdmGreeter.GLADE_DIR, "persistencewindow.glade"))
        builder.connect_signals(self)

        # Sets self.window
        TranslatableWindow.__init__(self, builder.get_object("login_dialog"))
        self.lbl_main = builder.get_object("main_label")
        self.cbx_persistence = builder.get_object("persistence_checkbutton")
        self.lbl_passphrase = builder.get_object("passphrase_label")
        self.entry_passphrase = builder.get_object("passphrase_entry")
        self.btn_options = builder.get_object("options_button")
        self.btn_login = builder.get_object("login_button") 

    def process_persistence(self):
        """Ask the backend to setup persistence and handle errors

        Returns: True if everything went fine, False if the user should try again"""
        if self.cbx_persistence.get_active():
            try:
                self.greeter.persistence.activate(self.entry_passphrase.get_text())
                return True
            except GdmGreeter.WrongPassphraseError:
                self.lbl_main = _("Wrong passphrase. Please try again.")
                return False
        else:
            return True

    def cb_persistence_toggeled(self, widget, data=None):
        persistence = widget.get_active()
        self.lbl_passphrase.set_visible(persistence)
        self.entry_passphrase.set_visible(persistence)

    def cb_login_clicked(self, widget, data=None):
        if self.process_persistence():
            self.greeter.login()

    def cb_options_clicked(self, widget, data=None):
        if self.process_persistence():
            self.window.hide()
            self.greeter.langpanel.window.hide()
            self.greeter.optionswindow.window.show()
