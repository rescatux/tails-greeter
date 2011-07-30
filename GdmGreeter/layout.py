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

from GdmGreeter.language import TranslatableWindow

def print_variant(c_reg, item):
    print ('\t %s (%s)' % (item.get_description(), item.get_name()))

class LayoutWindow(TranslatableWindow):
    """Display layout selection window"""
    name = 'layout'
    primary = False
    configreg = None
    layout = 'us'    

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.configreg = xklavier.ConfigRegistry(xklavier.Engine(gtk.gdk.display_get_default()))

    def filter_layout(self, c_reg, item):
        if item.get_name() == self.layout:
            print ('\n%s (%s)' % (item.get_description(), item.get_name()))
            c_reg.foreach_layout_variant(item.get_name(), print_variant)

    def get_variants(self):
        self.configreg.load(False)
        return self.configreg.foreach_layout(self.filter_layout)

    def button_clicked(self, widget):
        """Signal event to move to next widget"""
        logging.debug('layout button clicked')
        self.gapp.SwitchVisibility()
