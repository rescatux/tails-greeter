#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Localistaion panel

"""

import logging, gtk, gettext, os
_ = gettext.gettext
from GdmGreeter.language import TranslatableWindow
import GdmGreeter
import GdmGreeter.language as language

class LangDialog(TranslatableWindow):
    """Language selection dialog"""

    def __init__(self):
        builder = gtk.Builder()
        builder.set_translation_domain(GdmGreeter.__appname__)
        builder.add_from_file(os.path.join(GdmGreeter.GLADE_DIR, "langdialog.glade"))
        self.dialog = builder.get_object("languages_dialog")
        self.treeview = builder.get_object("languages_treeview")
        self.liststore = builder.get_object("languages_liststore")
        builder.connect_signals(self, self.dialog)

        tvcolumn = gtk.TreeViewColumn(_("Language"))
        self.treeview.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'text', 1)

        TranslatableWindow.__init__(self, self.dialog)

    def cb_langdialog_key_press(self, widget, event, data=None):
        """Handle key press in langdialog"""
        if event.keyval in [ gtk.keysyms.Return, gtk.keysyms.KP_Enter ]:
            if isinstance(data, gtk.Dialog):
                data.response(True)

    def cb_langdialog_button_press(self, widget, event, data=None):
        """Handle mouse click in langdialog"""
        if (event.type == gtk.gdk._2BUTTON_PRESS or
                event.type == gtk.gdk._3BUTTON_PRESS):
            if isinstance(data, gtk.Dialog):
                data.response(True)

class LangPanel(TranslatableWindow):
    """Display language and layout selection panel"""

    def __init__(self, greeter):
        self.greeter = greeter

        # XXX: initialize instance variables
        self.additional_language_displayed = False
        self.default_position = 0

        # Build UI
        builder = gtk.Builder()
        builder.set_translation_domain(GdmGreeter.__appname__)
        builder.add_from_file(os.path.join(GdmGreeter.GLADE_DIR, "langpanel.glade"))
        builder.connect_signals(self)
        self.window = builder.get_object("langpanel")

        cell = gtk.CellRendererText()

        self.cb_languages = builder.get_object("lang_list_cbox")
        self.cb_languages.pack_start(cell, True)
        self.cb_languages.add_attribute(cell, 'text', 1)

        self.cb_locales = builder.get_object("locale_cbox")
        self.cb_locales.pack_start(cell, True)
        self.cb_locales.add_attribute(cell, 'text', 1)

        self.cb_layouts = builder.get_object("layout_cbox")
        self.cb_layouts.pack_start(cell, True)
        self.cb_layouts.add_attribute(cell, 'text', 1)

        self.cb_variants = builder.get_object("variant_cbox")
        if self.cb_variants:
            self.cb_variants.pack_start(cell, True)
            self.cb_variants.add_attribute(cell, 'text', 1)

        TranslatableWindow.__init__(self, self.window)

        self.populate_languages()
        self.cb_languages.set_active(self.default_position)
        self.set_panel_geometry()

    def set_panel_geometry(self):
        """Position panel to bottom and use full screen width"""
        panel = self.window
        panel.set_gravity(gtk.gdk.GRAVITY_SOUTH_WEST)
        width, height = panel.get_size()
        panel.set_default_size(gtk.gdk.screen_width(), height)
        panel.move(0, gtk.gdk.screen_height() - height)

    # Populate lists

    def populate_languages(self):
        """Create all the required entries"""
        count = 0
        for l in self.greeter.localisationsettings.get_default_languages():
            self.cb_languages.get_model().append([l, language.language_name(l)])
            if l == self.greeter.localisationsettings.get_language():
                self.default_position = count
            count += 1
        self.cb_languages.get_model().append(['', _("Other...")])

    def populate_locales(self):
        """populate the lists for a given language"""
        self.cb_locales.get_model().clear()
        count = 0
        default_position = 0
        for l in self.greeter.localisationsettings.get_default_locales():
            self.cb_locales.get_model().append([l, language.country_name(l)])
            if l == self.greeter.localisationsettings.get_locale():
                default_position = count
            count += 1
        self.cb_locales.set_active(default_position)

    def populate_layouts(self):
        """populate the lists for current locale"""
        self.cb_layouts.get_model().clear()
        count = 0
        default_position = 0
        for l in self.greeter.localisationsettings.get_default_layouts():
            self.cb_layouts.get_model().append([l, language.layout_name(l)])
            if l == self.greeter.localisationsettings.get_layout():
                default_position = count
            count += 1
        self.cb_layouts.set_active(default_position)
        #XXX select default locale!

    # Callbacks

    def key_event_cb(self, widget, event=None):
        """Handle key event - check for layout change"""
        if event:
            if (event.keyval == gtk.keysyms.ISO_Next_Group or
                event.keyval ==  gtk.keysyms.ISO_Prev_Group):
                pass

    def layout_selected(self, widget):
        """handler for combobox selecion event"""
        i = self.cb_layouts.get_active_iter()
        if i:
            l = self.cb_layouts.get_model().get(i, 0)[0]
            if l:
                self.greeter.localisationsettings.set_layout(l)

    def locale_selected(self, widget):
        """handler for locale combobox selection event"""
        i = self.cb_locales.get_active_iter()
        if i:
            l = self.cb_locales.get_model().get(i, 0)[0]
            if l:
                self.greeter.localisationsettings.set_locale(l)
                self.populate_layouts()

    def language_selected(self, widget):
        """handler for language combobox selection event"""
        if self.cb_languages.get_active() == \
                self.cb_languages.get_model().iter_n_children(None) - 1:
            selected_language = self.show_more_languages()
        else:
            i = self.cb_languages.get_active_iter()
            if i:
                selected_language = self.cb_languages.get_model().get(i, 0)[0]

        if selected_language:
            self.greeter.localisationsettings.set_language(selected_language)
            self.populate_locales()
            if not selected_language == self.cb_languages.get_model().get(
                    self.cb_languages.get_active_iter(), 0)[0]:
                self.update_other_language_entry(selected_language)

    # "Other..." dialog handeling

    def update_other_language_entry(self, lang=None):
        if not lang:
            lang = _("Other...")
        last_entry = self.cb_languages.get_model().iter_n_children(None) - 1
        if not self.additional_language_displayed:
            self.cb_languages.get_model().insert(
                last_entry,
                [lang, language.language_name(lang)])
            self.cb_languages.set_active(last_entry)
            self.additional_language_displayed = True
        else:
            self.cb_languages.get_model().set(
                self.cb_languages.get_model().get_iter(last_entry - 1),
                0,
                language)
            self.cb_languages.set_active(last_entry - 1)

    def show_more_languages(self):
        """Show a dialog to allow selecting more languages"""

        langdialog = LangDialog()

        count = 0
        for l in self.greeter.localisationsettings.get_languages():
            langdialog.liststore.append([l, language.language_name(l)])
            # XXX
            if self.greeter.localisationsettings.get_language() == l:
                self.default_position = count
            count += 1

        lang = None
        if langdialog.dialog.run():
            dummy, selected_iter = langdialog.treeview.get_selection().get_selected()
            if selected_iter:
                lang = langdialog.liststore[selected_iter][0]

        langdialog.dialog.destroy()

        return lang
