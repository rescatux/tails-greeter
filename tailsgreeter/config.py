#!/usr/bin/python
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

tails_specific = False # TODO: Depend on a runtime check

"""Tails-greeter configuration"""

# default Tails credentials
LPASSWORD = 'live'
if tails_specific:
    LUSER = 'amnesia'
else:
    LUSER = 'user'

# file where supported language codes (such as en_US) are saved at Tails build time
language_codes_path = '/usr/share/tails-greeter/language_codes'

# file where default language code for languages are saved at Tails build time
default_langcodes_path = '/usr/share/tails-greeter/default_langcodes'

# locales path
locales_path = '/usr/share/locale/'

# locales to display in main menu
default_locales = ["ar_EG", "zh_CN", "en_US", "fa_IR", "fr_FR",
                  "de_DE", "it", "pt", "ru", "es", "vi_VN"]

# file to store tails session locale settings
locale_output_path = '/var/lib/gdm3/tails.locale'

# file to store tails session sudo password to
rootpassword_output_path = '/var/lib/gdm3/tails.password'

# File where Tails persistence status is saved
persistence_state_file = '/var/lib/gdm3/tails.persistence'

# Stores which operating system camouflage to activate, if any
camouflage_settings = '/var/lib/gdm3/tails.camouflage'

# Stores settings related to physical security
physical_security_settings = '/var/lib/gdm3/tails.physical_security'
