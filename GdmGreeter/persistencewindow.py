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

        self.moreoptions = False

        # Sets self.window
        TranslatableWindow.__init__(self, builder.get_object("login_dialog"))
        self.btn_persistence_yes = builder.get_object("persistence_yes_button")
        self.btn_persistence_no = builder.get_object("persistence_no_button")
        self.lbl_passphrase = builder.get_object("passphrase_label")
        self.entry_passphrase = builder.get_object("passphrase_entry")
        self.btn_moreoptions_yes = builder.get_object("moreoptions_yes_button")
        self.btn_moreoptions_no = builder.get_object("moreoptions_no_button")
        self.btn_login = builder.get_object("login_button")
        self.img_login = builder.get_object("login_image")
        self.img_next = builder.get_object("next_image")
        self.box_persistence = builder.get_object("persistence_box")
        self.readonly_checkbutton = builder.get_object("readonly_checkbutton")
        self.warning_label = builder.get_object("warning_label")
        self.warning_area = builder.get_object("warning_area")

        self.warning_area.hide()

        # FIXME: list_containers may raise exceptions. Deal with that.
        self.containers = [
            { "path": container, "locked": True }
            for container in self.greeter.persistence.list_containers()
            ]
        if len(self.containers) == 0:
            self.box_persistence.hide()

        # FIXME:
        # * support multiple persistent containers:
        #   - display brand, model, partition path and size for each container
        #   - create as many passphrase input fields as needed

    def activate_persistence(self):
        """Ask the backend to activate persistence and handle errors

        Returns: True if everything went fine, False if the user should try again"""
        if self.btn_persistence_yes.get_active():
            try:
                self.greeter.persistence.activate(
                    device=self.containers[0]['path'],
                    password=self.entry_passphrase.get_text(),
                    readonly=self.readonly_checkbutton.get_active()
                    )
                return True
            except GdmGreeter.errors.WrongPassphraseError:
                self.warning_label.set_markup(_('<i>Wrong passphrase. Please try again.</i>'))
                self.warning_area.show()
                return False
        else:
            return True

    def set_persistence_visibility(self, persistence):
        self.lbl_passphrase.set_visible(persistence)
        self.entry_passphrase.set_visible(persistence)
        self.btn_persistence_yes.set_active(persistence)
        self.btn_persistence_no.set_active(not persistence)

    def cb_persistence_yes_toggled(self, widget, data=None):
        persistence = widget.get_active()
        self.set_persistence_visibility(persistence)

    def cb_persistence_no_toggled(self, widget, data=None):
        persistence = not widget.get_active()
        self.set_persistence_visibility(persistence)

    def update_login_button(self, moreoptions):
        if moreoptions:
            self.btn_login.set_label("gtk-go-forward")
            self.btn_login.set_use_stock(True)
        else:
            self.btn_login.set_label(_("Login"))
            self.btn_login.set_use_stock(False)
            self.btn_login.set_image(self.img_login)

    def update_moreoptions_buttons(self, moreoptions):
        self.btn_moreoptions_yes.set_active(moreoptions)
        self.btn_moreoptions_no.set_active(not moreoptions)

    def cb_moreoptions_yes_toggled(self, widget, data=None):
        moreoptions = widget.get_active()
        self.moreoptions = moreoptions
        self.update_login_button(moreoptions)
        self.update_moreoptions_buttons(moreoptions)

    def cb_moreoptions_no_toggled(self, widget, data=None):
        moreoptions = not widget.get_active()
        self.moreoptions = moreoptions
        self.update_login_button(moreoptions)
        self.update_moreoptions_buttons(moreoptions)

    def go(self):
        if self.activate_persistence():
            # next
            if self.moreoptions:
                self.window.hide()
                self.greeter.langpanel.window.hide()
                self.greeter.optionswindow.window.show()
            # login
            else:
                self.greeter.login()

    def cb_login_clicked(self, widget, data=None):
        self.go()

    def key_press_event_cb(self, widget, event=None):
        """Handle key press"""
        if event:
            if event.keyval == gtk.keysyms.Return:
                self.go()

    def delete_event_cb(self, widget, event=None):
        """Ignore delete event (Esc)"""
        return True
