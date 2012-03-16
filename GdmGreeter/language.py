#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Tails developers <tails@boum.org>
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

import logging, gettext, gtk, pycountry
import xklavier

from subprocess import Popen, PIPE
from icu import Locale, Collator

import GdmGreeter.config


def ln_cc(lang_name):
    """obtain language code from name, for example: English -> en_US"""
    return LDICT[unicode(lang_name)][0]

def ln_list(lang_name):
    """obtain list of locales for a given language name, for example: English -> en_US, en_GB"""
    return LDICT[unicode(lang_name)]

def ln_country(ln_CC):
    """get country name for locale: en_US -> USA"""
    return Locale(ln_CC).getDisplayCountry(Locale(ln_CC))

def ln_iso639_tri(ln_CC):
    """get iso639 3-letter code: en_US -> eng"""
    return Locale(ln_CC).getISO3Language()

def ln_iso639_2_T_to_B(ln_CC):
    """Convert a ISO-639-2/T code (e.g. deu for German) to a 639-2/B one (e.g. ger for German)"""
    return pycountry.languages.get(terminology=ln_CC).bibliographic

def get_native_langs(lang_list):
    """assemble dictionary of native language names with language codes"""
    langs_dict = {}
    for l in lang_list:
        # English = Locale(en_GB)...
        lang =  Locale(l).getDisplayLanguage(Locale(l)).title()
        try:
            langs_dict[lang]
        except: #XXX specify exception
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
        except: # Specify exception
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

MOFILES = '/usr/share/locale/'
DOMAIN  = 'tails-greeter'

p = Popen(["tails-lang-helper"], stdout=PIPE)
langcodes = str.split(p.communicate()[0])
logging.debug('%s languages found: helper returned %s', len(langcodes), p.returncode)

LDICT = get_native_langs(langcodes)
LANGS = sorted(LDICT.keys(), key=compare_choice)
DEFAULT_LANGS = get_native_langs(
        ["ar_EG", "zh_CN", "en_US", "fa_IR", "fr_FR",
         "de_DE", "it", "pt", "ru", "es", "vi_VN"])
TEXTS = get_texts(LDICT)

class TranslatableWindow(object):
    """Interface providing functions to translate a window on the fly
    """
    retain_focus = True

    def __init__(self, window):
        self.window = window
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
        if self.window.get_sensitive() and self.window.get_visible() and self.retain_focus:
            self.window.present()

# =====================

class LanguageSettings(object):
    """Model storing settings related to language and keyboard

    """

    def __init__(self, greeter):
        self.greeter = greeter

        # Initialize instance variables
        self.lang3 = None
        self.options = 'grp:alt_shift_toggle' # 'grp:sclk_toggle' would be much more convenient but we default to mustdie switcher in here
        self.variant_list = None
        self.layout_list = None
        self.locales = {}
        self.default_layouts = {}
        self.engine = xklavier.Engine(gtk.gdk.display_get_default())
        self.configreg = xklavier.ConfigRegistry(self.engine)
        self.configreg.load(False)
        self.crecord = xklavier.ConfigRec()
        self.crecord.get_from_server(self.engine)
 
        # Attrubutes
        self.language = "English" #XXX
        self.locale = "en_US" #XXX
        self.layout = "us" #XXX
        self.variant = None


    # Language

    def get_languages(self):
        return LANGS

    def get_default_languages(self):
        return DEFAULT_LANGS

    def get_language(self):
        return self.language

    def set_language(self, language):
        self.language = language
        self.set_locales()

    def set_locales(self):
        """Set locales for current language
        
        """
        for l in ln_list(self.language):
            self.locales[unicode(ln_country(l))] = l
            if l == 'en_US' or l.split('_')[0] == l.split('_')[1].lower():
                self.set_locale(ln_country(l))

    #language = property(get_language, set_language)

    # Locales

    def get_locales(self):
        return ln_country

    def get_locales_for_language(self, language):
        default_locales = []
        count = 0
        for l in ln_list(language):
            default_locales.append(ln_country(l))
            # XXX
            #self.locales[unicode(ln_country(l))] = l
        return default_locales

    def get_default_locales(self):
        return self.get_locales_for_language(self.get_language())

    def get_locale(self):
        return self.locale

    def set_locale(self, locale):
        assert locale
        self.locale = locale
        language_code = self.locales[unicode(locale)]
        if language_code:
            self.variant = None
            self.greeter.SelectLanguage(language_code)
            self.set_layouts()

    #locale = property(get_locale, set_locale)

    def set_layouts(self):
        """Set default layouts for current locale
        
        XXX: also select and apply default, to split"""

        locale = self.locales[unicode(self.locale)]
        lang3 = ln_iso639_tri(locale)
        if lang3:
            self.default_layouts.clear()
            layouts = self.get_layouts_for_language(lang3)
            count = 0
            default = 0
            backup = 0
            use_default = 0
            for l in layouts:
                layout_name = l.split(')')[0].split('(')[1]
                layout_code = l.split()[0]
                # Unfortunately XklConfigItem's xkl_get_country_name is not part
                # of the Python bindings, so we have to hack our way through
                # another way. Moreover, layout codes don't easily map to country
                # codes: layout code "be" is for Belgium, while country code "be"
                # is for Бельгія, so we cannot use ICU to get the country code
                # from the layout code. Hence, just display the English layout
                # names until we find a better solution.
                self.default_layouts[layout_name] = layout_code
                if locale.split('_')[1].lower() == layout_code:
                    default = layout_code
                    use_default = 1
                if locale.split('_')[0].lower() == layout_code:
                    backup = layout_code
                count += 1
            if use_default:
                self.layout = default
            else:
                self.layout = backup
            self.variant = None
        else:
            self.default_layouts['USA'] = 'us'
        self.apply_layout()

    # Layouts

    def get_layouts(self):
        return self.default_layouts.keys()

    def get_layouts_for_language(self, language):
        """Return list of supported keyboard layouts for a given language"""
        t_code = language
        layouts = []

        def process_language(config_registry, item, subitem, store):
            """add layout to the store"""
            layout = item.get_name()
            #if 'eng' == self.lang3 or 'us' != layout:
            name = '%s (%s)' % (layout, item.get_description())
            if name not in store: store.append(name)

        self.configreg.foreach_language_variant(t_code, layouts)
        if len(layouts) == 0:
            b_code = ln_iso639_2_T_to_B(t_code)
            logging.debug(
                'got no layout for ISO-639-2/T code %s, trying with ISO-639-2/B code %s',
                t_code, b_code)
            self.configreg.foreach_language_variant(b_code, layouts)

        self.configreg.foreach_language_variant(language, process_language, layouts)
        layouts.sort()
        logging.debug('got %d layouts for %s', len(layouts), language)
        return layouts

    def apply_layout(self, layout):
        """populate the lists for a given layout"""
        self.variant_list = []
        self.layout_list = []
        if self.variant and self.variant != 'Default': self.variant_list = ['', self.variant]
        else: self.variant_list = ['']
        if len(self.variant_list) > 1 or layout != 'us': self.layout_list = ['us', layout]
        else: self.layout_list = ['us']
        self.crecord.set_variants(self.variant_list)
        self.crecord.set_layouts(self.layout_list)
        self.crecord.set_options([self.options])
        self.crecord.activate(self.engine)
        logging.debug('L:%s V:%s O:%s', self.crecord.get_layouts(), self.crecord.get_variants(), self.crecord.get_options())

    def get_default_layouts(self):
        return self.default_layouts.keys()

    def get_layout(self):
        # Reverse lookup
        revdict = dict((v,k) for k,v in self.default_layouts.items())
        return revdict[self.layout]

    def set_layout(self, layout):
        self.layout = self.default_layouts[layout]
        if self.layout:
            self.variant = None
            self.apply_layout(self.layout)
            self.greeter.SelectLayout(self.layout)
            self.switch_layout()
        #self._layout = layout

    #layout = property(get_layout, set_layout)

    def switch_layout(self):
        """enforce layout"""
        if self.variant != 'Default':
            self.engine.start_listen(xklavier.XKLL_TRACK_KEYBOARD_STATE)
            self.engine.lock_group(1)
            self.engine.stop_listen(xklavier.XKLL_TRACK_KEYBOARD_STATE)

    # Variants

    def process_layout(self, config_registry, item, store):
        """add variant to the store"""
        name = '%s (%s)' % (item.get_name(), item.get_description())
        if name not in store: store.append(name)

    def get_variants_for_layout(self, layout):
        """Return list of supported keyboard layout variants for a given layout"""
        variants = []
        self.configreg.foreach_layout_variant(layout, self.process_layout, variants)
        variants.sort()
        logging.debug('got %d variants for layout %s', len(variants), layout)
        return variants


