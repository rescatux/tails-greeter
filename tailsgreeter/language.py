#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Tails developers <tails@boum.org>
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
"""Localization handling

"""

import logging
import gettext
import os
import locale

import pycountry
import icu

from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import Gtk
from gi.repository import Xkl
from gi.repository import AccountsService

import tailsgreeter.config

def xkl_strip(string):
    """Clean strings returned by Xkl

    Strings returned by Xkl are fixed length and contains null chars.
    The part we want is the beginning, before the 1st null char.
    This method cleans up this kind of strings."""
    return string.split("\x00", 1)[0]

def ln_iso639_tri(ln_CC):
    """get iso639 3-letter code
    
    example: en_US -> eng"""
    return icu.Locale(ln_CC).getISO3Language()

def ln_iso639_2_T_to_B(ln_CC):
    """Convert a ISO-639-2/T code (e.g. deu for German) to a 639-2/B one (e.g. ger for German)"""
    return pycountry.languages.get(terminology=ln_CC).bibliographic

def __fill_layouts_dict():
    """assemble dictionary of layout codes to corresponding layout name
    
    """
    _xkl_engine = Xkl.Engine.get_instance(GdkX11.x11_get_default_xdisplay())
    _xkl_registry = Xkl.ConfigRegistry.get_instance(_xkl_engine)
    _xkl_registry.load(False)

    layouts_dict = {}

    def variant_iter(registry, variant, layout):
        code = '%s/%s' % (xkl_strip(layout.name),
                          xkl_strip(variant.name))
        description = '%s - %s' % (xkl_strip(layout.description),
                                   xkl_strip(variant.description))
        if code not in layouts_dict:
            layouts_dict[code] = description

    def layout_iter(registry, layout, _):
        code = xkl_strip(layout.name)
        description = xkl_strip(layout.description)
        if code not in layouts_dict:
            layouts_dict[code] = description
        _xkl_registry.foreach_layout_variant(code, variant_iter, layout)

    _xkl_registry.foreach_layout(layout_iter, None)
    return layouts_dict

def language_from_locale(locale):
    """Obtain the language code from a locale code

    example: fr_FR -> fr"""
    return locale.split('_')[0]

def languages_from_locales(locales):
    """Obtain a language code list from a locale code list

    example: [fr_FR, en_GB] -> [fr, en]"""
    language_codes = []
    for l in locales:
        language_code = language_from_locale(l)
        if not language_code in language_codes:
            language_codes.append(language_code)
    return language_codes

def country_from_locale(locale):
    """Obtain the country code from a locale code

    example: fr_FR -> FR"""
    return locale.split('_')[1]

def countries_from_locales(locales):
    """Obtain a country code list from a locale code list

    example: [fr_FR, en_GB] -> [FR, GB]"""
    country_codes = []
    for l in locales:
        country_code = country_from_locale(l)
        if not country_code in country_codes:
            country_codes.append(country_code)
    return country_codes

def language_name(language_code):
    return icu.Locale(language_code).getDisplayLanguage(icu.Locale(language_code)).title()

def country_name(locale_code):
    return icu.Locale(locale_code).getDisplayCountry(icu.Locale(locale_code))

def layout_name(layout_code):
    if layout_code in _system_layouts_dict:
        return _system_layouts_dict[layout_code]

def sort_by_name(list, locale='C'):
    try:
        # Note that we always collate with the 'C' locale.  This is far
        # from ideal.  But proper collation always requires a specific
        # language for its collation rules (languages frequently have
        # custom sorting).  This at least gives us common sorting rules,
        # like stripping accents.
        collator = icu.Collator.createInstance(icu.Locale(locale))
    except:
        collator = None
    def compare_choice(elt):
        """comparison function"""
        if collator:
            try:
                return collator.getCollationKey(elt[1]).getByteArray()
            except: # Specify exception
                return elt[1]
    list.sort(key=compare_choice)
    return list

def languages_with_names(languages, locale='C'):
    languages_with_names = [(l, language_name(l)) for l in languages]
    sort_by_name(languages_with_names, locale)
    return languages_with_names
 
def locales_with_names(locales, locale='C'):
    locales_with_names = [(l, country_name(l)) for l in locales]
    sort_by_name(locales_with_names, locale)
    return locales_with_names

def layouts_with_names(layouts, locale='C'):
    layouts_with_names = [(l, layout_name(l)) for l in layouts]
    sort_by_name(layouts_with_names, locale)
    return layouts_with_names

def __get_langcodes():
    with open(tailsgreeter.config.default_langcodes_path, 'r') as f:
        defcodes = [ line.rstrip('\n') for line in f.readlines() ]
    with open(tailsgreeter.config.language_codes_path, 'r') as f:
        langcodes = [ line.rstrip('\n') for line in f.readlines() ]
    logging.debug('%s languages found', len(langcodes))
    return defcodes + langcodes

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
            if isinstance(child, Gtk.Container):
                self.store_translations(child)
            if isinstance(child, Gtk.Label):
                self.labels.append( (child, child.get_label()) )
            if child.get_has_tooltip():
                self.tips.append( (child, child.get_tooltip_text()) )

    def gettext(self, lang, text):
        """Return a translated string or string"""
        if lang:
            text = lang.gettext(text)
        return text

    def translate_to(self, lang):
        """Loop through everything and translate on the fly"""
        try:
            lang = gettext.translation(tailsgreeter.__appname__, tailsgreeter.config.locales_path, [str(lang)])
        except IOError:
            lang = None

        for (child, text) in self.labels:
            child.set_label(self.gettext(lang, text))
        for (child, text) in self.tips:
            child.set_tooltip_markup(self.gettext(lang, text))
        if self.window.get_sensitive() and self.window.get_visible() and self.retain_focus:
            self.window.present()

class LocalisationSettings(object):
    """Model storing settings related to language and keyboard

    """
    def __init__(self, usermanager_loaded_cb=None, locale_selected_cb=None):
        self._usermanager_loaded_cb = usermanager_loaded_cb
        self._locale_selected_cb = locale_selected_cb

        self.__act_user = None
        self.__actusermanager_loadedid = None

        self._xkl_engine = Xkl.Engine.get_instance(GdkX11.x11_get_default_xdisplay())
        self._xkl_registry = Xkl.ConfigRegistry.get_instance(self._xkl_engine)
        self._xkl_registry.load(False)
        self._xkl_record = Xkl.ConfigRec()
        self._xkl_record.get_from_server(self._xkl_engine)

        self._system_locales_list = _langcodes
        self._system_locales_dict = self.__fill_locales_dict(self._system_locales_list)

        self._language = 'en'
        self._locale = 'en_US'
        self._layout = 'us'
        self._variant = ''
        self._options = 'grp:alt_shift_toggle'

        actusermanager = AccountsService.UserManager.get_default()
        self.__actusermanager_loadedid = actusermanager.connect(
            "notify::is-loaded",  self.__on_usermanager_loaded)

    def __del__(self):
        if self.__actusermanager_loadedid:
            self.__actusermanager.disconnect(self.__actusermanager_loadedid)

    def __on_usermanager_loaded(self, manager, pspec, data=None):
        logging.debug("Received AccountsManager signal is-loaded")
        act_user = manager.get_user(tailsgreeter.config.LUSER)
        if not act_user.is_loaded():
            raise RuntimeError("User manager for %s not loaded" % tailsgreeter.config.LUSER)
        self.__act_user = act_user
        if self._usermanager_loaded_cb:
            self._usermanager_loaded_cb()

    def __fill_locales_dict(self, locales):
        """assemble dictionary of language codes to corresponding locales list
        
        example {en: [en_US, en_GB], ...}"""
        locales_dict = {}
        for locale in locales:
            # English = icu.Locale(en_GB)...
            lang = language_from_locale(locale)
            if lang not in locales_dict:
                locales_dict[lang] = []
            if locale not in locales_dict[lang]:
                locales_dict[lang].append(locale)
        return locales_dict

    def __apply_layout_to_upcoming_session(self):
        variant = ''
        if self._layout != 'us':
            layout = 'us,%s' % self._layout
            if self._variant:
                variant = '%s,' % self._variant
        else:
            layout = self._layout
            variant = self._variant
        with open(tailsgreeter.config.locale_output_path, 'w') as f:
            os.chmod(tailsgreeter.config.locale_output_path, 0o600)
            f.write('TAILS_LOCALE_NAME=%s\n' % self._locale)
            f.write('TAILS_XKBMODEL=%s\n' % 'pc105') # use default value from /etc/default/keyboard
            f.write('TAILS_XKBLAYOUT=%s\n' % layout)
            f.write('TAILS_XKBVARIANT=%s\n' % variant)
            f.write('TAILS_XKBOPTIONS=%s\n' % self._options)

    # LANGUAGES

    def get_languages(self):
        """Return a list of available languages codes

        """
        return languages_from_locales(self._system_locales_list)

    def get_languages_with_names(self):
        return languages_with_names(self.get_languages(), self.get_locale())

    def get_default_languages(self):
        """Return a list of default languages codes

        """
        return languages_from_locales(tailsgreeter.config.default_locales)

    def get_default_languages_with_names(self):
        return languages_with_names(self.get_default_languages(), self.get_locale())

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

    def get_default_locales_with_names(self):
        return locales_with_names(self.get_default_locales(), self.get_locale())

    def get_locale(self):
        return self._locale

    def set_locale(self, locale):
        self._locale = locale
        self.__apply_locale()
        self.__set_default_layout()
        if self._locale_selected_cb:
            self._locale_selected_cb(locale)

    def __set_default_locale(self):
        """Set default locale for current language

        Select locale whose country code corresponds to language code. If none,
        select first locale.
        """
        default_locale = None
        default_locales = self.get_default_locales()
        logging.debug("default_locales = %s" % default_locales)
        if default_locales:
            default_locale = default_locales[0]
        else:
            default_locale = 'en_US'
        logging.debug("setting default locale to %s" % default_locale)
        self.set_locale(default_locale)

    def __apply_locale(self):
        locale_code = locale.normalize(
            self._locale + '.' + locale.getpreferredencoding())
        logging.debug("Setting session language to %s", locale_code)

        if self.__act_user:
            GLib.idle_add(lambda:
                self.__act_user.set_language(locale_code))
        else:
            logging.warning("AccountsManager not ready")

    # LAYOUTS

    def get_layouts(self):
        """Return a list of all available keyboard layout codes

        """
        layouts = _system_layouts_dict.keys()
        return layouts

    def get_layouts_with_names(self):
        return layouts_with_names(self.get_layouts(), self.get_locale())

    def layouts_for_language(self):
        """Return the list of available layouts for given language

        Query XKL and return layouts for a given language.
        """
        layouts = []
        t_code = ln_iso639_tri(self._language)
        if t_code == 'nno' or t_code == 'nob':
            t_code = 'nor'
        if t_code == 'hrv':
            layouts.append('hr')

        def language_iter(config_registry, item, subitem, store):
            layout_code = xkl_strip(item.name)
            if layout_code not in layouts:
                layouts.append(layout_code)

        self._xkl_registry.foreach_language_variant(t_code,
                                                    language_iter,
                                                    layouts)
        if len(layouts) == 0:
            b_code = ln_iso639_2_T_to_B(t_code)
            logging.debug(
                'got no layout for ISO-639-2/T code %s, trying with ISO-639-2/B code %s',
                t_code, b_code)
            self._xkl_registry.foreach_language_variant(b_code,
                                                        language_iter,
                                                        layouts)

        logging.debug('got %d layouts for %s', len(layouts), self._language)
        return layouts

    def get_default_layouts(self):
        """Return list of supported keyboard layouts for current language
        
        """

        layouts = self.layouts_for_language()
        if not layouts:
            layouts = ['us']
        return layouts

    def get_default_layouts_with_names(self):
        return layouts_with_names(self.get_default_layouts(), self.get_locale())

    def get_layout(self):
        return self._layout

    def set_layout(self, layout):
        try:
            layout, variant = layout.split('/')
        except ValueError:
            layout = layout
            variant = ''
        self._layout = layout
        self._variant = variant
        self.__apply_layout_to_current_screen()
        self.__apply_layout_to_upcoming_session()

    def __set_default_layout(self):
        default_layout = False
        backup_layout = False
        default_layouts = self.get_default_layouts()
        for layout_code in default_layouts:
            ln=language_from_locale(self._locale).lower()
            country=country_from_locale(self._locale).lower()
            logging.debug("layout_code='%s', ln='%s', CC='%s'",
                layout_code, ln, country)
            if country == layout_code:
                logging.debug("Default layout is %s", layout_code)
                default_layout = layout_code
            elif ln == layout_code:
                logging.debug("Backup layout is %s", layout_code)
                backup_layout = layout_code
        if not default_layout:
            logging.debug("No default layout")
            if backup_layout:
                logging.debug("Using backup layout")
                default_layout = backup_layout
            elif len(default_layouts) > 0:
                default_layout = self.get_default_layouts()[0]
                logging.debug("Using %s as default layout", default_layout)
            else:
                default_layout = 'us'
                logging.debug("Using us as default layout")
        self.set_layout(default_layout)            

    def __apply_layout_to_current_screen(self):
        logging.debug("layout=%s" % self._layout)

        if self._layout != 'us':
            layout_list = ['us', self._layout]
            variant_list = ['', self._variant]
        else:
            layout_list = [self._layout]
            variant_list = [self._variant]

        self._xkl_record.set_layouts(layout_list)
        self._xkl_record.set_variants(variant_list)
        # 'grp:sclk_toggle' would be much more convenient but we default to
        # mustdie switcher in here
        self._xkl_record.set_options([self._options])
        self._xkl_record.activate(self._xkl_engine)
        # try to 'enforce layout'
        self._xkl_engine.start_listen(Xkl.EngineListenModes.TRACK_KEYBOARD_STATE)
        self._xkl_engine.lock_group(1)
        self._xkl_engine.stop_listen(Xkl.EngineListenModes.TRACK_KEYBOARD_STATE)

        logging.debug('L:%s V:%s O:%s',
                       self._xkl_record.layouts,
                       self._xkl_record.variants,
                       self._xkl_record.options)

# MODULE INITIALISATION

# List of system locale codes
_langcodes = __get_langcodes()

# dictionary of layout codes: layout name
_system_layouts_dict = __fill_layouts_dict()
