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
import icu

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

def __fill_layouts_dict():
    """assemble dictionary of layout codes to corresponding layout name
    
    We need this dictionnary to get the 'description' (human readeable name)
    of the layout.
    
    Instead of storing correspondance in this dictionnary, we should be able
    to query xklavier with the following code, but it fails because
    `Xkl.ConfigItem.set_name` doesn't exist in python bindings:
    
        _xkl_engine = xklavier.Engine(gtk.gdk.display_get_default())
        _xkl_registry = xklavier.ConfigRegistry(_xkl_engine)
        _xkl_registry.load(False)
        layout_config_item = xklavier.ConfigItem()
        layout_config_item.set_name(layout_code)
        if _xkl_registry.find_layout(layout_config_item):
        return layout_config_item.get_description()
    """
    _xkl_engine = xklavier.Engine(gtk.gdk.display_get_default())
    _xkl_registry = xklavier.ConfigRegistry(_xkl_engine)
    _xkl_registry.load(False)

    layouts_dict = {}

    def layout_iter(registry, item, layouts):
        layout_code = item.get_name()
        if layout_code not in layouts:
            layouts_dict[layout_code] = item.get_description()

    _xkl_registry.foreach_layout(layout_iter, layouts_dict)
    return layouts_dict

_system_layouts_dict = __fill_layouts_dict()

def language_from_locale(locale):
    return locale.split('_')[0]

def languages_from_locales(locales):
    language_codes = []
    for l in locales:
        language_code = language_from_locale(l)
        if not language_code in language_codes:
            language_codes.append(language_code)
    language_codes.sort()
    return language_codes

def country_from_locale(locale):
    return locale.split('_')[1]

def countries_from_locales(locales):
    country_codes = []
    for l in locales:
        country_code = country_from_locale(l)
        if not country_code in country_codes:
            country_codes.append(country_code)
    country_codes.sort()
    return country_codes

def language_name(language_code):
    return icu.Locale(language_code).getDisplayLanguage(Locale(language_code)).title()

def country_name(locale_code):
    return icu.Locale(locale_code).getDisplayCountry(Locale(locale_code))

def layout_name(layout_code):
    if layout_code in _system_layouts_dict:
        return _system_layouts_dict[layout_code]
     
class LocalisationSettings(object):
    """Model storing settings related to language and keyboard

    """
    def __init__(self, greeter):
        self._greeter = greeter

        self._xkl_engine = xklavier.Engine(gtk.gdk.display_get_default())
        self._xkl_registry = xklavier.ConfigRegistry(self._xkl_engine)
        self._xkl_registry.load(False)
        self._xkl_record = xklavier.ConfigRec()
        self._xkl_record.get_from_server(self._xkl_engine)

        self._system_locales_list = langcodes
        self._system_locales_dict = self.__fill_locales_dict(self._system_locales_list)

        self._language = 'en'
        self._locale = 'en_US'
        self._layout = 'us'

    def __fill_locales_dict(self, locales):
        """assemble dictionary of language codes to corresponding locales list
        
        example {en: [en_US, en_GB], ...}"""
        locales_dict = {}
        for locale in locales:
            # English = Locale(en_GB)...
            lang = language_from_locale(locale)
            if lang not in locales_dict:
                locales_dict[lang] = []
            if locale not in locales_dict[lang]:
                locales_dict[lang].append(locale)
        return locales_dict


    # LANGUAGES

    def get_languages(self):
        """Return a list of available languages codes

        """
        return languages_from_locales(self._system_locales_list)

    def get_default_languages(self):
        """Return a list of default languages codes

        """
        return languages_from_locales(GdmGreeter.config.default_locales)

    def get_language(self):
        """Return current language code

        """
        return self._language

    def set_language(self, language):
        self._language = language
        self.__set_default_locale()

    # LOCALES

    def get_locales(self):
        """Return a list of all available locale codes

        XXX: not useful? impossible to set country w/o corresponding language
        """
        return self._system_locales_list

    def get_default_locales(self):
        """Return available locales for current language

        """
        lang = self._language
        if lang in self._system_locales_dict:
            return self._system_locales_dict[lang]

    def get_locale(self):
        return self._locale

    def set_locale(self, locale):
        self.__apply_locale()
        self._locale = locale
        self.__set_default_layout()

    def __set_default_locale(self):
        """Set default locale for current language

        Select locale whose country code corresponds to language code. If none,
        select first locale.
        """
        default_locale = None
        for locale in self.get_default_locales():
            if ((locale == 'en_US')
                or (language_from_locale(locale).lower() ==
                    country_from_locale(locale).lower())):
                default_locale = locale
        if not default_locale:
            default_locale = self.get_default_locales()[0]
        self.set_locale(default_locale)

    def __apply_locale(self):
        self._greeter.SelectLanguage(self._locale)

    # LAYOUTS

    def get_layouts(self):
        """Return a list of all available keyboard layout codes

        """
        layouts = _system_layouts_dict.keys()
        layouts.sort()
        return layouts

    def get_default_layouts(self):
        """Return list of supported keyboard layouts for current language
        
        """
        layouts = []
        t_code = ln_iso639_tri(self._language)

        def language_iter(config_registry, item, subitem, store):
            layout_code = item.get_name()
            if layout_code not in layouts:
                layouts.append(item.get_name())

        self._xkl_registry.foreach_language_variant(t_code,
                                                    language_iter,
                                                    layouts)
        if len(layouts) == 0:
            b_code = ln_iso639_2_T_to_B(t_code)
            logging.debug(
                'got no layout for ISO-639-2/T code %s, trying with ISO-639-2/B code %s',
                t_code, b_code)
            self._xkl_registry.foreach_language_variant(b_code,
                                                        process_language,
                                                        layouts)
        layouts.sort()
        logging.debug('got %d layouts for %s', len(layouts), self._language)
        return layouts

    def get_layout(self):
        return self._layout

    def set_layout(self, layout):
        self._layout = layout
        self.__apply_layout()

    def __set_default_layout(self):
        default_layout = False
        backup_layout = False
        default_layouts = self.get_default_layouts()
        for layout_code in default_layouts:
            logging.debug("layout_code=%s, ln=%s, CC=%s" % 
                (layout_code,
                 language_from_locale(self._locale).lower(),
                 country_from_locale(self._locale).lower()))
            if language_from_locale(self._locale).lower() == layout_code:
                default_layout = layout_code
            elif country_from_locale(self._locale).lower() == layout_code:
                backup_layout = layout_code
        if not default_layout:
            if backup_layout:
                default_layout = backup_layout
            elif len(default_layouts) > 0:
                default_layout = self.get_default_layouts()[0]
            else:
                default_layout = 'us'
        self.set_layout(default_layout)            

    def __apply_layout(self):
        self.variant_list = []
        self.layout_list = []
        layout = self._layout

        self._xkl_record.set_layouts([layout])
        self._xkl_record.set_variants([''])
        # 'grp:sclk_toggle' would be much more convenient but we default to
        # mustdie switcher in here
        self._xkl_record.set_options(['grp:alt_shift_toggle'])
        self._xkl_record.activate(self._xkl_engine)

        logging.debug("layout=%s" % layout)
        logging.debug('L:%s V:%s O:%s',
                       self._xkl_record.get_layouts(),
                       self._xkl_record.get_variants(),
                       self._xkl_record.get_options())
