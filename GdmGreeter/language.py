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

import logging, gettext, gtk, xklavier

from subprocess import Popen, PIPE
from gtkme import Window, FormWindow
from GdmGreeter import Images
from icu import Locale, Collator

MOFILES = '/usr/share/locale/'
DOMAIN  = 'tails-greeter'
IMAGES = Images('lang')

p = Popen(["tails-lang-helper"], stdout=PIPE)
langcodes = str.split(p.communicate()[0])
logging.debug('%s languages found: helper returned %s', len(langcodes), p.returncode)

def ln_cc(lang_name):
    """obtain language code from name, for example: English -> en_US"""
    return LDICT[unicode(lang_name)][0]

def ln_list(lang_name):
    """obtain list of locales for a given language name, for example: English -> en_US, en_GB"""
    return LDICT[unicode(lang_name)]

def get_native_langs(lang_list):
    """assemble dictionary of native language names with language codes"""
    langs_dict = {}
    for l in lang_list:
        lang =  Locale(l).getDisplayLanguage(Locale(l)).title()
        try:
            langs_dict[lang]
        except:
            langs_dict[lang] = []
        if l not in langs_dict[lang]:
            langs_dict[lang].append(l)
    return langs_dict

try:
# Note that we always collate with the 'C' locale.  This is far
# from ideal.  But proper collation always requires a specific
# language for its collation rules (languages frequently have
# custom sorting).  This at least gives us common sorting rules,
# like stripping accents.
    collator = Collator.createInstance(Locale('C'))
except:
    collator = None

def compare_choice(x):
    """comparison function"""
    if collator:
        try:
            return collator.getCollationKey(x).getByteArray()
        except:
            return x

def get_texts(langs):
    """obtain texts for a given locale using gettext"""
    result = {}
    for k, l in langs.iteritems():
        loc = l[0].split('_')[0]
        try:
            result[str(loc)] = gettext.translation(DOMAIN, MOFILES, [str(loc)])
        except IOError:
            logging.error('Failed to get texts for %s locale', loc)
    return result

LDICT = get_native_langs(langcodes)
LANGS = sorted(LDICT.keys(), key=compare_choice)
TEXTS = get_texts(LDICT)

class iso639():
    """Utility class to convert iso639 2-letter into 3-letter language code"""
    test_country = None
    test_name = None
    found = False
    name_check = True
    lang_check = True
    display = None
    engine = None
    configreg = None
    triplets = []

    def __init__(self):
        """xklavier loader"""
        self.display = gtk.gdk.display_get_default()
        self.engine = xklavier.Engine(self.display)
        self.configreg = xklavier.ConfigRegistry(self.engine)
        self.configreg.load(False)

    def process_variant(self, c_reg, item, subitem):
        """internal comparison utility"""
        if self.lang_check:
            if item.get_name() == self.test_country: self.found = True
        else:
            if item.get_name() == self.test_name: self.found = True
    
    def process_language(self, c_reg, item):
        """internal search result processor"""
        c_reg.foreach_language_variant(item.get_name(), self.process_variant)
        if self.found:
            if self.name_check:
                if self.test_name == item.get_name()[:2]: self.triplets.append(item.get_name())
            else: self.triplets.append(item.get_name())
            self.found = False

    def search(self, lang):
        """search 2-letter language code"""
        self.test_country = lang.split('_')[1].lower()
        self.test_name = lang.split('_')[0]
        self.triplets = []
        self.configreg.foreach_language(self.process_language)
        return self.triplets

    def conv(self, bi):
        """conversion via cascade search"""
        res = self.search(bi)
        if 0 == len(res):
            self.name_check = False
            res = self.search(bi)
        if 0 == len(res):
            self.lang_check = False
            res = self.search(bi)
        if 0 == len(res): return None
        return res[0]

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

