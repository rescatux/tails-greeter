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
Wraps the gtk windows with something a little nicer.
"""

import logging
from xsdvalidate import Validator
from gtkme.main import Thread, FakeWidget

import pygtk
pygtk.require('2.0')
#from gi.repository import Gtk, Gdk, GLib, GObject
import gtk
from gtk import gdk
import glib
import gobject

class Window(object):
    """
    This wraps gtk windows and allows for having parent windows as well
    as callback events when done and optional quiting of the gtk stack.

    name = 'name-of-the-window'

    Should the window be the first loaded and end gtk when closed:

    primary = True/False

    A list of all the field elements in the window that should be given
    to the callback when exiting:

    fields = [ 'widget-name', ... ]
    
    """
    name    = None
    primary = True
    fields  = []

    def __init__(self, gapp, parent=None, callback=None):
        self.gapp     = gapp
        # Set object defaults
        self.dead     = False
        self.parent   = parent
        self.callback = callback

        # Setup the gtk app connection
        #self.w_tree   = Gtk.Builder()
        self.w_tree   = gtk.Builder()
        self.widget   = self.w_tree.get_object
        self.w_tree.set_translation_domain(self.gapp.app_name)
        self.w_tree.add_from_file(gapp.ui_file(self.name))
        self.w_tree.connect_signals(self)

        # Setup the gtk builder window
        self.window = self.widget(self.name)
        if not self.window:
            raise Exception("Missing window widget '%s' from '%s'" % (
                self.name, gapp.ui_file(self.name)))

        # These are some generic convience signals
        self.window.connect('destroy', self.exit)

        # Give us a window id to track this window
        self.wid = str(hash(self.window))

        # If we have a parent window, then we expect not to quit
        if self.parent:
            self.parent.set_sensitive(False)

        # We may have some more gtk widgets to setup
        self.load_widgets()
        self.window.show()

    def __getattr__(self, name):
        """Catch signals with window names that need to be stripped."""
        # Be warned all ye who enter here, GTK will eat your errors and
        # exceptions and simply complain about missing signals. This happened
        # to me, don't let it happen to you!
        if self.name+'_' in name:
            function = name.replace(self.name+'_', '')
            return getattr(self, function)
        raise AttributeError("Window '%s' has no method '%s'" %(
            type(self).__name__, name))

    def load_window(self, name, *args, **kwargs):
        """Load child window, automatically sets parent"""
        kwargs['parent'] = self.window
        return self.gapp.load_window(name, *args, **kwargs)

    def load_widgets(self):
        """Child class should use this to create widgets"""
        pass

    def destroy(self):
        """Destroy the window"""
        logging.debug("Destroying Window %s" % self.name)
        self.window.destroy()
        # We don't need to call self.exit(),
        # handeled by window event.

    def pre_exit(self):
        """Internal method for what to do when the window has died"""
        if self.callback:
            self.callback(self)

    def exit(self, widget=None):
        """Called when the window needs to exit."""
        #if not widget or not isinstance(widget, Gtk.Window):
    	if not widget or not isinstance(widget, gtk.Window):
            self.destroy()
        # Clean up any required processes
        self.pre_exit()
        if self.parent:
            # We assume the parent didn't load another gtk loop
            self.parent.set_sensitive(True)
        # Exit our entire app if this is the primary window
        # Or just remove from parent window list, which may still exit.
        if self.primary:
            logging.debug("Exiting the application")
            self.gapp.exit()
        else:
            logging.debug("Removing Window %s from parent" % self.name)
            self.gapp.remove_window(self)
        # Now finish up what ever is left to do now the window is dead.
        self.dead = True
        self.post_exit()
        return widget

    def post_exit(self):
        """Called after we've killed the window"""
        pass

    def if_widget(self, name):
        """
        Attempt to get the widget from gtk, but if not return a fake that won't
        cause any trouble if we don't further check if it's real.
        """
        return self.widget(name) or FakeWidget(name)


class ChildWindow(Window):
    """
    Base class for child window objects, these child windows are typically
    window objects in the same gtk builder file as their parents. If you just want
    to make a window that interacts with a parent window, use the normal
    Window class and call with the optional parent attribute.
    """
    primary = False


class FormWindow(ChildWindow):
    """
    Base class from windows which act as forms, they expect to contain all
    kinds of fields and be able to validate them and pass the data back to
    the callback when required.
    """
    fields = None

    def __init__(self, *args, **kwrds):
        self.done      = False
        self._data     = {}
        self._marked   = {}
        self._pindex   = []
        super(FormWindow, self).__init__(*args, **kwrds)
        self._notebook = self.if_widget('pages')
        if self._notebook:
            self._notebook.connect("switch-page", self.update_buttons)
            for n in range(self._notebook.get_n_pages()):
                page = self._notebook.get_nth_page(n)
                self._pindex.append(page)

    def pre_exit(self):
        """Callback on exit with form data as args."""
        if self.callback and self.done:
            self.callback(**self.data())
            # Reset callback so super doesn't execute it.
            self.callback = None

    def data(self):
        """Access the data in the window."""
        # Refresh the data when the window is still alive
        # But don't when the window is closed (because we can't)
        if not self.dead:
            self._data = self.get_data()
        return self._data

    def get_data(self):
        """Return the data from all fields on the window."""
        return {}

    def double_click(self, widget, event):
        """This is the cope with gtk's rotten support for mouse events"""
        #if event.type == Gdk._2BUTTON_PRESS:
        if event.type == gdk._2BUTTON_PRESS:
            return self.apply(widget)

    def next_page(self, widget=None):
        """When we have pages calling this event will move to the next"""
        working = self.is_valid(self._notebook.get_current_page())
        if working != True:
            return self.mark_invalid(working)
        # Call apply on this form if we've reached the end.
        if self._notebook.get_n_pages()-1 == self._notebook.get_current_page():
            return self.apply(widget)
        else:
            self._notebook.next_page()
        return widget

    def previous_page(self, widget=None):
        """when we have pages call this event and go back to the prev page"""
        notebook = self.if_widget('pages')
        notebook.prev_page()
        return widget

    def this_page(self, overide=None):
        """Return the current page we're on"""
        if overide == None:
            return self._notebook.get_current_page()
        return int(overide)

    @property
    def first_page(self):
        """Return the first page index, normally 0"""
        return 0

    @property
    def last_page(self):
        """Return the last page index, normally count -1"""
        return self._notebook.get_n_pages() - 1

    def update_buttons(self, widget, page_from, page_to):
        """Updates the back, forward and apply buttons"""
        this_page = self.this_page(page_to)
        # Enable the back button if the page is != 0
        self.update_button('back', this_page > self.first_page)
        # Hide the forward and show the apply if the page is last
        if self.if_widget('apply'):
            self.update_button('apply', this_page == self.last_page)
            self.update_button('forward', this_page < self.last_page)
        else:
            # Sometimes we hide the forward button in glade so loading
            # screens can take the entire space. But now we need them.
            self.update_button('forward', True)
        return this_page

    def update_button(self, name, enable):
        """Show/hide and/or enable/disable the named button"""
        #self.if_widget(name).set_sensitive(enable)
        self.if_widget(name).set_visible(enable)

    def set_page(self, pageid):
        """Set the form to a specific page"""
        if isinstance(pageid, int):
            self._notebook.set_current_page(pageid)
        elif isinstance(pageid, basestring):
            element = self.if_widget(pageid)
            if element and element in self._pindex:
                return self.set_page(self._pindex.index(element))
            else:
                raise KeyError("Couldn't find page element '%s'" % pageid)
        else:
            raise KeyError("Page id isn't an index or an element id.")

    def apply(self, widget=None):
        """Apply any changes as required by callbacks"""
        problems = self.is_valid()
        # True for is_valid or a list of problems
        if not problems or problems == True:
            logging.debug("Applying changes")
            self.done = True
            # Make sure arguments are stored.
            if not isinstance(self.data(), dict):
                logging.warn("%s data isn't a dictionary." % self.name)
            # Now exit the main application.
            self.destroy()
        else:
            self.mark_invalid(problems)
        return widget

    def is_valid(self, page=-1):
        "Return true if all data is valid or an array of invalid widget names." 
        # If fields is defined than we expect to do field validation.
        if self.fields:
            if isinstance(self.fields, list):
                # Checking single page
                if page >= 0 and page < len(self.fields):
                    return self.are_fields_valid(self.fields[page])
                else: # Checking all pages
                    for p in range(0, len(self.fields)):
                        errors = self.are_fields_valid(self.fields[p])
                        if errors != True:
                            return errors
            else: # No pages exist
                return self.are_fields_valid(self.fields)
        return True

    def are_fields_valid(self, f_def):
        """Returns true if the hash of field definitions are all valid."""
        if not f_def:
            return True
        data = self.field_data(f_def)
        field_list = []
        # Translate to xsd style syntax by transposing
        # the name into the hash from the key.
        for name in f_def.keys():
            field = f_def[name]
            field['name'] = name
            field['type'] = field.get('type', 'string')
            field_list.append( field )
        validator = Validator( { 'root' : field_list } )
        try:
            errors = validator.validate( data )
        except Exception, msg:
            logging.warn("Couldn't validate page, skipping validation: %s"%msg)
        # Collect the errors and report on what fields failed
        if errors:
            result = []
            for err in errors.keys():
                if errors[err]:
                    result.append(err)
            return result
        # Otherwise we pass!
        return True

    def all_field_data(self):
        """Returns all of the fields we know about"""
        result = {}
        if isinstance(self.fields, list):
            for fields in self.fields:
                result.update(self.field_data(fields))
        return result

    def field_data(self, fields):
        """Return a simple hash of all the fields"""
        if not fields:
            return {}
        result = {}
        for name, field in fields.iteritems():
            widget = self.widget('field_' + name)
            #if isinstance(widget, Gtk.TextView):
            if isinstance(widget, gtk.TextView):
                buf = widget.get_buffer()
                start, end = ( buf.get_start_iter(), buf.get_end_iter() )
                result[name] = buf.get_text( start, end, True )
            #elif isinstance(widget, Gtk.Entry):
            elif isinstance(widget, gtk.Entry):
                try:
                    result[name] = widget.get_text()
                except AttributeError:
                    result[name] = ''
            #elif isinstance(widget, Gtk.ComboBox):
            elif isinstance(widget, gtk.ComboBox):
                # To avoid translations messing up the validation, with the
                # enumeration validation, this returns the index if no enum
                # is available, but will return the string if it is. Glade
                # is expected to translate, so don't translate your enum.
                active = widget.get_active()
                if active >= 0 and field.has_key('enumeration'):
                    active = field['enumeration'][active]
                result[name] = active
            #elif isinstance(widget, Gtk.RadioButton):
            elif isinstance(widget, gtk.RadioButton):
                group = widget.get_group()
                if group:
                    for radio in group:
                        if radio.get_active():
                            result[name] = radio.get_label()
            #elif isinstance(widget, Gtk.CheckButton):
            elif isinstance(widget, gtk.CheckButton):
                result[name] = widget.get_active()
            else:
                logging.warn("Couldn't find field %s!" % name)
        return result

    def mark_invalid(self, invalids):
        """This is what happens when we're not valid"""
        if isinstance(self.fields, list):
            for f in self.fields:
                self._mark_invalid(invalids, f)
        else:
            self._mark_invalid(invalids, self.fields)

    def _mark_invalid(self, invalids, marks):
        """Only mark invalid on a set list"""
        if not marks:
            return
        for fname in marks.keys():
            widget = self.if_widget(fname+'_label')
            marked = self._marked.get(fname, None)
            if fname in invalids and not marked:
                self._marked[fname] = widget.get_label()
                widget.set_label(
                        "<span color='red'>*%s</span>" % self._marked[fname])
            elif fname not in invalids and marked:
                widget.set_label(self._marked.pop(fname))

    def cancel(self, widget=None):
        """We didn't like what we did, so don't apply"""
        self.done = False
        self.destroy()
        return widget

    
class ThreadedWindow(Window):
    """
    This class enables an extra status stream to cross call gtk
    From a threaded process, allowing unfreezing of gtk apps.
    """
    animated_widget = None
    animated_icons = None
    animated_count = 0
    inital_thread = None

    def __init__(self, *args, **kwargs):
        # Common variables for threading
        self._thread = None
        self._closed = False
        self._calls  = [] # Calls Stack
        self._unique = {} # Unique calls stack
        self._anista = None
        # Back to setting up a window
        super(ThreadedWindow, self).__init__(*args, **kwargs)
        # And try and set up any animated widget
        if self.animated_widget:
            self._anista = self.widget(self.animated_widget)
            self._anipos = 0
        # Kick off the inital thread, if there is one
        if self.inital_thread:
            self.start_thread(self.inital_thread)
        
    def start_thread(self, method, *args, **kwargs):
        """Kick off a thread and a status monitor timer"""
        if not self._thread or not self._thread.isAlive() and not self._closed:
            self._thread = Thread(target=method, args=args, kwargs=kwargs)
            self._thread.start()
            logging.debug("-- Poll Start %s --" % self.name)
            # Show an animation to reflect the polling
            if self._anista:
                self._anista.show()
            # Kick off a polling service, after a delay
            #GObject.timeout_add( 300, self.thread_through )
            gobject.timeout_add( 300, self.thread_through )
        else:
            raise Exception("Thread is already running!")

    def thread_through(self):
        """Keep things up to date fromt he thread."""
        self.process_calls()
        if self._thread.isAlive():
            #logging.debug("-- Poll Through %s --" % self.name)
            # This will allow our poll to be visible to the user and
            # Has the advantage of showing stuff is going on.
            if self._anista:
                self._anipos += 1
                if self._anipos == self.animated_count:
                    self._anipos = 1
                image = self.animated_icons.get_icon(str(self._anipos))
                self._anista.set_from_pixbuf(image)
            #GObject.timeout_add( 100, self.thread_through )
            gobject.timeout_add( 100, self.thread_through )
        else:
            logging.debug("-- Poll Quit %s --" % self.name)
            # Hide the animation by default and exit the thread
            if self._anista:
                self._anista.hide()
            self.thread_exited()

    def thread_exited(self):
        """What is called when the thread exits"""
        pass

    def call(self, name, *args, **kwargs):
        """Call a method outside of the thread."""
        unique = kwargs.pop('unique_call', False)
        if type(name) != str:
            raise Exception("Call name must be a string not %s" % type(name))
        call = (name, args, kwargs)
        # Unique calls replace the previous calls to that method.
        if unique:
            self._unique[name] = call
        else:
            self._calls.append( call )

    def process_calls(self):
        """Go through the calls stack and call them, return if required."""
        ret = None
        while self._calls:
            (name, args, kwargs) = self._calls.pop(0)
            logging.debug("Calling %s" % name)
            ret = getattr(self, name)(*args, **kwargs)
        for name in self._unique.keys():
            (name, args, kwargs) = self._unique.pop(name)
            ret = getattr(self, name)(*args, **kwargs)
        return ret

    def pre_exit(self):
        """Mark the thread as closed before exiting"""
        if self._thread and self._thread.isAlive():
            logging.warn("Your thread is still active.")
        self._closed = True
        super(ThreadedWindow, self).pre_exit()


