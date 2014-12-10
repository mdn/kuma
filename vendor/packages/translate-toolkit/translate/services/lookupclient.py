#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""Small example program for querying an XML-RPC lookup service"""

from translate.storage import tbx
from xml.dom import minidom
import xmlrpclib
import sys

server_url = 'http://localhost:1234/'
server = xmlrpclib.Server(server_url)
UnitClass = tbx.tbxunit

text = sys.stdin.readline()
while text:
    text = text.strip().decode("utf-8")
    if text != "":
        source = server.lookup(text)
        if source:
            print source
            #Lets assume life is simple:
            if "<termEntry>" in source:
                #TBX
                base = minidom.parseString(source)
                unit = UnitClass.createfromxmlElement(base.documentElement, None)
                #Do something interesting with unit
            elif "<tu><tuv>" in source:
                #TMX
                base = minidom.parseString
                unit = tmx.createfromxmlElement(base.documentElement, None)
            target = server.translate(text)
            print "%s -> %s".decode('utf-8') % (text, target)
        else:
            print " (Not found)"
        candidates = server.matches(text)
        #alternate example, slightly faster:
        #candidates = server.matches(text, 5, 70)
        if len(candidates):
            print "Likely matches:"
            columnwidth = min(int(len(text)*1.3)+5, 35)
            for score, original, translation in candidates:
                print "%s %-*s | %s".encode('utf-8') % (score, columnwidth, original, translation)
        else:
            print "No likely matches found"
    text = sys.stdin.readline()

