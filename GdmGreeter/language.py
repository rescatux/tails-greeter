#!/usr/bin/python
#
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
"""
Greeter program for GDM using gtk (nothing else works)
"""

import logging, babel, gettext, gtk

from gtk import gdk
from subprocess import Popen, PIPE
from gtkme import Window, FormWindow
from GdmGreeter import Images

MOFILES = '/usr/share/locale/'
DOMAIN  = 'tails-greeter'
IMAGES = Images('lang')

p = Popen(["tails-lang-helper.sh"], stdout=PIPE)
langcodes = str.split(p.communicate()[0])
logging.debug('%s languages found: helper returned %s', len(langcodes), p.returncode)
LANGS = map(lambda x: babel.Locale.parse(x), langcodes)

def get_texts(langs):
    """obtain texts for a given locale using gettext"""
    result = {}
    for loc in langs:
        try:
            result[str(loc)] = gettext.translation(DOMAIN, MOFILES, [str(loc)])
        except IOError:
            logging.error('Failed to get texts for %s locale', loc)
    return result

TEXTS = get_texts(LANGS)

class Translatable(object):
    """Provides functions for translating the window on the fly"""
    retain_focus = True

    def __init__(self):
        self.labels = []
        self.tips = []
        self.store_translations(self.window)

    def store_translations(self, widget):
        """Go through all widgets and store the translatable elements"""
        for child in widget.get_children():
            if isinstance(child, gtk.Container):
                self.store_translations(child)
            if isinstance(child, gtk.Label):
                self.labels.append( (child, child.get_label()) )
            if child.get_has_tooltip():
                self.tips.append( (child, child.get_tooltip_text()) )

    def language(self, lang):
        """Return normalised language for use in this process"""
        if '_' in lang:
            lang = lang.split('_')[0]
        if '.' in lang:
            lang = lang.split('.')[0]
        return lang.lower()

    def gettext(self, lang, text):
        """Return a translated string or string"""
        if lang:
            text = lang.gettext(text)
        return text

    def translate_to(self, lang):
        """Loop through everything and translate on the fly"""
        lang = TEXTS.get(self.language(lang), None)
        for (child, text) in self.labels:
            child.set_label(self.gettext(lang, text))
        for (child, text) in self.tips:
            child.set_tooltip_markup(self.gettext(lang, text))
        if self.window.get_sensitive() and self.retain_focus:
            self.window.present()

class TranslatableWindow(Translatable, Window):
    """dynamically translatable window"""
    def __init__(self, *args, **kwargs):
        Window.__init__(self, *args, **kwargs)
        Translatable.__init__(self)

class TranslatableFormWindow(Translatable, FormWindow):
    """dynamically translatable window with form"""
    def __init__(self, *args, **kwargs):
        FormWindow.__init__(self, *args, **kwargs)
        Translatable.__init__(self)

class LanguageWindow(TranslatableWindow):
    """A language selection window for display at the bottom"""
    name = 'language'
    primary = False
    retain_focus = False

    def __init__(self, *args, **kwargs):
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.container = self.if_widget("buttonbar")
        self.images = Images('lang')
        self.buttons = {}
        self.populate()
        self.window.set_gravity(gdk.GRAVITY_SOUTH)

    def set_position(self, width, height):
        """Set the window's possition in the middle of the screen"""
        logging.debug("Setting pos: %sx%s resolution", width, height)
        self.window.move(width/2, height)

    def populate(self):
        """Create all the required entries"""
        for locale in LANGS:
            # Our locale needs to be without territory
            locale = babel.Locale.parse(locale.language)
            # Because the territory could repeat the language, ignore after the first language.
            if not self.buttons.has_key(str(locale)):
                button = LanguageButton(locale, self.button_clicked)
                if button:
                    self.container.pack_start(button, False, False, 0)
                    self.buttons[str(locale)] = button

    def translate_to(self, lang):
        """Press the selected language's button"""
        lang = self.language(lang)
        TranslatableWindow.translate_to(self, lang)
        for lid, button in self.buttons.iteritems():
            if button:
                button.set_sensitive(lid != lang)
            else:
                logging.warn("Couldn't find a button for language: %s", lid)

    def button_clicked(self, widget, lang):
        """Signal event for button clicking, translate entire app"""
        self.gapp.SelectLanguage(lang)
        self.gapp.SwitchVisibility()


def LanguageButton(locale, signal=None):
    """Returns a gtk button with the correct contents"""
    code = str(locale)
    button = gtk.Button()
    if signal:
        button.connect('clicked', signal, code)
    button.set_relief(gtk.RELIEF_NONE)
    holder = gtk.VBox()
    button.add(holder)
    icon = gtk.Image()
    label = gtk.Label()
    holder.pack_start(icon, True, True, 6)
    logging.debug("Loading pixmap for '%s'", code)
    image = IMAGES.get_pixmap(code)
    if not image:
        return None
    logging.debug("Setting icon from '%s' pixmap", code)
    icon.set_from_pixbuf(image)
    holder.pack_end(label, False, True, 0)
    label_unicode = "<b>%s</b>" % locale.languages[code] 
    label.set_markup(label_unicode.encode('UTF-8'))
    button.show_all()
    return button

