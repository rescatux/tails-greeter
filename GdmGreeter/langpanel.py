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

import logging, gtk, xklavier

from gtkme.listview import text_combobox
from xklavier import XKLL_TRACK_KEYBOARD_STATE
from GdmGreeter.language import TranslatableWindow, LANGS, ln_list, ln_cc

class LangPanel(TranslatableWindow):
    """Display language and layout selection panel"""
    name = 'langpanel'
    primary = False
    language_name = None
    configreg = None
    layout = 'us'
    selected_layout = 'us'
    engine = None
    crecord = None
    layout_name = None
    language_code = None
    default_position = 0

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.engine = xklavier.Engine(gtk.gdk.display_get_default())
        self.configreg = xklavier.ConfigRegistry(self.engine)
        self.configreg.load(False)
        self.crecord = xklavier.ConfigRec()
        self.crecord.get_from_server(self.engine)
        text_combobox(self.widget('locale_variant_combobox'), self.widget('locales'))
        text_combobox(self.widget('layout_combobox'), self.widget('layouts'))
        text_combobox(self.widget('lang_list_combobox'), self.widget('languages'))
        self.populate()
        self.widget('lang_list_combobox').set_active(self.default_position)

    def populate_locale_variant(self, language):
        """populate the list with country variants for a given language"""
        self.widget('layouts').clear()
        self.widget('layouts').append(['us'])
        self.layout = ln_cc(language).split('_')[1].lower()
        logging.debug('layout is %s', self.layout)
        if self.layout and self.layout != 'us':
            self.widget('layouts').append([self.layout])
            logging.debug('added layout %s', self.layout)
            self.crecord.set_layouts(['us', self.layout])
            self.crecord.set_options(['grp:alt_shift_toggle'])
            logging.debug('options set to %s', self.crecord.get_options())
            self.crecord.activate(self.engine)
        self.widget('layout_combobox').set_active(0)
        self.widget('locales').clear()
        count = 0
        default = 0
        for l in ln_list(language):
            self.widget('locales').append([l])
            if 'en_US' == l:
                default = count
            count += 1
        self.widget('locale_variant_combobox').set_active(default)
        self.gen_variants()

    def gen_variants(self):
        """function to trigger layout variant selection"""
        self.configreg.foreach_layout(self.filter_layout)

    def get_current_layout(self):
        """Get currently active keyboard layout"""
        self.engine.start_listen(XKLL_TRACK_KEYBOARD_STATE)
        self.engine.lock_group(self.engine.get_next_group())
        layout_index = self.engine.get_current_state()['group']
        self.engine.stop_listen(XKLL_TRACK_KEYBOARD_STATE)
        # assume only 2 layouts with 'us' always first one
        if layout_index:
            return self.layout
        else:
            return 'us'

    def key_event_cb(self, widget, event=None):
        """Handle key event: Alt+Shift"""
        if event.state & gtk.gdk.SHIFT_MASK:
            if event.state & gtk.gdk.MOD1_MASK:
                if 'us' == self.selected_layout:
                    self.selected_layout = self.layout
                else:
                    self.selected_layout = 'us'
                logging.debug('layout has changed to %s', self.selected_layout)
#        l = self.get_current_layout()
#        if self.selected_layout != l:
#            self.selected_layout = l
#            logging.debug('layout has changed to %s', self.selected_layout)

    def populate(self):
        """Create all the required entries"""
        count = 0
        for l in LANGS:
            self.widget('languages').append([l])
            if 'English' == l:
                self.default_position = count
            count += 1

    def populate_layouts(self, c_reg, item):
        """Obtain variants for a given layout"""
#        self.widget('layouts').append(['%s (%s)' % (item.get_description(), item.get_name())])

    def layout_selected(self, widget):
        """handler for combobox selecion event"""
        self.layout = self.widget('layout_combobox').get_active_text()
        logging.debug('obtained layout %s', self.layout)
        if self.layout:
            logging.debug('setting layout %s', self.layout)
            self.gapp.SelectLayout(self.layout)

    def locale_selected(self, widget):
        """handler for combobox selecion event"""
        self.language_code = self.widget('locale_variant_combobox').get_active_text()
        self.gen_variants()

    def filter_layout(self, c_reg, item):
        """Handle particular layout"""
        if item.get_name() == self.layout:
            self.layout_name = item.get_description()
            c_reg.foreach_layout_variant(item.get_name(), self.populate_layouts)
            self.widget('layout_combobox').set_active(0)

    def button_clicked(self, widget):
        """Signal event to move to next widget"""
        logging.debug('panel button clicked')
        self.translate_action(widget, False)
        self.language_code = self.widget('locale_variant_combobox').get_active_text()
        self.gapp.SelectLanguage(self.language_code)
        self.gapp.SwitchVisibility()

    def translate_to(self, lang):
        """Press the selected language's button"""
        lang = self.language(lang)
        TranslatableWindow.translate_to(self, lang)
        logging.debug('translating to %s', lang)

    def translate_action(self, widget, populate_locales = True):
        """Signal event to translate entire app"""
        self.language_name = self.widget('lang_list_combobox').get_active_text()
        self.gapp.SelectLanguage(ln_cc(self.language_name))
        if populate_locales:
            self.populate_locale_variant(self.language_name)

    def skip_button_clicked(self, widget):
        """Initiate immediate login"""
        self.gapp.ForcedLogin()
