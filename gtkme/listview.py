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
Wraps the gtk treeview and iconview in something a little nicer.
"""

import logging
import pygtk
pygtk.require('2.0')
#from gi.repository import Gtk, Gdk, GObject
import gtk
from gtk import gdk
#import glib
import gobject

def text_combobox(combo, liststore):
    """
    Connects up a combo box to a liststore and gives the first column
    the text column in the display and packs it in.
    """
    #cell = Gtk.CellRendererText()
    cell = gtk.CellRendererText()
    combo.set_model(liststore)
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 0)


class BaseView(object):
    """Controls for tree and icon views, a base class"""
    def __init__(self, dbobj, selected=None, unselected=None, name=None):
        self.selected_signal = selected
        self.unselected_signal = unselected
        self._iids = []
        self._list = dbobj
        self._name = name
        self.selected = None
        self._model   = None
        self._data    = None
        self.no_dupes = True
        self.connect_signals()
        self.setup()
        super(BaseView, self).__init__()

    def connect_signals(self):
        """Try and connect signals to and from the view control"""
        raise NotImplementedError, "Signal connection should be elsewhere."

    def setup(self):
        """Setup any required aspects of the view"""
        return self._list

    def clear(self):
        """Clear all items from this treeview"""
        for iter_index in range(0, len(self._model)):
            try:
                del(self._model[0])
            except IndexError:
                logging.error("Could not delete item %d", iter_index)
                return

    def add(self, target, parent=None):
        """Add all items from the target to the treeview"""
        for item in target:
            self.add_item(item, parent=parent)

    def add_item(self, item, parent=None):
        """Add a single item image to the control"""
        if item:
            iid = self.get_item_id(item)
            if iid:
                if iid in self._iids and self.no_dupes:
                    logging.debug("Ignoring item %s in list, duplicate.", iid)
                    return None
                self._iids.append(iid)
            result = self._model.append(parent, [item])
            # item.connect('update', self.updateItem)
            return result
        else:
            raise Exception("Item can not be None.")

    def get_item_id(self, target):
        """Return if possible an id for this item,
           if set forces list to ignore duplicates,
           if returns None, any items added."""
        return target and None

    def replace(self, new_item, item_iter=None):
        """Replace all items, or a single item with object"""
        if item_iter:
            self.remove_item(target_iter=item_iter)
            self.add_item(new_item)
        else:
            self.clear()
            self._data = new_item
            self.add(new_item)

    def item_selected(self, item=None):
        """Base method result, called as an item is selected"""
        if self.selected != item:
            self.selected = item
            if self.selected_signal and item:
                self.selected_signal(item)
            elif self.unselected_signal and not item:
                self.unselected_signal(item)

    def remove_item(self, item=None, target_iter=None):
        """Remove an item from this view"""
        if target_iter and not item:
            return self._model.remove(target_iter)
        target_iter = self._model.get_iter_first()
        for itemc in self._model:
            if itemc[0] == item:
                return self._model.remove(target_iter)
            target_iter = self._model.iter_next(target_iter)

    def item_double_clicked(self, items):
        """What happens when you double click an item"""
        return items # Nothing

    def get_item(self, item_iter):
        """Return the object of attention from an iter"""
        return self._model[item_iter][0]


class TreeView(BaseView):
    """Controls and operates a tree view."""
    def connect_signals(self):
        """Attach the change cursor signal to the item selected"""
        self._list.connect('cursor_changed', self.item_selected_signal)

    def selected_items(self, treeview):
        """Return a list of selected item objects"""
        # This may need more thought, only returns one item
        item_iter = treeview.get_selection().get_selected()[1]
        try:
            return [ self.get_item(item_iter) ]
        except TypeError, msg:
            logging.debug("Error %s", msg)

    def item_selected_signal(self, treeview):
        """Signal for selecting an item"""
        items = self.selected_items(treeview)
        if items:
            return self.item_selected( items[0] )

    def item_button_clicked(self, treeview, event):
        """Signal for mouse button click"""
        #if event.type == Gdk.EventType.BUTTON_PRESS:
        if event.type == gdk.EventType.BUTTON_PRESS:
            self.item_double_clicked( self.selected_items(treeview)[0] )

    def expand_item(self, item):
        """Expand one of our nodes"""
        self._list.expand_row(self._model.get_path(item), True)

    def setup(self):
        """Set up an icon view for showing gallery images"""
        #self._model = Gtk.TreeStore(GObject.TYPE_PYOBJECT)
        self._model = gtk.TreeStore(gobject.TYPE_PYOBJECT)
        self._list.set_model(self._model)
        return self._list


class IconView(BaseView):
    """Allows a simpler IconView for DBus List Objects"""
    def connect_signals(self):
        """Connect the selection changed signal up"""
        self._list.connect('selection-changed', self.item_selected_signal)

    def setup(self):
        """Setup the icon view control view"""
        #self._model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, GObject.TYPE_PYOBJECT)
        self._model = gtk.ListStore(str, gdk.pixbuf, gobject.TYPE_PYOBJECT)
        self._list.set_model(self._model)
        return self._list

    def item_selected_signal(self, icon_view):
        """Item has been selected"""
        self.selected = icon_view.get_selected_items()


