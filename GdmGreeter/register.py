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

import sys
import logging
import crypt
import random
import string

import gtk
import gobject

from gtkme.listview import text_combobox
from GdmGreeter.language import TranslatableFormWindow#, LANGS, LanguageButton
from GdmGreeter.user import User

ALPHANUM = string.letters + string.digits

class RegisterWindow(TranslatableFormWindow):
    """Display a create user window"""
    name = 'register'
    primary = False
    fields = [ None, {
        'age'      : { 'maxLength': 3, 'minLength': 1 },
        'postcode' : { 'maxLength': 20, 'minLength': 0 },
        'gender'   : { 'maxLength': 40, 'minLength': 0, 'enumeration': ['-','M','F'] },
    },{
        'password' : { 'maxLength': 200, 'minLength': 6, },
        'confirm'  : { 'maxLength': 200, 'minLength': 6, 'match': 'password' },
        'email'    : { 'maxLength': 200, 'minLength': 0, },
    },{
        'comments' : { },
    },None,
    ]

    def __init__(self, *args, **kwargs):
        self._username = None
        # Data input preperation
        self.realname = kwargs.pop('real_name')
        self.users = kwargs.pop('users')
        self.user = User( self.username )
        logging.debug("RegisterWindow ready for translation.")
        # Call the higher power to translate the window
        TranslatableFormWindow.__init__(self, *args, **kwargs)
        # Deal with issues of widgetness
        self.label = self.widget('label')
        self.languages = self.widget('buttonbar')
        text_combobox(self.widget('field_gender'), self.widget('genders'))

    @property
    def username(self):
        """Return the username for this user"""
        if not self._username:
            username = self.realname.lower().replace(' ', '-')
            username = "".join(i for i in username if ord(i) < 128)
            self._username = username + "-" + "".join(random.sample(ALPHANUM, 6))
        return self._username

    def translate_to(self, lang):
        """Translate but also fill in the language selection field"""
        TranslatableFormWindow.translate_to(self, lang)
        self.label.set_label(self.label.get_label() % self.realname)
        self.language = lang

    def cancel(self, widget, event=None):
        """Event for canceling the registration, Esc or Gtk.Button"""
        if isinstance(widget, gtk.Button) or (event and event.keyval == gtk.keysyms.Escape):
            self.destroy()

    def get_data(self):
        """Return all the user entered data"""
        result = self.all_field_data()
        result['name'] = self.realname
        result['username'] = self.username
        result['language'] = self.language
        # Encrypt password and remove confirm password field.
        salt = '$6$%s$' % "".join(random.sample(ALPHANUM, 12))
        result['password'] = crypt.crypt(result.pop('confirm'), salt)
        # Return all our data for a laugh.
        return result

    def apply(self, widget=None):
        """Apply the registration... before the window is destroyed."""
        user = User( self.username )
        user.save( self.get_data() )
        # Show the user something interesting to let them know we're waiting
        # This doesn't actually work unless the wait is threaded or timed.
        self.widget('pages').hide()
        self.widget('buttons').hide()
        self.widget('pleasewait').show()
        # Wait for the user to be registered, the server deletes or
        # zeros the file when it's complete so we wait for that.
        sys.stderr.write("Waiting for registrations\n")
        self.wait_for_new_user()

    def wait_for_new_user(self):
        """Wait for user to appear..."""
        if self.username not in self.users:
            #sys.stderr.write("Testing: %s not in %s\n" % (self.username, str(self.users)))
            return gobject.timeout_add( 1000, self.wait_for_new_user )
        self.finish_registration()

    def finish_registration(self):
        """Now we're done with the registration, we can destroy the window"""
        self.done = True
        self.destroy()

    def pre_exit(self):
        """What to do when the window is destroyed"""
        self.callback()

    def update_buttons(self, *args):
        """Hide and show the cancel button"""
        this_page = super(RegisterWindow, self).update_buttons(*args)
        self.update_button('cancel', this_page == 0)

