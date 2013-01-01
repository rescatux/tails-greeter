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
import os
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
                "--log-file=/var/log/live-persist",
                "--encryption=luks",
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
        containers = str.splitlines(out)
        logging.debug("found containers: %s", containers)
        return containers

    def activate(self, device, password, readonly):
        cleartext_device = self.unlock_device(device, password)
        logging.debug("unlocked cleartext_device: %s", cleartext_device)
        self.setup_persistence(cleartext_device, readonly)
        with open(GdmGreeter.config.persistence_state_file, 'w') as f:
            os.chmod(GdmGreeter.config.persistence_state_file, 0o600)
            f.write('TAILS_PERSISTENCE_ENABLED=true\n')
            if readonly:
                f.write('TAILS_PERSISTENCE_READONLY=true\n')

    def unlock_device(self, device, password):
        """Unlock the LUKS persistent device"""
        cleartext_name = str.rsplit(device, '/', 1)[-1] + '_unlocked'
        cleartext_device = '/dev/mapper/' + cleartext_name
        if not os.path.exists(cleartext_device):
            args = [
                "/usr/bin/sudo", "-n",
                "/sbin/cryptsetup", "luksOpen",
                "--tries", "1",
                device, cleartext_name
                ]
            proc = subprocess.Popen(
                args, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            out, err = proc.communicate(password + "\n")
            out = unicode_to_utf8(out)
            err = unicode_to_utf8(err)
            if proc.returncode:
                logging.debug(
                    "cryptsetup failed with return code %(returncode)s:\n%(stdout)s\n%(stderr)s"
                    % { 'returncode': proc.returncode, 'stdout': out, 'stderr': err })
                raise GdmGreeter.errors.WrongPassphraseError(
                    _("cryptsetup failed with return code %(returncode)s:\n%(stdout)s\n%(stderr)s")
                    % { 'returncode': proc.returncode, 'stdout': out, 'stderr': err }
                    )
            logging.debug("crytpsetup success")
        return cleartext_device

    def setup_persistence(self, cleartext_device, readonly):
        args = [ "/usr/bin/sudo", "-n", "/usr/local/sbin/live-persist" ]
        if readonly:
            args.append('--read-only')
        else:
            args.append('--read-write')
        args.append('--log-file=/var/log/live-persist')
        args.append('activate')
        args.append(cleartext_device)
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
        out, err = proc.communicate()
        out = unicode_to_utf8(out)
        err = unicode_to_utf8(err)
        if proc.returncode:
            raise GdmGreeter.errors.LivePersistError(
                _("live-persist failed with return code %(returncode)s:\n%(stdout)s\n%(stderr)s")
                % { 'returncode': proc.returncode, 'stdout': out, 'stderr': err }
                )
