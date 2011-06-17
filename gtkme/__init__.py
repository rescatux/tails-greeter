#
# Copyright 2009 Martin Owens
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
Manages a GtkApp object as well as wrapping several classes.
"""

import threading
import os
import logging

from gtkme.window import Window, ChildWindow, FormWindow, ThreadedWindow
from gtkme.listview import TreeView, IconView
from gtkme.pixmap import PixmapManager
from gtkme.main import Thread, GtkApp, FakeWidget

__version__ = '1.0'

