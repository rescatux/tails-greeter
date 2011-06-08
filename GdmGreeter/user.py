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
Control the user configuration.
"""

import sys, os
import logging
import json

USER_CONFIG = '/home/users/%s.user'

class User(object):
    """Reprisent User Data"""
    def __init__(self, username, data=None):
        self._data = None
        self.user = username
        self.access = None
        self.update(data)

    @property
    def filename(self):
        """Return the configuration filename"""
        return USER_CONFIG % self.user.replace('/', '-')

    @property
    def last_modified(self):
        """Return the last modified time"""
        return os.path.getmtime(self.filename)

    @property
    def last_accessed(self):
        """Return the last time I accessed the file"""
        return self.access

    @property
    def data(self):
        """Return all the current data for the user"""
        if not self._data:
            self._data = self.load()
        return self._data

    def update(self, data):
        """Update some of the data for the user"""
        if data != None:
            self.data.update(data)

    def load(self):
        """Load method, returns hash of filename"""
        if os.path.exists(self.filename):
            with open(self.filename) as fhl:
                try:
                    self.access = os.path.getatime(self.filename)
                    return json.loads(fhl.read())
                except ValueError:
                    pass
        return { 'username': self.user }

    def get(self, name, default):
        return self.data.get(name, default)

    def save(self, data=None):
        """Saves data to filename, can also update data."""
        self.update(data)
        with open(self.filename, 'w') as fhl:
            fhl.write(json.dumps(self.data, indent=2))
            self.access = self.last_modified

