#!/usr/bin/python
#
# Copyright 2013 Tails developers <tails@boum.org>
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
"""Help screen

"""

import GdmGreeter
from   GdmGreeter.language import TranslatableWindow
import gtk
import os
import webbrowser
import webkit

class HelpWindow(TranslatableWindow):
    """Displays a modal html help window"""

    def __init__(self, uri):
        builder = gtk.Builder()
        builder.set_translation_domain(GdmGreeter.__appname__)
        builder.add_from_file(os.path.join(GdmGreeter.GLADE_DIR,
                                           "helpwindow.glade"))
        builder.connect_signals(self)
        TranslatableWindow.__init__(self, builder.get_object("help_dialog"))
        self.html_help = webkit.WebView()

        def cb_request_starting(web_view, web_frame, web_ressource, request,
                                response, user_data = None):
            if not request.get_uri().startswith("file://"):
                webbrowser.open_new(request.get_uri())
                request.set_uri(web_frame.get_uri())

        self.html_help.connect("resource-request-starting",
                               cb_request_starting)
        self.help_container = builder.get_object("scrolled_help")
        self.html_help.load_uri(uri)
        self.help_container.add_child(builder, self.html_help, None)
        self.html_help.show()
        self.window.run()

    def close(self, *args):
        self.window.destroy()
