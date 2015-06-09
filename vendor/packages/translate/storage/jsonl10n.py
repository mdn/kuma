#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007,2009-2011 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
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

r"""Class that manages JSON data files for translation

JSON is an acronym for JavaScript Object Notation, it is an open standard
designed for human-readable data interchange.

JSON basic types:

- Number (integer or real)
- String (double-quoted Unicode with backslash escaping)
- Boolean (true or false)
- Array (an ordered sequence of values, comma-separated and enclosed in square
  brackets)
- Object (a collection of key:value pairs, comma-separated and enclosed in
  curly braces)
- null

Example:

.. code-block:: json

   {
        "firstName": "John",
        "lastName": "Smith",
        "age": 25,
        "address": {
            "streetAddress": "21 2nd Street",
            "city": "New York",
            "state": "NY",
            "postalCode": "10021"
        },
        "phoneNumber": [
            {
              "type": "home",
              "number": "212 555-1234"
            },
            {
              "type": "fax",
              "number": "646 555-4567"
            }
        ]
   }


TODO:

- Handle ``\u`` and other escapes in Unicode
- Manage data type storage and conversion. True --> "True" --> True
- Sort the extracted data to the order of the JSON file

"""

import json
import os
from cStringIO import StringIO

from translate.storage import base


class JsonUnit(base.TranslationUnit):
    """A JSON entry"""

    def __init__(self, source=None, ref=None, item=None, encoding="UTF-8"):
        self._id = None
        self._item = str(os.urandom(30))
        if item is not None:
            self._item = item
        self._ref = {}
        if ref is not None:
            self._ref = ref
        if ref is None and item is None:
            self._ref[self._item] = ""
        if source:
            self.source = source
        super(JsonUnit, self).__init__(source)

    def getsource(self):
        return self.gettarget()

    def setsource(self, source):
        self.settarget(source)
    source = property(getsource, setsource)

    def gettarget(self):

        def change_type(value):
            if isinstance(value, bool):
                return str(value)
            return value

            return newvalue
        if isinstance(self._ref, list):
            return change_type(self._ref[self._item])
        elif isinstance(self._ref, dict):
            return change_type(self._ref[self._item])

    def settarget(self, target):

        def change_type(oldvalue, newvalue):
            if isinstance(oldvalue, bool):
                newvalue = bool(newvalue)
            return newvalue

        if isinstance(self._ref, list):
            self._ref[int(self._item)] = change_type(self._ref[int(self._item)],
                                                     target)
        elif isinstance(self._ref, dict):
            self._ref[self._item] = change_type(self._ref[self._item], target)
        else:
            raise ValueError("We don't know how to handle:\n"
                             "Type: %s\n"
                             "Value: %s" % (type(self._ref), target))
    target = property(gettarget, settarget)

    def setid(self, value):
        self._id = value

    def getid(self):
        return self._id

    def getlocations(self):
        return [self.getid()]


class JsonFile(base.TranslationStore):
    """A JSON file"""
    UnitClass = JsonUnit

    def __init__(self, inputfile=None, unitclass=UnitClass, filter=None):
        """construct a JSON file, optionally reading in from inputfile."""
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self._filter = filter
        self.filename = ''
        self._file = u''
        if inputfile is not None:
            self.parse(inputfile)

    def __str__(self):
        return json.dumps(self._file, sort_keys=True,
                          indent=4, ensure_ascii=False).encode('utf-8')

    def _extract_translatables(self, data, stop=None, prev="", name_node=None,
                               name_last_node=None, last_node=None):
        """Recursive function to extract items from the data files

        :param data: the current branch to walk down
        :param stop: a list of leaves to extract or None to extract everything
        :param prev: the heirarchy of the tree at this iteration
        :param name_node:
        :param name_last_node: the name of the last node
        :param last_node: the last list or dict
        """
        if isinstance(data, dict):
            for k, v in data.iteritems():
                for x in self._extract_translatables(v, stop,
                                                          "%s.%s" % (prev, k),
                                                          k, None, data):
                    yield x
        elif isinstance(data, list):
            for i, item in enumerate(data):
                for x in self._extract_translatables(item, stop,
                                                          "%s[%s]" % (prev, i),
                                                          i, name_node, data):
                    yield x
        # apply filter
        elif (stop is None or
              (isinstance(last_node, dict) and name_node in stop) or
              (isinstance(last_node, list) and name_last_node in stop)):

            if isinstance(data, str) or isinstance(data, unicode):
                yield (prev, data, last_node, name_node)
            elif isinstance(data, bool):
                yield (prev, str(data), last_node, name_node)
            elif data is None:
                pass
            else:
                raise ValueError("We don't handle these values:\n"
                                 "Type: %s\n"
                                 "Data: %s\n"
                                 "Previous: %s" % (type(data), data, prev))

    def parse(self, input):
        """parse the given file or file source string"""
        if hasattr(input, 'name'):
            self.filename = input.name
        elif not getattr(self, 'filename', ''):
            self.filename = ''
        if hasattr(input, "read"):
            src = input.read()
            input.close()
            input = src
        if isinstance(input, str):
            input = StringIO(input)
        try:
            self._file = json.load(input)
        except ValueError as e:
            raise base.ParseError(e.message)

        for k, data, ref, item in self._extract_translatables(self._file,
                                                stop=self._filter):
            unit = self.UnitClass(data, ref, item)
            unit.setid(k)
            self.addunit(unit)
