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
from GdmGreeter.language import TranslatableWindow, LANGS, ln_list, iso639

class LangPanel(TranslatableWindow):
    """Display language and layout selection panel"""
    name = 'langpanel'
    primary = False
    language_name = None
    configreg = None
    layout = 'us'
    variant = None
    selected_layout = 'us'
    engine = None
    crecord = None
    lang3 = None
    layout_name = None
    added_layout = None
    language_code = None
    default_position = 0

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.engine = xklavier.Engine(gtk.gdk.display_get_default())
        self.configreg = xklavier.ConfigRegistry(self.engine)
        self.configreg.load(False)
        self.crecord = xklavier.ConfigRec()
        self.crecord.get_from_server(self.engine)
        text_combobox(self.widget('locale_cbox'), self.widget('locales'))
        text_combobox(self.widget('layout_cbox'), self.widget('layouts'))
        text_combobox(self.widget('variant_cbox'), self.widget('variants'))
        text_combobox(self.widget('lang_list_cbox'), self.widget('languages'))
        self.populate()
        self.widget('lang_list_cbox').set_active(self.default_position)

    def populate_for_locale(self, locale):
        """populate the lists for a given locale"""
        self.widget('layouts').clear()
        self.lang3 = iso639().conv(locale)
        if self.lang3:
            layouts = self.get_layouts_for_language(self.lang3)
            count = 0
            default = 0
            backup = 0
            use_default = 0
            for l in layouts:
                self.widget('layouts').append([l])
                if locale.split('_')[1].lower() == l.split()[0]:
                    default = count
                    use_default = 1
                if locale.split('_')[0].lower() == l.split()[0]: backup = count
                count += 1
            if use_default: self.widget('layout_cbox').set_active(default)
            else: self.widget('layout_cbox').set_active(backup)            
        else:
            self.crecord.set_layouts(['us'])
            self.crecord.activate(self.engine)
            self.gapp.SelectLayout('us')

    def populate_for_language(self, language):
        """populate the lists for a given language"""
        self.widget('locales').clear()
        count = 0
        default = 0
        for l in ln_list(language):
            self.widget('locales').append([l])
            if 'en_US' == l: default = count
            count += 1
        self.widget('locale_cbox').set_active(default)

    def apply_layout(self, layout):
        """populate the lists for a given layout"""
        if layout != 'us':
            self.added_layout = layout
            logging.debug('added layout %s', self.added_layout)
            self.crecord.set_layouts(['us', self.added_layout])
            self.crecord.set_options(['grp:alt_shift_toggle']) # mustdie way
#            self.crecord.set_options(['grp:sclk_toggle']) # proper way
            logging.debug('options set to %s', self.crecord.get_options())
            self.crecord.activate(self.engine)

    def key_event_cb(self, widget, event=None):
        """Handle key event - check for layout change"""
        if event:
            if event.keyval ==  gtk.keysyms.ISO_Next_Group or event.keyval ==  gtk.keysyms.ISO_Prev_Group:
                self.update_layout_indicator()

    def process_language(self, config_registry, item, subitem, store):
        """add layout to the store"""
        layout = item.get_name()
        if 'eng' == self.lang3 or 'us' != layout:
            name = '%s (%s)' % (layout, item.get_description())
            if name not in store: store.append(name)

    def process_layout(self, config_registry, item, store):
        """add variant to the store"""
        name = '%s (%s)' % (item.get_name(), item.get_description())
        if name not in store: store.append(name)

    def get_varians_for_layout(self, layout):
        """Return list of supported keyboard layout variants for a given layout"""
        variants = []
        self.configreg.foreach_layout_variant(layout, self.process_layout, variants)
        variants.sort()
        logging.debug('got %d variants for layout %s', len(variants), layout)
        return variants

    def get_layouts_for_language(self, language):
        """Return list of supported keyboard layouts for a given language"""
        layouts = []
        self.configreg.foreach_language_variant(language, self.process_language, layouts)
        layouts.sort()
        logging.debug('got %d layouts for %s', len(layouts), language)
        return layouts
        
    def update_layout_indicator(self):
        """update layout indicator state"""
        if 'us' == self.selected_layout: self.selected_layout = self.added_layout
        else: self.selected_layout = 'us'
        logging.debug('layout has changed to %s', self.selected_layout)
        self.widget('layout_indicator').set_text('Current layout: [%s]' % self.selected_layout.upper())

    def populate(self):
        """Create all the required entries"""
        count = 0
        for l in LANGS:
            self.widget('languages').append([l])
            if 'English' == l: self.default_position = count
            count += 1

    def layout_selected(self, widget):
        """handler for combobox selecion event"""
        layout = self.widget('layout_cbox').get_active_text()
        if layout:
            self.apply_layout(layout.split()[0])
            logging.debug('selected layout %s', layout)
            self.layout = layout.split()[0]
            self.gapp.SelectLayout(self.layout)
            variants = self.get_varians_for_layout(self.layout)
            self.widget('variants').clear()
            self.widget('variants').append(['Default'])
            self.widget('variant_cbox').set_active(0)
            for v in variants:
                self.widget('variants').append([v])

    def variant_selected(self, widget):
        """handler for combobox selecion event"""
        variant = self.widget('variant_cbox').get_active_text()
        if variant: self.variant = variant

    def locale_selected(self, widget):
        """handler for combobox selecion event"""
        self.language_code = self.widget('locale_cbox').get_active_text()
        if self.language_code:
            self.gapp.SelectLanguage(self.language_code)
            self.populate_for_locale(self.language_code)

    def language_selected(self, widget):
        """Signal event to translate entire app"""
        self.language_name = self.widget('lang_list_cbox').get_active_text()
        self.populate_for_language(self.language_name)

