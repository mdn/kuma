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

"""A translation memory server using tmdb for storage, communicates
with clients using JSON over HTTP."""

import urllib
import StringIO
import logging
import sys
from cgi import parse_qs
from optparse import OptionParser
try:
    import json #available since Python 2.6
except ImportError:
    import simplejson as json #API compatible with the json module
from wsgiref import simple_server

from translate.misc import selector
from translate.misc import wsgi
from translate.storage import factory
from translate.storage import base
from translate.storage import tmdb

class TMServer(object):
    """A RESTful JSON TM server."""

    def __init__(self, tmdbfile, tmfiles, max_candidates=3, min_similarity=75,
            max_length=1000, prefix="", source_lang=None, target_lang=None):

        self.tmdb = tmdb.TMDB(tmdbfile, max_candidates, min_similarity, max_length)

        #load files into db
        if isinstance(tmfiles, list):
            [self.tmdb.add_store(factory.getobject(tmfile), source_lang, target_lang) \
                    for tmfile in tmfiles]
        elif tmfiles:
            self.tmdb.add_store(factory.getobject(tmfiles), source_lang, target_lang)

        #initialize url dispatcher
        self.rest = selector.Selector(prefix=prefix)
        self.rest.add("/{slang}/{tlang}/unit/{uid:any}",
                      GET=self.translate_unit,
                      POST=self.update_unit,
                      PUT=self.add_unit,
                      DELETE=self.forget_unit
                      )

        self.rest.add("/{slang}/{tlang}/store/{sid:any}",
                      GET=self.get_store_stats,
                      PUT=self.upload_store,
                      POST=self.add_store,
                      DELETE=self.forget_store)

    @selector.opliant
    def translate_unit(self, environ, start_response, uid, slang, tlang):
        start_response("200 OK", [('Content-type', 'text/plain')])
        candidates = self.tmdb.translate_unit(uid, slang, tlang)
        logging.debug("candidates: %s", unicode(candidates))
        response = json.dumps(candidates, indent=4)
        params = parse_qs(environ.get('QUERY_STRING', ''))
        try:
            callback = params.get('callback', [])[0]
            response = "%s(%s)" % (callback, response)
        except IndexError:
            pass
        return [response]

    @selector.opliant
    def add_unit(self, environ, start_response, uid, slang, tlang):
        start_response("200 OK", [('Content-type', 'text/plain')])
        #uid = unicode(urllib.unquote_plus(uid), "utf-8")
        data = json.loads(environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'])))
        unit = base.TranslationUnit(data['source'])
        unit.target = data['target']
        self.tmdb.add_unit(unit, slang, tlang)
        return [""]

    @selector.opliant
    def update_unit(self, environ, start_response, uid, slang, tlang):
        start_response("200 OK", [('Content-type', 'text/plain')])
        #uid = unicode(urllib.unquote_plus(uid), "utf-8")
        data = json.loads(environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'])))
        unit = base.TranslationUnit(data['source'])
        unit.target = data['target']
        self.tmdb.add_unit(unit, slang, tlang)
        return [""]

    @selector.opliant
    def forget_unit(self, environ, start_response, uid):
        #FIXME: implement me
        start_response("200 OK", [('Content-type', 'text/plain')])
        #uid = unicode(urllib.unquote_plus(uid), "utf-8")

        return [response]

    @selector.opliant
    def get_store_stats(self, environ, start_response, sid):
        #FIXME: implement me
        start_response("200 OK", [('Content-type', 'text/plain')])
        #sid = unicode(urllib.unquote_plus(sid), "utf-8")

        return [response]

    @selector.opliant
    def upload_store(self, environ, start_response, sid, slang, tlang):
        """add units from uploaded file to tmdb"""
        start_response("200 OK", [('Content-type', 'text/plain')])
        data = StringIO.StringIO(environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'])))
        data.name = sid
        store = factory.getobject(data)
        count = self.tmdb.add_store(store, slang, tlang)
        response = "added %d units from %s" % (count, sid)
        return [response]

    @selector.opliant
    def add_store(self, environ, start_response, sid, slang, tlang):
        """Add unit from POST data to tmdb."""
        start_response("200 OK", [('Content-type', 'text/plain')])
        units = json.loads(environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'])))
        count = self.tmdb.add_list(units, slang, tlang)
        response = "added %d units from %s" % (count, sid)
        return [response]

    @selector.opliant
    def forget_store(self, environ, start_response, sid):
        #FIXME: implement me
        start_response("200 OK", [('Content-type', 'text/plain')])
        #sid = unicode(urllib.unquote_plus(sid), "utf-8")

        return [response]


def main():
    parser = OptionParser()
    parser.add_option("-d", "--tmdb", dest="tmdbfile", default=":memory:",
                      help="translation memory database file")
    parser.add_option("-f", "--import-translation-file", dest="tmfiles", action="append",
                      help="translation file to import into the database")
    parser.add_option("-t", "--import-target-lang", dest="target_lang",
                      help="target language of translation files")
    parser.add_option("-s", "--import-source-lang", dest="source_lang",
                      help="source language of translation files")
    parser.add_option("-b", "--bind", dest="bind", default="localhost",
                      help="adress to bind server to (default: localhost)")
    parser.add_option("-p", "--port", dest="port", type="int", default=8888,
                      help="port to listen on (default: 8888)")
    parser.add_option("--max-candidates", dest="max_candidates", type="int", default=3,
                      help="Maximum number of candidates")
    parser.add_option("--min-similarity", dest="min_similarity", type="int", default=75,
                      help="minimum similarity")
    parser.add_option("--max-length", dest="max_length", type="int", default=1000,
                      help="Maxmimum string length")
    parser.add_option("--debug", action="store_true", dest="debug", default=False,
                      help="enable debugging features")

    (options, args) = parser.parse_args()

    #setup debugging
    format = '%(asctime)s %(levelname)s %(message)s'
    level = options.debug and logging.DEBUG or logging.WARNING
    if options.debug:
        format = '%(levelname)7s %(module)s.%(funcName)s:%(lineno)d: %(message)s'
        if sys.version_info[:2] < (2, 5):
            format = '%(levelname)7s %(module)s [%(filename)s:%(lineno)d]: %(message)s'
    else:
        try:
            import psyco
            psyco.full()
        except Exception:
            pass

    logging.basicConfig(level=level, format=format)

    application = TMServer(options.tmdbfile, options.tmfiles, max_candidates=options.max_candidates,
                           min_similarity=options.min_similarity, max_length=options.max_length,
                           prefix="/tmserver", source_lang=options.source_lang, target_lang=options.target_lang)
    wsgi.launch_server(options.bind, options.port, application.rest)


if __name__ == '__main__':
    main()
