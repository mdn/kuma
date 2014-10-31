#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2008 Zuza Software Foundation
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

"""Classes that hold units of PHP localisation files L{phpunit} or entire files
   L{phpfile}. These files are used in translating many PHP based applications.

   Only PHP files written with these conventions are supported::
      $lang['item'] = "vale";  # Array of values
      $some_entity = "value";  # Named variables

   The parser does not support other array conventions such as::
      $lang = array(
         'item1' => 'value1',
         'item2' => 'value2',
      );

   The working of PHP strings and specifically the escaping conventions which
   differ between single quote (') and double quote (") characters are outlined
   in the PHP documentation for the U{String type<http://www.php.net/language.types.string>}
"""

from translate.storage import base
import re

def phpencode(text, quotechar="'"):
    """convert Python string to PHP escaping

    The encoding is implemented for 
    U{'single quote'<http://www.php.net/manual/en/language.types.string.php#language.types.string.syntax.single>}
    and U{"double quote"<http://www.php.net/manual/en/language.types.string.php#language.types.string.syntax.double>}
    syntax.

    heredoc and nowdoc are not implemented and it is not certain whether this would 
    ever be needed for PHP localisation needs.
    """
    if not text:
        return text
    if quotechar == '"':
        # \n may be converted to \\n but we don't.  This allows us to preserve pretty layout that might have appeared in muliline entries
        # we might lose some "blah\nblah" layouts but that's probably not the most frequent use case. See bug 588
        escapes = (("\\", "\\\\"), ("\r", "\\r"), ("\t", "\\t"), ("\v", "\\v"), ("\f", "\\f"), ("\\\\$", "\\$"), ('"', '\\"'), ("\\\\", "\\"))
        for a, b in escapes:
            text = text.replace(a, b)
        return text
    else:
        return text.replace("%s" % quotechar, "\\%s" % quotechar)

def phpdecode(text, quotechar="'"):
    """convert PHP escaped string to a Python string"""
    def decode_octal_hex(match):
        """decode Octal \NNN and Hex values"""
        if match.groupdict().has_key("octal"):
            return match.groupdict()['octal'].decode("string_escape")
        elif match.groupdict().has_key("hex"):
            return match.groupdict()['hex'].decode("string_escape")
        else:
            return match.group

    if not text:
        return text
    if quotechar == '"':
        # We do not escape \$ as it is used by variables and we can't roundtrip that item.
        text = text.replace('\\"', '"').replace("\\\\", "\\")
        text = text.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\v", "\v").replace("\\f", "\f")
        text = re.sub(r"(?P<octal>\\[0-7]{1,3})", decode_octal_hex, text)
        text = re.sub(r"(?P<hex>\\x[0-9A-Fa-f]{1,2})", decode_octal_hex, text)
    else:
        text = text.replace("\\'", "'").replace("\\\\", "\\")
    return text

class phpunit(base.TranslationUnit):
    """a unit of a PHP file i.e. a name and value, and any comments
    associated"""
    def __init__(self, source=""):
        """construct a blank phpunit"""
        self.escape_type = None
        super(phpunit, self).__init__(source)
        self.name = ""
        self.value = ""
        self.translation = ""
        self._comments = []
        self.source = source

    def setsource(self, source):
        """Sets the source AND the target to be equal"""
        self.value = phpencode(source, self.escape_type)

    def getsource(self):
        return phpdecode(self.value, self.escape_type)
    source = property(getsource, setsource)

    def settarget(self, target):
        self.translation = phpencode(target, self.escape_type)

    def gettarget(self):
        return phpdecode(self.translation, self.escape_type)
    target = property(gettarget, settarget)

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """convert the unit back into formatted lines for a php file"""
        return "".join(self._comments + ["%s='%s';\n" % (self.name, self.translation or self.value)])

    def addlocation(self, location):
        self.name = location

    def getlocations(self):
        return [self.name]

    def addnote(self, text, origin=None, position="append"):
        if origin in ['programmer', 'developer', 'source code', None]:
            if position == "append":
                self._comments.append(text)
            else:
                self._comments = [text]
        else:
            return super(phpunit, self).addnote(text, origin=origin, position=position)

    def getnotes(self, origin=None):
        if origin in ['programmer', 'developer', 'source code', None]:
            return '\n'.join(self._comments)
        else:
            return super(phpunit, self).getnotes(origin)

    def removenotes(self):
        self._comments = []

    def isblank(self):
        """Returns whether this is a blank element, containing only comments."""
        return not (self.name or self.value)

    def getid(self):
        return self.name

class phpfile(base.TranslationStore):
    """This class represents a PHP file, made up of phpunits"""
    UnitClass = phpunit
    def __init__(self, inputfile=None, encoding='utf-8'):
        """construct a phpfile, optionally reading in from inputfile"""
        super(phpfile, self).__init__(unitclass = self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        self._encoding = encoding
        if inputfile is not None:
            phpsrc = inputfile.read()
            inputfile.close()
            self.parse(phpsrc)

    def parse(self, phpsrc):
        """Read the source of a PHP file in and include them as units"""
        newunit = phpunit()
        lastvalue = ""
        value = ""
        comment = []
        invalue = False
        incomment = False
        valuequote = "" # either ' or "
        for line in phpsrc.decode(self._encoding).split("\n"):
            commentstartpos = line.find("/*")
            commentendpos = line.rfind("*/")
            if commentstartpos != -1:
                incomment = True
                if commentendpos != -1:
                    newunit.addnote(line[commentstartpos:commentendpos].strip(), "developer")
                    incomment = False
                else:
                    newunit.addnote(line[commentstartpos:].strip(), "developer")
            if commentendpos != -1 and incomment:
                newunit.addnote(line[:commentendpos+2].strip(), "developer")
                incomment = False
            if incomment and commentstartpos == -1:
                newunit.addnote(line.strip(), "developer")
                continue
            equalpos = line.find("=")
            hashpos = line.find("#")
            if 0 <= hashpos < equalpos:
                # Assume that this is a '#' comment line
                newunit.addnote(line.strip(), "developer")
                continue
            if equalpos != -1 and not invalue:
                newunit.addlocation(line[:equalpos].strip().replace(" ", ""))
                value = line[equalpos+1:].lstrip()[1:]
                valuequote = line[equalpos+1:].lstrip()[0]
                lastvalue = ""
                invalue = True
            else:
                if invalue:
                    value = line
            colonpos = value.rfind(";")
            while colonpos != -1:
                if value[colonpos-1] == valuequote:
                    newunit.value = lastvalue + value[:colonpos-1] 
                    newunit.escape_type = valuequote
                    lastvalue = ""
                    invalue = False
                if not invalue and colonpos != len(value)-1:
                    commentinlinepos = value.find("//", colonpos)
                    if commentinlinepos != -1:
                        newunit.addnote(value[commentinlinepos+2:].strip(), "developer")
                if not invalue:
                    self.addunit(newunit)
                    value = ""
                    newunit = phpunit()
                colonpos = value.rfind(";", 0, colonpos)
            if invalue:
                lastvalue = lastvalue + value + "\n"

    def __str__(self):
        """Convert the units back to lines."""
        lines = []
        for unit in self.units:
            lines.append(str(unit))
        return "".join(lines)

