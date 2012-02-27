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
"""Persistence handling

"""
import logging
import subprocess

import gettext
_ = gettext.gettext

import GdmGreeter
import GdmGreeter.config
import GdmGreeter.errors
from GdmGreeter.utils import unicode_to_utf8

class PersistenceSettings(object):
    """Model storing settings related to persistence

    """
    def __init__(self):
        pass

    def list_containers(self):
         """Returns a list of persistence containers we might want to unlock."""
         proc = subprocess.Popen(
             [
                 "/usr/bin/sudo", "-n", "/usr/local/sbin/live-persist",
                 "--encryption=luks", "--media=removable",
                 "list", "TailsData"
             ],
             stdout=subprocess.PIPE,
             stderr=subprocess.PIPE
             )
         out, err = proc.communicate()
         out = unicode_to_utf8(out)
         err = unicode_to_utf8(err)
         if proc.returncode:
             raise GdmGreeter.errors.LivePersistError(
                 _("live-persist failed with return code %(returncode)s:\n%(stderr)s")
                 % { 'returncode': proc.returncode, 'stderr': err }
                 )
         containers = str.splilinest(out)
         logging.debug("found containers: %s", containers)
         return containers

    def activate(self, volume, password, readonly):
        # XXX: To be implemented
        # Might throw WrongPassphraseError or some other kind of LivePersistError
        logging.debug("passphrase: %s", password)
        args = []
        if readonly:
            options.append('--read-only')
        else:
            options.append('--read-write')
        args.append('activate')
        args.append(volume)
        # /usr/bin/sudo -n /usr/local/sbin/live-persist activate args
        pass

