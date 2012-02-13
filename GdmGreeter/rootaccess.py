#!/usr/bin/python
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
"""Root access handeling

"""
import os
import logging
import pipes

import GdmGreeter.config

class RootAccessSettings(object):
    """Model storing settings related to root access

    """
    def __init__(self):
        # Root password
        self.password = None

    def __del__(self):
        if self.password:
            with open(GdmGreeter.config.rootpassword_path, 'w') as f:
                os.chmod(GdmGreeter.config.rootpassword_path, 0o600)
                f.write('TAILS_USER_PASSWORD=%s\n' % pipes.quote(self.password))
                logging.debug('password written to %s', GdmGreeter.config.rootpassword_path)

