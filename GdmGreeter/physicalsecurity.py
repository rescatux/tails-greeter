#!/usr/bin/python
#
# Copyright 2013 Tails developers <tails@boum.org>
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
"""Physical security settings

"""
import os
import logging
import pipes

import GdmGreeter.config

class PhysicalSecuritySettings(object):
    """Model storing settings related to physical security

    """
    def __init__(self):
        # Whether to run macspoof
        self._macspoof = not self.inside_virtual_machine()
        self.write_settings()

    def write_settings(self):
        physical_security_settings_file = GdmGreeter.config.physical_security_settings
        with open(physical_security_settings_file, 'w') as f:
            os.chmod(physical_security_settings_file, 0o600)
            f.write('TAILS_MACSPOOF_ENABLED={0}\n'.format(
                    pipes.quote(str(self.macspoof).lower())))
            logging.debug('physical security settings written to %s',
                          physical_security_settings_file)

    @property
    def macspoof(self):
        return self._macspoof

    @macspoof.setter
    def macspoof(self, new_state):
        self._macspoof = new_state
        self.write_settings()

    @staticmethod
    def inside_virtual_machine():
        with open('/var/lib/live/detected-virtual-machine', 'r') as f:
            return any(x.strip() != "" for x in f.read())
        return False
