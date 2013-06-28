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
"""
Thin layer on top of libgdmgreeter.
"""

import logging

from gi.repository import GdmGreeter
# from gi.repository import Gtk
from gi.repository import GLib
import tailsgreeter.config

class GdmClient (object):
    
    AUTOLOGIN_SERVICE_NAME = 'gdm3-autologin'
    USER_NAME = tailsgreeter.config.LUSER

    def __init__(self, server_ready_cb):
        self.server_ready = False
        self.server_ready_cb = server_ready_cb

        self.__greeter_client = GdmGreeter.Client()
        self.__greeter_client.open_connection()

        self.__greeter_client.connect('ready', self.__on_ready)
        self.__greeter_client.connect('reset', self.__on_reset)
        self.__greeter_client.connect('default-session-changed', self.__on_default_session_changed)
        self.__greeter_client.connect('info', self.__on_info)
        self.__greeter_client.connect('problem', self.__on_problem)
        self.__greeter_client.connect('info-query', self.__on_info_query)
        self.__greeter_client.connect('secret-info-query', self.__on_secret_info_query)
        self.__greeter_client.connect('session-opened', self.__on_session_opened)
        self.__greeter_client.connect('timed-login-requested', self.__on_timed_login_requested)
        self.__greeter_client.connect('authentication-failed', self.__on_authentication_failed)
        self.__greeter_client.connect('conversation-stopped', self.__on_conversation_stopped)

        self.__greeter_client.call_start_conversation(GdmClient.AUTOLOGIN_SERVICE_NAME)

        # XXX: to activate the main loop or something like that
        # self.__dialog = Gtk.MessageDialog(None,
        #                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
        #                            Gtk.MessageType.INFO,
        #                            Gtk.ButtonsType.OK,
        #                            "Click to start autologin")
        # self.__dialog.run()

    def __on_ready(self, client, service_name):
        logging.debug("Received ready")
        self.server_ready = True
        self.server_ready_cb()

    def __on_session_opened(self, client, service_name):
        logging.debug("Received session opened")
        client.call_start_session_when_ready(service_name, True)

    def __on_default_session_changed(self, client, session_id):
        logging.debug("Received session changed: %s" % session_id)

    def __on_info(self, client, service_name, info):
        logging.debug("Received info: %s" % info)

    def __on_reset(self, client, service_name):
        logging.debug("Received reset")
        raise NotImplementedError

    def __on_problem(self, client, service_name, problem):
        logging.debug("Received problem: %s" % problem)
        raise NotImplementedError

    def __on_info_query(self, client, service_name, question):
        logging.debug("Received info query: %s" % question)
        raise NotImplementedError

    def __on_secret_info_query(self, client, service_name, secret_question):
        logging.debug("Received secret info query: %s" % secret_question)
        raise NotImplementedError

    def __on_timed_login_requested(self, client, user_name, seconds):
        logging.debug("Received timed login resquet for %s in %s" % (user_name, seconds))
        raise NotImplementedError

    def __on_authentication_failed(self, client):
        logging.debug("Received authentication failure")
        raise NotImplementedError

    def __on_conversation_stopped(self, client, service_name):
        logging.debug("Received conversation stopped")
        raise NotImplementedError

    def do_login(self):
        if self.server_ready:
            GLib.idle_add(lambda: self.__greeter_client.call_begin_auto_login(GdmClient.USER_NAME))
        else:
            raise tailsgreeter.errors.GdmServerNotReady
