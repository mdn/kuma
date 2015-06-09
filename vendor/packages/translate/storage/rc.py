#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006,2008-2009 Zuza Software Foundation
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

"""Classes that hold units of .rc files (:class:`rcunit`) or entire files
(:class:`rcfile`) used in translating Windows Resources.

.. note:::

   This implementation is based mostly on observing WINE .rc files,
   these should mimic other non-WINE .rc files.
"""

import re

from translate.storage import base


def escape_to_python(string):
    """Escape a given .rc string into a valid Python string."""
    pystring = re.sub('"\s*\\\\\n\s*"', "", string)   # xxx"\n"xxx line continuation
    pystring = re.sub("\\\\\\\n", "", pystring)       # backslash newline line continuation
    pystring = re.sub("\\\\n", "\n", pystring)        # Convert escaped newline to a real newline
    pystring = re.sub("\\\\t", "\t", pystring)        # Convert escape tab to a real tab
    pystring = re.sub("\\\\\\\\", "\\\\", pystring)   # Convert escape backslash to a real escaped backslash
    return pystring


def escape_to_rc(string):
    """Escape a given Python string into a valid .rc string."""
    rcstring = re.sub("\\\\", "\\\\\\\\", string)
    rcstring = re.sub("\t", "\\\\t", rcstring)
    rcstring = re.sub("\n", "\\\\n", rcstring)
    return rcstring


class rcunit(base.TranslationUnit):
    """A unit of an rc file"""

    def __init__(self, source="", encoding="cp1252"):
        """Construct a blank rcunit."""
        super(rcunit, self).__init__(source)
        self.name = ""
        self._value = ""
        self.comments = []
        self.source = source
        self.match = None
        self.encoding = encoding

    def setsource(self, source):
        """Sets the source AND the target to be equal"""
        self._rich_source = None
        self._value = source or ""

    def getsource(self):
        return self._value

    source = property(getsource, setsource)

    def settarget(self, target):
        """.. note:: This also sets the ``.source`` attribute!"""
        self._rich_target = None
        self.source = target

    def gettarget(self):
        return self.source
    target = property(gettarget, settarget)

    def __str__(self):
        """Convert to a string. Double check that unicode is handled somehow here."""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """Convert the element back into formatted lines for a .rc file."""
        if self.isblank():
            return "".join(self.comments + ["\n"])
        else:
            return "".join(self.comments + ["%s=%s\n" % (self.name, self.value)])

    def getlocations(self):
        return [self.name]

    def addnote(self, text, origin=None, position="append"):
        self.comments.append(text)

    def getnotes(self, origin=None):
        return '\n'.join(self.comments)

    def removenotes(self):
        self.comments = []

    def isblank(self):
        """Returns whether this is a blank element, containing only comments."""
        return not (self.name or self.value)


class rcfile(base.TranslationStore):
    """This class represents a .rc file, made up of rcunits."""
    UnitClass = rcunit

    def __init__(self, inputfile=None, lang=None, sublang=None, encoding="cp1252"):
        """Construct an rcfile, optionally reading in from inputfile."""
        self.encoding = encoding
        super(rcfile, self).__init__(unitclass=self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        self.lang = lang
        self.sublang = sublang
        if inputfile is not None:
            rcsrc = inputfile.read().decode(encoding)
            inputfile.close()
            self.parse(rcsrc)

    def parse(self, rcsrc):
        """Read the source of a .rc file in and include them as units."""
        BLOCKS_RE = re.compile("""
                         (?:
                         LANGUAGE\s+[^\n]*|                              # Language details
                         /\*.*?\*/[^\n]*|                                      # Comments
                         \/\/[^\n\r]*|                                  # One line comments
                         (?:[0-9A-Z_]+\s+(?:MENU|DIALOG|DIALOGEX|TEXTINCLUDE)|STRINGTABLE)\s  # Translatable section or include text (visual studio)
                         .*?
                         (?:
                         BEGIN(?:\s*?POPUP.*?BEGIN.*?END\s*?)+?END|BEGIN.*?END|  # FIXME Need a much better approach to nesting menus
                         {(?:\s*?POPUP.*?{.*?}\s*?)+?}|{.*?})+[\n]|
                         \s*[\n]         # Whitespace
                         )
                         """, re.DOTALL + re.VERBOSE)
        STRINGTABLE_RE = re.compile("""
                         (?P<name>[0-9A-Za-z_]+?),?\s*
                         L?"(?P<value>.*?)"\s*[\n]
                         """, re.DOTALL + re.VERBOSE)
        DIALOG_RE = re.compile("""
                         (?P<type>AUTOCHECKBOX|AUTORADIOBUTTON|CAPTION|Caption|CHECKBOX|CTEXT|CONTROL|DEFPUSHBUTTON|
                         GROUPBOX|LTEXT|PUSHBUTTON|RADIOBUTTON|RTEXT)  # Translatable types
                         \s+
                         L?                                    # Unkown prefix see ./dlls/shlwapi/shlwapi_En.rc
                         "(?P<value>.*?)"                                      # String value
                         (?:\s*,\s*|[\n])                          # FIXME ./dlls/mshtml/En.rc ID_DWL_DIALOG.LTEXT.ID_DWL_STATUS
                         (?P<name>.*?|)\s*(?:/[*].*?[*]/|),
                         """, re.DOTALL + re.VERBOSE)
        MENU_RE = re.compile("""
                         (?P<type>POPUP|MENUITEM)
                         \s+
                         "(?P<value>.*?)"                                      # String value
                         (?:\s*,?\s*)?
                         (?P<name>[^\s]+).*?[\n]
                         """, re.DOTALL + re.VERBOSE)

        processsection = False
        self.blocks = BLOCKS_RE.findall(rcsrc)
        for blocknum, block in enumerate(self.blocks):
            processblock = None
            if block.startswith("LANGUAGE"):
                if self.lang is None or self.sublang is None or re.match("LANGUAGE\s+%s,\s*%s\s*$" % (self.lang, self.sublang), block) is not None:
                    processsection = True
                else:
                    processsection = False
            else:
                if re.match(".+LANGUAGE\s+[0-9A-Za-z_]+,\s*[0-9A-Za-z_]+\s*[\n]", block, re.DOTALL) is not None:
                    if re.match(".+LANGUAGE\s+%s,\s*%s\s*[\n]" % (self.lang, self.sublang), block, re.DOTALL) is not None:
                        processblock = True
                    else:
                        processblock = False

            if not (processblock or (processsection and processblock is None)):
                continue

            if block.startswith("STRINGTABLE"):
                for match in STRINGTABLE_RE.finditer(block):
                    if not match.groupdict()['value']:
                        continue
                    newunit = rcunit(escape_to_python(match.groupdict()['value']))
                    newunit.name = "STRINGTABLE." + match.groupdict()['name']
                    newunit.match = match
                    self.addunit(newunit)
            if block.startswith("/*"):  # Comments
                continue
            if block.startswith("//"):  # One line comments
                continue
            if re.match("[0-9A-Z_]+\s+TEXTINCLUDE", block) is not None:  # TEXTINCLUDE is editor specific, not part of the app.
                continue
            if re.match("[0-9A-Z_]+\s+DIALOG", block) is not None:
                dialog = re.match("(?P<dialogname>[0-9A-Z_]+)\s+(?P<dialogtype>DIALOGEX|DIALOG)", block).groupdict()
                dialogname = dialog["dialogname"]
                dialogtype = dialog["dialogtype"]
                for match in DIALOG_RE.finditer(block):
                    if not match.groupdict()['value']:
                        continue
                    type = match.groupdict()['type']
                    value = match.groupdict()['value']
                    name = match.groupdict()['name']
                    newunit = rcunit(escape_to_python(value))
                    if type == "CAPTION" or type == "Caption":
                        newunit.name = "%s.%s.%s" % (dialogtype, dialogname, type)
                    elif name == "-1":
                        newunit.name = "%s.%s.%s.%s" % (dialogtype, dialogname, type, value.replace(" ", "_"))
                    else:
                        newunit.name = "%s.%s.%s.%s" % (dialogtype, dialogname, type, name)
                    newunit.match = match
                    self.addunit(newunit)
            if re.match("[0-9A-Z_]+\s+MENU", block) is not None:
                menuname = re.match("(?P<menuname>[0-9A-Z_]+)\s+MENU", block).groupdict()["menuname"]
                for match in MENU_RE.finditer(block):
                    if not match.groupdict()['value']:
                        continue
                    type = match.groupdict()['type']
                    value = match.groupdict()['value']
                    name = match.groupdict()['name']
                    newunit = rcunit(escape_to_python(value))
                    if type == "POPUP":
                        newunit.name = "MENU.%s.%s" % (menuname, type)
                    elif name == "-1":
                        newunit.name = "MENU.%s.%s.%s" % (menuname, type, value.replace(" ", "_"))
                    else:
                        newunit.name = "MENU.%s.%s.%s" % (menuname, type, name)
                    newunit.match = match
                    self.addunit(newunit)

    def __str__(self):
        """Convert the units back to lines."""
        return "".join(self.blocks)
