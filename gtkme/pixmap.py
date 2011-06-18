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
Wraps the gtk pixmap access.
"""

import os
import logging

import pygtk
pygtk.require('2.0')
#from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
#import gtk
from gtk import gdk
#import glib
#import gobject

class PixmapManager(object):
    """Manage a set of cached pixmaps"""
    missing_image = None
    default_image = 'default'

    def get_pixmap_dir(self):
        """Set this variable in your class"""
        if not self.pixmap_dir:
            raise NotImplementedError("You need to set 'pixmap_dir' in the class.")
        return self.pixmap_dir

    def __init__(self, location, pixmap_dir=None):
        if pixmap_dir:
            self.pixmap_dir = pixmap_dir
        self.location = os.path.join(self.get_pixmap_dir(), location)
        self.cache    = {}
        self.get_pixmap(self.default_image)

    def get_pixmap(self, name):
        """Simple method for getting a set of pix pixmaps and caching them."""
        if not name:
            name = self.default_image
        if not self.cache.has_key(name):
            pixmap_path = self.pixmap_path(name)
            if os.path.exists(pixmap_path):
                try:
                    #self.cache[name] = GdkPixbuf.Pixbuf.new_from_file(pixmap_path)
                    self.cache[name] = gdk.pixbuf_new_from_file(pixmap_path)
                except RuntimeError, msg:
                    logging.warn("No pixmap '%s',%s", pixmap_path, msg)
            else:
                self.cache[name] = None
                logging.warning("Can't find pixmap for %s in %s", (name, self.location))
        if not self.cache.has_key(name) or not self.cache[name]:
            name = self.default_image
        return self.cache.get(name, self.missing_image)

    def pixmap_path(self, name):
        """Returns the pixmap path based on stored location"""
        svg_path = os.path.join(self.location, '%s.svg' % name)
        png_path = os.path.join(self.location, '%s.png' % name)
        if os.path.exists(name) and os.path.isfile(name):
            return name
        if os.path.exists(svg_path) and os.path.isfile(svg_path):
            return svg_path
        elif os.path.exists(png_path) and os.path.isfile(png_path):
            return png_path
        return os.path.join(self.location, name)


