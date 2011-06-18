#
# Copyright 2010 Martin Owens
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
Base Classes etc.
"""

import threading
import os
import logging

import pygtk
pygtk.require('2.0')
#from gi.repository import Gtk, GLib, GObject
import gtk
#from gtk import gdk
import glib
#import gobject


class Thread(threading.Thread):
    """Special thread object for catching errors and logging them"""
    def run(self, *args, **kwargs):
        """The code to run when the thread us being run"""
        try:
            super(Thread, self).run(*args, **kwargs)
        except Exception, message: #W:0041
            logging.exception(message)


class GtkApp(object):
    """
    This wraps gtk builder and allows for some extra functionality with
    windows, especially the management of gtk main loops.

    start_loop - If set to true will start a new gtk main loop.
    *args **kwargs - Passed to primary window when loaded.
    """
    prefix  = ''
    windows = None

    @property
    def glade_dir(self):
        """Set this variable in your class"""
        raise NotImplementedError("You need to set 'glade_dir' in the class.")

    @property
    def app_name(self):
        """Set this variable in your class"""
        raise NotImplementedError("You need to set 'app_name' in the class.")

    def __init__(self, **kwargs):
        self._loaded = {}
        self._inital = {}
        self._primary = None
	# self.main_loop = GLib.main_depth()
	self.main_loop = glib.main_depth()
        start_loop = kwargs.pop('start_loop', False)
        self.callback = kwargs.pop('callback', None)
        # Now start dishing out initalisation
        self.init_gui(**kwargs)
        # Start up a gtk main loop when requested
        if start_loop:
            logging.debug("Starting new GTK Main Loop.")
            gtk.main() #Gtk.main()

    def ui_file(self, window):
        """Load any given gtk builder file from a standard location."""
        # Explaining Rant: I dislike Gnome developers, for some reason they
        # think it's funny to muddle the concepts of application and window to
        # such a degree that it's impossible to create windows as seperated
        # classes handeling their own events. This happens because they have
        # stuffed a multi-window ui file into a single window ui idea, I can
        # only deduce that Gnome/Gtk developers have no concept of gobject
        # programming and are in reality an infinity of chimps typing on banna
        # phones, may entropy have mercy on their souls.
        path = os.path.join(self.glade_dir, self.prefix, "%s.glade" % window)
        if not os.path.exists(path):
            path = os.path.join(self.glade_dir, self.prefix, "%s.ui" % window)
            if not os.path.exists(path):
                raise Exception("Gtk Builder file is missing: %s" % path)
        return path


    def init_gui(self, **kwargs):
        """Initalise all of our windows and load their signals"""
        if self.windows:
            for cls in self.windows:
                window = cls
                logging.debug("Adding window %s to GtkApp", window.name )
                self._inital[window.name] = window
                if window.primary:
                    if not self._primary:
                        self._primary = self.load_window(window.name,
                            callback=self.callback, **kwargs)
                    else:
                        logging.error("More than one window is set Primary!")

    def load_window(self, name, *args, **kwargs):
        """Load a specific window from our group of windows"""
        logging.debug("Loading '%s' from %s", name, str(self._inital))
        if self._inital.has_key(name):
            # Create a new instance of this window
            window = self._inital[name](self, *args, **kwargs)
            # Save the window object linked against the gtk window instance
            self._loaded[window.wid] = window
            return window
        raise KeyError("Can't load window '%s', class not found." % name)

    def remove_window(self, window):
        """Remove the window from the list and optional exit"""
        if self._loaded.has_key(window.wid):
            self._loaded.pop(window.wid)
        else:
            logging.warn("Tried unload window '%s' on exit, it's already gone.", window.name)
            logging.debug("Loaded windows: %s", str(self._loaded))
        if not self._loaded:
            self.exit()

    def exit(self):
        """Exit our gtk application and kill gtk main if we have to"""
	# if self.main_loop < GLib.main_depth():
	if self.main_loop < glib.main_depth():
            # Quit Gtk loop if we started one.
            logging.debug("Quit '%s' Main Loop.", self._primary and self._primary.name or 'program')
            gtk.main_quit() #Gtk.main_quit()
            # You have to return in order for the loop to exit
            return 0


class FakeWidget(object):
    """A fake widget class that can take calls"""
    def __init__(self, name):
        self._name = name

    def __getattr__(self, name):
        return self.fake_method

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False

    def fake_method(self, *args, **kwargs):
        """Don't do anything, this is fake"""
        logging.info("Calling fake method: %s:%s", str(args), str(kwargs))
        return None

    def information(self):
        """This is a dumb method too"""
        return None

