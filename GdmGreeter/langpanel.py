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
    selected_layout = 'us'
    engine = None
    crecord = None
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
        text_combobox(self.widget('locale_variant_cbox'), self.widget('locales'))
        text_combobox(self.widget('layout_cbox'), self.widget('layouts'))
        text_combobox(self.widget('session_layouts_cbox'), self.widget('session_layouts'))
        text_combobox(self.widget('lang_list_cbox'), self.widget('languages'))
        self.populate()
        self.widget('lang_list_cbox').set_active(self.default_position)

    def populate_for_locale(self, locale):
        """populate the lists for a given locale"""
        self.widget('layouts').clear()
        language_iso639 = iso639().conv(locale)
        if language_iso639:
            layouts = self.get_layouts_for_language(language_iso639)
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
            if 'en_US' != locale:
                if use_default: self.widget('layout_cbox').set_active(default)
                else: self.widget('layout_cbox').set_active(backup)            
        else:
            self.widget('session_layouts').clear()
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
        self.widget('locale_variant_cbox').set_active(default)

    def populate_for_layout(self, layout):
        """populate the lists for a given layout"""
        self.widget('session_layouts').clear()
        self.widget('session_layouts').append(['us'])
        if layout != 'us':
            self.added_layout = layout
            self.widget('session_layouts').append([self.added_layout])
            logging.debug('added layout %s', self.added_layout)
            self.crecord.set_layouts(['us', self.added_layout])
            self.crecord.set_options(['grp:alt_shift_toggle'])
#            self.crecord.set_options(['grp:sclk_toggle'])
            logging.debug('options set to %s', self.crecord.get_options())
            self.crecord.activate(self.engine)
        self.widget('session_layouts_cbox').set_active(0)

    def key_event_cb(self, widget, event=None):
        """Handle key event - check for layout change"""
        if event:
            if event.keyval ==  gtk.keysyms.ISO_Next_Group or event.keyval ==  gtk.keysyms.ISO_Prev_Group:
                self.update_layout_indicator()

    def layout_populate_lang(self, config_registry, item, subitem, store):
        """add layout to the store"""
        layout = item.get_name()
        if 'us' != layout:
            name = '%s (%s)' % (layout, item.get_description())
            if name not in store: store.append(name)
#        if subitem:
#            description = '%s, %s' % (subitem.get_description(), item.get_description())
#            variant = subitem.get_name()
#        else:
#            description = 'Default layout, %s' % item.get_description()
#            variant = ''
#        store.append([description, ('%s(%s)' % (layout, variant))])
#        logging.debug('appending %s: %s(%s)', description, layout, variant)

    def get_layouts_for_language(self, language):
        """Return list of supported keyboard layouts for a given language"""
        layouts = []
        self.configreg.foreach_language_variant(language, self.layout_populate_lang, layouts)
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
            if 'English' == l:
                self.default_position = count
            count += 1

    def layout_selected(self, widget):
        """handler for combobox selecion event"""
        layout = self.widget('layout_cbox').get_active_text()
        logging.debug('selected layout %s', layout)
        if layout: self.populate_for_layout(layout.split()[0])

    def session_layout_selected(self, widget):
        """handler for combobox selecion event"""
        self.layout = self.widget('session_layouts_cbox').get_active_text()
        if self.layout: self.gapp.SelectLayout(self.layout)

    def locale_selected(self, widget):
        """handler for combobox selecion event"""
        self.language_code = self.widget('locale_variant_cbox').get_active_text()
        if self.language_code:
            self.gapp.SelectLanguage(self.language_code)
            self.populate_for_locale(self.language_code)

    def language_selected(self, widget):
        """Signal event to translate entire app"""
        self.language_name = self.widget('lang_list_cbox').get_active_text()
        self.populate_for_language(self.language_name)

