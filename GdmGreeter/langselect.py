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
import gtk
import gobject
import babel
import locale
import gettext

from gtkme.listview import text_combobox
from GdmGreeter.services import GdmUsers
from GdmGreeter.language import TranslatableWindow
from GdmGreeter.language import TEXTS, LANGS
from GdmGreeter import Images

class LangselectWindow(TranslatableWindow):
    """Display language selection window"""
    name = 'langselect'
    primary = False

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
	text_combobox(self.widget('combobox1'), self.widget('languages'))

    def populate(self):
        """Create all the required entries"""
        for locale in LANGS:
            # Our locale needs to be without territory
            locale = babel.Locale.parse(locale.language)
            # Because the territory could repeat the language,
            # Ignore after the first language.
	    self.cbox.append_text(locale)
	    logging.debug('%s added to the combo-box', locale)
#            if not self.buttons.has_key(str(locale)):
#                button = LanguageButton(locale, self.button_clicked)
#                if button:
#                    self.container.pack_start(button, False, False, 0)
#                    self.buttons[str(locale)] = button

    def translate_to(self, lang):
        """Press the selected language's button"""
        lang = self.language(lang)
        TranslatableWindow.translate_to(self, lang)
        logging.debug('translating to %s', lang)
#        for lid, button in self.buttons.iteritems():
#            if button:
#                button.set_sensitive(lid != lang)
#            else:
#                logging.warn("Couldn't find a button for language: %s", lid)

    def button_clicked(self, widget, lang):
        """Signal event for button clicking, translate entire app"""
        self.gapp.SelectLanguage(lang)
        self.gapp.SwitchVisibility()
