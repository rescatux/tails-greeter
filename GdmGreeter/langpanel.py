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

import logging, gtk, xklavier, gettext
_ = gettext.gettext
from gtkme.listview import text_combobox
from GdmGreeter.language import TranslatableWindow, LANGS, ln_list, ln_country, ln_iso639_tri

class LangPanel(TranslatableWindow):
    """Display language and layout selection panel"""
    name = 'langpanel'
    primary = False
    language_name = None
    configreg = None
    layout = 'us'
    variant = None
    engine = None
    crecord = None
    lang3 = None
    options = 'grp:alt_shift_toggle' # 'grp:sclk_toggle' would be much more convenient but we default to mustdie switcher in here
    layout_name = None
    language_code = None
    default_position = 0
    variant_list = None
    layout_list = None
    locales = {}
    layouts = {}

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.engine = xklavier.Engine(gtk.gdk.display_get_default())
        self.configreg = xklavier.ConfigRegistry(self.engine)
        self.configreg.load(False)
        self.crecord = xklavier.ConfigRec()
        self.crecord.get_from_server(self.engine)
        text_combobox(self.widget('locale_cbox'), self.widget('locales'))
        text_combobox(self.widget('layout_cbox'), self.widget('layouts'))
        text_combobox(self.widget('lang_list_cbox'), self.widget('languages'))
        self.populate()
        self.widget('lang_list_cbox').set_active(self.default_position)
        self.set_panel_geometry()

    def set_panel_geometry(self):
        """Position panel to bottom and use full screen width"""
        panel = self.widget('langpanel')
        panel.set_gravity(gtk.gdk.GRAVITY_SOUTH_WEST)
        width, height = panel.get_size()
        panel.set_default_size(gtk.gdk.screen_width(), height)
        panel.move(0, gtk.gdk.screen_height() - height)

    def populate_for_locale(self, locale):
        """populate the lists for a given locale"""
        self.widget('layouts').clear()
        self.lang3 = ln_iso639_tri(locale)
        if self.lang3:
            layouts = self.get_layouts_for_language(self.lang3)
            count = 0
            default = 0
            backup = 0
            use_default = 0
            for l in layouts:
                layout_name = l.split(')')[0].split('(')[1]
                self.layouts[layout_name] = l.split()[0]
                self.widget('layouts').append([layout_name])
                if locale.split('_')[1].lower() == self.layouts[layout_name]:
                    default = count
                    use_default = 1
                if locale.split('_')[0].lower() == self.layouts[layout_name]: backup = count
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
            self.widget('locales').append([ln_country(l)])
            self.locales[unicode(ln_country(l))] = l
            if 'en_US' == l: default = count
            if l.split('_')[0] == l.split('_')[1].lower(): default = count
            count += 1
        self.widget('locale_cbox').set_active(default)

    def apply_layout(self, layout):
        """populate the lists for a given layout"""
        self.variant_list = []
        self.layout_list = []
        if self.variant and self.variant != 'Default': self.variant_list = ['', self.variant]
        else: self.variant_list = ['']
        if len(self.variant_list) > 1 or layout != 'us': self.layout_list = [layout, 'us']
        else: self.layout_list = ['us']
        self.crecord.set_variants(self.variant_list)
        self.crecord.set_layouts(self.layout_list)
        self.crecord.set_options([self.options])
        self.crecord.activate(self.engine)
        logging.debug('L:%s V:%s O:%s', self.crecord.get_layouts(), self.crecord.get_variants(), self.crecord.get_options())

    def key_event_cb(self, widget, event=None):
        """Handle key event - check for layout change"""
        if event:
            if event.keyval ==  gtk.keysyms.ISO_Next_Group or event.keyval ==  gtk.keysyms.ISO_Prev_Group:
                pass

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

    def switch_layout(self):
        """enforce layout"""
        if self.variant != 'Default':
            self.engine.start_listen(xklavier.XKLL_TRACK_KEYBOARD_STATE)
            self.engine.lock_group(1)
            self.engine.stop_listen(xklavier.XKLL_TRACK_KEYBOARD_STATE)
        
    def update_layout_indicator(self):
        """update layout indicator state"""
        self.engine.start_listen(xklavier.XKLL_TRACK_KEYBOARD_STATE)
        state = self.engine.get_current_state()
        self.engine.stop_listen(xklavier.XKLL_TRACK_KEYBOARD_STATE)
        layout = self.crecord.get_layouts()
        if layout:
            if state['group'] < len(layout):
                layout = layout[state['group']].upper()
            else: layout = layout[0].upper()
        variant = self.crecord.get_variants()
        shown = False
        if variant:
            if state['group'] < len(variant):
                variant = variant[state['group']]
                if variant:
                    self.widget('layout_indicator').set_text(_('Current layout: %s (%s)') % (layout, variant))
                    shown = True
        if not shown:
            self.widget('layout_indicator').set_text(_('Current layout: %s') % layout)

    def populate(self):
        """Create all the required entries"""
        count = 0
        for l in LANGS:
            self.widget('languages').append([l])
            if 'English' == l: self.default_position = count
            count += 1

    def layout_selected(self, widget):
        """handler for combobox selecion event"""
        l = self.widget('layout_cbox').get_active_text()
        if l:
            self.layout = self.layouts[l]
            if self.layout:
                self.variant = None
                self.apply_layout(self.layout)
                logging.debug('selected layout %s', l)
                self.gapp.SelectLayout(self.layout)
                self.switch_layout()
                variants = self.get_varians_for_layout(self.layout)
                self.widget('variants').clear()
                self.widget('variants').append(['Default'])
                for v in variants:
                    self.widget('variants').append([v])

    def variant_selected(self, widget):
        """handler for combobox selecion event"""
        if variant:
            self.apply_layout(self.layout)

    def locale_selected(self, widget):
        """handler for combobox selecion event"""
        self.language_code = self.widget('locale_cbox').get_active_text()
        if self.language_code:
            self.language_code = self.locales[unicode(self.language_code)]
            if self.language_code:
                self.variant = None
                self.gapp.SelectLanguage(self.language_code)
                self.populate_for_locale(self.language_code)

    def language_selected(self, widget):
        """Signal event to translate entire app"""
        self.language_name = self.widget('lang_list_cbox').get_active_text()
        if self.language_name: self.populate_for_language(self.language_name)

