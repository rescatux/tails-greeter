#!/usr/bin/python
#
# Copyright 2012-2013 Tails developers <tails@boum.org>
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
"""Camouflage handling

"""
import os
import logging
import pipes

import tailsgreeter.config

class CamouflageSettings(object):
    """Model storing settings related to camouflage

    """
    def __init__(self):
        # Which OS to impersonate
        self.os = None
        # XXX: this should read the content of the setting file

    @property
    def os(self):
        return self._os

    @os.setter
    def os(self, new_os):
        camouflage_settings_file = tailsgreeter.config.camouflage_settings
        self._os = new_os
        if new_os:
            with open(camouflage_settings_file, 'w') as f:
                os.chmod(camouflage_settings_file, 0o600)
                f.write('TAILS_CAMOUFLAGE_OS=%s\n' % pipes.quote(self.os))
                logging.debug('camouflage setting written to %s',
                              camouflage_settings_file)
        else:
            try:
                os.unlink(camouflage_settings_file)
                logging.debug('removed %s', camouflage_settings_file)
            except OSError:
                # configuration file does not exist
                pass
