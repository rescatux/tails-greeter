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

import logging

from GdmGreeter.language import TranslatableWindow

class LayoutWindow(TranslatableWindow):
    """Display layout selection window"""
    name = 'layout'
    primary = False

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)

    def button_clicked(self, widget):
        """Signal event to move to next widget"""
        logging.debug('layout button clicked')
        self.gapp.SwitchVisibility()
