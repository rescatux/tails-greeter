#!/usr/bin/python
#
# Copyright 2012 Tails developers <tails@boum.org>
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

import GdmGreeter.config

class CamouflageSettings(object):
    """Model storing settings related to camouflage

    """
    def __init__(self):
        # Which OS to impersonate
        self.os = None

    def __del__(self):
        camouflage_settings_file = GdmGreeter.config.camouflage_settings
        if self.os:
            with open(camouflage_settings_file, 'w') as f:
                os.chmod(camouflage_settings_file, 0o600)
                f.write('TAILS_CAMOUFLAGE_OS=%s\n' % pipes.quote(self.os))
                logging.debug('camouflage setting written to %s',
                              camouflage_settings_file)
