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
Greeter program for GDM using gtk (nothing else works)
"""

import sys, os
import logging

#from gi.repository import Gtk, Gdk, GLib, GObject
import gtk
from gtk import gdk
import glib
import gobject

from GdmGreeter.services import GdmUsers
from GdmGreeter.language import TranslatableWindow
from GdmGreeter import Images

class LoginWindow(TranslatableWindow):
    """Display a login window"""
    name = 'login'
    primary = False
    other_asks = ['pass', 'name']

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service')
        TranslatableWindow.__init__(self, *args, **kwargs)
        self.search = self.widget('namesearch')
        self.users = GdmUsers(added=self.added_user, removed=self.removed_user)
        self.images = Images('auto')
        self.setup_autocomplete()
        self.users.load_users()

    def show_user(self, text):
        """We should ask for the user's name now"""
        self.ask_user_for('name')
        self.show_image()

    def show_pass(self, text):
        """We should ask for the user's password now"""
        self.ask_user_for('pass')

    def ask_user_for(self, name):
        """Ask user for..."""
        self.widget(name).show()
        for ask in self.other_asks:
            if ask != name:
                self.widget(ask).hide()
        entry = self.widget('%s_entry' % name)
        entry.set_text('')
        entry.set_sensitive(True)
        self.window.set_focus(entry)

    def show_image(self, icon='logo'):
        """Show the user's picture or some other icon"""
        # logo.svg -> default.svg <- ${icon}.svg <- filename
        self.widget('user_image').set_from_pixbuf(self.images.get_pixmap(icon))

    def cancel(self, widget=None, event=None):
        #if not event or event.key.keyval == Gdk.KEY_Escape:
        if not event or event.keyval == gtk.keysyms.Escape:
            self.service.Cancel()

    def setup_autocomplete(self):
        """Sets up the autocomplete functionality"""
        def text_cell_func(column, cell, model, iter_index):
            markup = "%s (%s)" % (model.get_value(iter_index, 0),
                model.get_value(iter_index, 1))
            renderer.set_property("markup", markup)

        #self.userstore = Gtk.TreeStore(GObject.TYPE_STRING)
        self.userstore = gtk.TreeStore(gobject.TYPE_STRING)
        self.search.set_model(self.userstore)
        self.search.set_match_func(self.match_user, 0)
        self.widget('name_entry').set_completion(self.search)
        #renderer = Gtk.CellRendererText()
        renderer = gtk.CellRendererText()
        self.search.pack_start(renderer, False)
        self.search.set_text_column(0)

    def match_user(self, completion, text, iter, column, user=None):
        """Match a user against what they've typed so far"""
        # Happens after name_changed event below! Take notice.
        user = user or self.userstore.get_value(iter, column)
        if text and user and user.lower().startswith(text.lower()):
            return True
        return False

    def generate_matches(self, text):
        """Returns a list of matching users"""
        result = []
        # This is requires because match_user for the completion happens
        # After name_changed event which is depending on that list.
        # So we build the list twice. Soss.
        for user in self.users._info.values():
            if self.match_user(None, text, None, None, user=user['name']):
                result.append(user['name'])
        return result

    def added_user(self, user):
        """Event for adding users."""
        logging.warn("Adding User: '%s'" % user['name'])
        self.userstore.append(None, [str(user['name'])])

    def removed_user(self, uid):
        """Event for removing users."""
        logging.warn("Removing User: '%s'" % uid)

    def name_changed(self, widget):
        """Event handler for username textbox, keypress"""
        content = widget.get_text()
        if len(content) >= self.search.get_minimum_key_length():
            matches = self.generate_matches(content)
            # Take the user from the last match or from an exact match
            if len(matches) == 1:
                if content.lower() == matches[0].lower():
                    self.name_activated(widget)
                name = matches[0]
            else:
                name = content
            user = self.users.get_user_by_name(name)
            if user:
                # Get their photo and display it if possible.
                self.show_image( user['icon'] )
            elif len(matches) == 0:
                # If nothing matches and there are no possible matches, then
                # Assume the user is new and show them some love.
                self.show_image('newuser')
            else:
                self.show_image()
        else:
            self.show_image()

    def name_activated(self, widget):
        """Event handler for full name textbox, on enter"""
        name = widget.get_text()
        matches = self.generate_matches(name)
        # Don't do anything if the name is too short.
        if len(name) < self.search.get_minimum_key_length():
            return
        # If we only have one match in the shown list, then
        # Replace the text in the box and return.
        if len(matches) == 1 and matches[0].lower() != name.lower():
            return widget.set_text(str(matches[0]))
        # Disable the box for a login
        widget.set_sensitive(False)
        user = self.users.get_user_by_name(name)
        if user:
            self.service.AnswerQuery(user['user'])
        else:
            if name == name.lower():
                name = name.title()
            register = self.load_window('register', real_name=name,
                users=self.users._users, callback=self.cancel)

    def pass_activated(self, widget):
        """Event handler for password textbox, on enter"""
        widget.set_sensitive(False)
        self.service.AnswerQuery(widget.get_text())


