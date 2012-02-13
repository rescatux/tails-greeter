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

import os, time, logging, locale
import dbus, dbus.bus, dbus.exceptions
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default = True)

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
            log( "%s:%s%s %s" % (self.interface, name, str(args), str(kwargs)) )
        else:
            log("%s:%s%s" % (self.interface, name, str(args)))


class GdmGreeter(GdmDbusService):
    """general greeter class"""
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
        logging.debug("Setting language to %s", lang)
        self.obj.SelectLanguage(locale.normalize(lang))

    def SelectLayout(self, layout):
        """Call into GdmGreeter to change the layout"""
        logging.debug("Setting session layout to %s", layout)
        if layout: self.obj.SelectLayout(layout)
        else: logging.debug("Ignored %s", layout)

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

    def BeginAutologin(self, username):
        """Attempt autologin"""
        self.obj.BeginAutologin(username)

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
        """obtain X11 display name"""
        return self.obj.GetX11DisplayName()

    @property
    def number(self):
        """obtain X11 display number"""
        return self.obj.GetX11DisplayNumber()
