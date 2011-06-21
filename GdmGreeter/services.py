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
Provides access to gdm services for python greeters (login windows).
"""

import os, time
import logging
import locale
import dbus
import dbus.bus
import dbus.exceptions
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
from GdmGreeter.user import User

PASSWD = '/etc/passwd'

class GdmDbusService(object):
    """Basic wrapper to create the correct interfaces and proxy signals"""
    def __init__(self):
        try:
            # The first is access to the object and any interfaces.
            self.raw = self.connection.get_object(self.address, self.path)
        except dbus.exceptions.DBusException:
            logging.error("Failed to get Dbus object %s", self.path)
            raise
        # The second is access to the interface, which is more interesting.
        self.obj = dbus.Interface(self.raw, self.interface)
        # Watch all signals on this interface
        self.connection.add_signal_receiver(self.got_signal,
            dbus_interface = self.interface, signal_name = None, bus_name = None, path = self.path,
            sender_keyword = "sent", destination_keyword = "dest", interface_keyword = None,
            member_keyword = "name", path_keyword = None, message_keyword = None
        )

    def got_signal(self, *args, **kwargs):
        """Log all signals and call the proxy method for it."""
        name = kwargs.pop('name', 'Unknown')
        # Call the object's signal proxy method
        if hasattr(self, name):
            getattr(self, name)( *args )
            log = logging.debug
        else:
            log = logging.warn
        # For debugging and for warnings.
        for key in kwargs.keys():
            if kwargs[key] == None:
                kwargs.pop(key)
        if kwargs:
            log( "%s:%s%s %s\n" % (
                self.interface, name, str(args), str(kwargs)) )
        else:
            log("%s:%s%s\n" % (self.interface, name, str(args)))


class GdmGreeter(GdmDbusService):
    path = '/org/gnome/DisplayManager/GreeterServer'
    address = 'org.gnome.DisplayManager.GreeterServer'
    interface = 'org.gnome.DisplayManager.GreeterServer'

    def __init__(self, *args, **kwargs):
        address = kwargs.pop('address', os.environ['GDM_GREETER_DBUS_ADDRESS'])
        try:
            self.connection = dbus.connection.Connection(address)
            logging.debug("Connected to Greeter-Service on %s", address)
        except dbus.exceptions.DBusException:
            logging.error("Failed to connect to Greeter-Service on %s", address)
            raise
        GdmDbusService.__init__(self)
        self.display = GdmDisplay(self.obj.GetDisplayId())

    def SelectLanguage(self, lang):
        """Call into GdmGreeter to change the language"""
        if '.' not in lang:
            lang += '.UTF8'
        lang = locale.normalize(lang).replace('UTF8', 'UTF-8')
        logging.debug("Setting language to %s", lang )
        self.obj.SelectLanguage(locale.normalize(lang))

    def Ready(self):
        """Called when greeter service is ready"""
        logging.debug("GdmServer is Ready")
        self.obj.BeginVerification()

    def InfoQuery(self, text):
        """Server wants to ask the user for something (username normally)"""
        raise NotImplementedError("You need to handle InfoQuery to ask for the username.")

    def SecretInfoQuery(self, text):
        """Server wants to ask for some secrate info (password normally)"""
        raise NotImplementedError("You need to handle SecretInfoQuery to ask for the password.")

    def UserAuthorized(self):
        """User is ready to go, lets get them in"""
        self.obj.StartSessionWhenReady( True )
        self.FinishProcess()

    def FinishProcess(self):
        """Called when we're logging into the client"""
        pass


class GdmDisplay(GdmDbusService):
    """Connect to the display bus"""
    address = 'org.gnome.DisplayManager'
    interface = 'org.gnome.DisplayManager.Display'

    def __init__(self, path):
        self.connection = dbus.SystemBus()
        self.path = path
        super(GdmDisplay, self).__init__()

    @property
    def name(self):
        return self.obj.GetX11DisplayName()

    @property
    def number(self):
        return self.obj.GetX11DisplayNumber()


class GdmUsers(GdmDbusService):
    """Connect to the display bus"""
    path = '/org/gnome/DisplayManager/UserManager'
    address = 'org.gnome.DisplayManager'
    interface = 'org.gnome.DisplayManager.UserManager'

    def __init__(self, added=None, removed=None):
        self.connection = dbus.SystemBus()
        self._users = [] # username list (iter)
        self._info = {}  # username -> info
        self._uids = {} # uid -> username
        self._names = {} # name -> username
        self.loaded = False
        self.refined = False
        self.event_added = added
        self.event_removed = removed
        super(GdmUsers, self).__init__()

    def __iter__(self):
        if not self.refined:
            self.load_users()
        for username in self._users:
            if self._info.has_key(str(username)):
                yield self._info[str(username)]

    def UsersLoaded(self):
        """When users have been loaded"""
        self.loaded = True

    def UserAdded(self, uid):
        """User has been added"""
        user = self.load_user(uid)
        if self.event_added:
            self.event_added(user)

    def UserRemoved(self, uid):
        """User has been removed"""
        # The uid we're given is complete bullshit, so for further
        # information we'll have to test for missing files.
        if uid in self._uids.keys():
            self.remove(self._uids[uid])
        else:
            # Do it the hard, manual way.
            with open(PASSWD, 'r') as fhl:
                passwd = fhl.read()
            for username in self._users:
                if '\n' + username not in passwd:
                    self.remove(username)

    def remove(self, username):
        """Remove a user from the data structures"""
        self._users.remove(username)
        user = self._info.pop(username)
        self._names.pop(user['name'].lower())
        for uid in self._uids:
            if self._uids == username:
                self._uids.pop(uid)
                logging.warn("User %s:%s '%s' has been removed!", str(uid), str(username), str(user['name']))
                if self.event_removed:
                    self.event_removed(uid)

    def load_users(self):
        """Take all users into our buzom"""
        if not self.obj.GetUsersLoaded():
            logging.debug("Waiting for users to load...")
            while not self.loaded:
                time.sleep(1)
            logging.debug("Users loaded!")
        self.loaded = True
        for uid in self.obj.GetUserList():
            self.UserAdded(uid)
        self.refined = True

    def load_user(self, uid):
        """Take a single user and load it"""
        (username, name, shell, count, icon) = self.obj.GetUserInfo(uid)
        if username in self._users:
            logging.warn("Attempted to add user %s twice.", username)
            return self._info[username]
        logging.debug("User Id Added: %s", str(uid))
        # We actually list and index by username
        self._users.append(str(username))
        self._uids[uid] = str(username)
        # And save info out as python types.
        self._info[str(username)] = {
            'name':unicode(name), 'shell':str(shell), 'user':str(username),
            'count':int(count), 'icon':str(icon).replace('file://',''),
            'uid':uid,
        }
        # Make connection between username and realname.
        self._names[name.lower()] = str(username)
        return self._info[str(username)]

    def get_username_by_name(self, name):
        """Return the username for a user that matches the name"""
        return self._names.get(name.lower(), None)

    def get_user_by_name(self, username):
        """Return the user structure for a user that matches the name or username"""
        if username:
            if self._info.has_key(username):
                return self._info[username]
            return self.get_user_by_name(self.get_username_by_name(username))
        return None

