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
from GdmGreeter.language import TranslatableWindow, ln_list, ln_cc

class LayoutWindow(TranslatableWindow):
    """Display layout selection window"""
    name = 'layout'
    primary = False
    configreg = None
    layout = 'us'
    layout_name = None
    language_code = None

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.configreg = xklavier.ConfigRegistry(xklavier.Engine(gtk.gdk.display_get_default()))
        self.configreg.load(False)
        text_combobox(self.widget('country_variant_combobox'), self.widget('countries'))
        text_combobox(self.widget('layout_combobox'), self.widget('layouts'))

    def populate(self, language):
        self.populated_language = language
        self.layout = ln_cc(self.language).split('_')[1].lower()
        logging.debug('layout set to %s', self.layout)
        for l in ln_list(self.language):
            self.widget('countries').append([l])
        self.widget('country_variant_combobox').set_active(0)
        self.gen_variants()

    def gen_variants():
        self.widget('layouts').clear()
        self.configreg.foreach_layout(self.filter_layout)

    def populate_layouts(self, c_reg, item):
        """Obtain variants for a given layout"""
        self.widget('layouts').append(['%s (%s)' % (item.get_description(), item.get_name())])

    def locale_selected(self, widget):
        self.language_code = self.widget('country_variant_combobox').get_active_text()
        self.gen_variants()

    def filter_layout(self, c_reg, item):
        """Handle particular layout"""
        if item.get_name() == self.layout:
            self.layout_name = item.get_description()
            c_reg.foreach_layout_variant(item.get_name(), self.populate_layouts)
            self.widget('layout_combobox').set_active(0)

    def button_clicked(self, widget):
        """Signal event to move to next widget"""
        logging.debug('layout button clicked')
        self.language_code = self.widget('country_variant_combobox').get_active_text()
        self.gapp.SelectLanguage(self.language_code)
        self.gapp.SwitchVisibility()
