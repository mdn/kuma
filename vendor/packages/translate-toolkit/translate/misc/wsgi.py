#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of translate.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""wrapper tht tries to pick the best available wsgi server"""

import logging
import os

def launch_server_wsgiref(host, port, app):
    """use python's builtin simple_server, this is a last resort since
    it doesn't support concurrency at all"""
    from wsgiref import simple_server
    class CustomRequestHandler(simple_server.WSGIRequestHandler):
        """Custom request handler, disables some inefficient defaults"""

        def address_string(self):
            """Disable client reverse dns lookup."""
            return  self.client_address[0]

        def log_error(self, format, *args):
            """Log errors using logging instead of printing to
            stderror"""
            logging.error("%s - - [%s] %s",
                          self.address_string(), self.log_date_time_string(), format % args)
            
        def log_message(self, format, *args):
            """Log requests using logging instead of printing to
            stderror."""
            logging.info("%s - - [%s] %s",
                         self.address_string(),  self.log_date_time_string(), format % args)
        
    server = simple_server.make_server(host, port, app, handler_class=CustomRequestHandler)
    logging.info("Starting wsgiref server, listening on port %s", port)
    server.serve_forever()


def launch_server_django(host, port, app):
    """use django's development server, only works for django apps"""
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        raise ImportError("no django settings module specified")

    from django.core.servers.basehttp import  run

    logging.info("Starting Django server, listening on port %s", port)
    run(host, port, app)


def launch_server_cherrypy(host, port, app):
    """use cherrypy's wsgiserver, a multithreaded scallable server"""
    from cherrypy.wsgiserver import  CherryPyWSGIServer

    server = CherryPyWSGIServer((host, port), app)
    logging.info("Starting CherryPy server, listening on port %s", port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

#FIXME: implement threading http server based on BaseHTTPServer and wsgiref

servers = [launch_server_cherrypy, launch_server_django, launch_server_wsgiref]

def launch_server(host, port, app):
    """use the best possible wsgi server"""
    for server in servers:
        try:
            server(host, port, app)
            break
        except ImportError:
            pass

            
