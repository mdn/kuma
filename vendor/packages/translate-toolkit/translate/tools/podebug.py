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

"""Insert debug messages into XLIFF and Gettext PO localization files

See: http://translate.sourceforge.net/wiki/toolkit/podebug for examples and
usage instructions.
"""

import os
import re

from translate.misc import hash
from translate.storage import factory
from translate.storage.placeables import StringElem, general
from translate.storage.placeables import parse as rich_parse
from translate.convert import dtd2po


def add_prefix(prefix, stringelems):
    for stringelem in stringelems:
        for string in stringelem.flatten():
            if len(string.sub) > 0:
                string.sub[0] = prefix + string.sub[0]
    return stringelems

podebug_parsers = general.parsers
podebug_parsers.remove(general.CapsPlaceable.parse)
podebug_parsers.remove(general.CamelCasePlaceable.parse)

class podebug:
    def __init__(self, format=None, rewritestyle=None, ignoreoption=None):
        if format is None:
            self.format = ""
        else:
            self.format = format
        self.rewritefunc = getattr(self, "rewrite_%s" % rewritestyle, None)
        self.ignorefunc = getattr(self, "ignore_%s" % ignoreoption, None)

    def apply_to_translatables(self, string, func):
        """Applies func to all translatable strings in string."""
        string.map(
            lambda e: e.apply_to_strings(func),
            lambda e: e.isleaf() and e.istranslatable
        )

    def rewritelist(cls):
        return [rewrite.replace("rewrite_", "") for rewrite in dir(cls) if rewrite.startswith("rewrite_")]
    rewritelist = classmethod(rewritelist)

    def _rewrite_prepend_append(self, string, prepend, append=None):
        if append is None:
            append = prepend
        if not isinstance(string, StringElem):
            string = StringElem(string)
        string.sub.insert(0, prepend)
        if unicode(string).endswith(u'\n'):
            # Try and remove the last character from the tree
            try:
                lastnode = string.flatten()[-1]
                if isinstance(lastnode.sub[-1], unicode):
                    lastnode.sub[-1] = lastnode.sub[-1].rstrip(u'\n')
            except IndexError:
                pass
            string.sub.append(append + u'\n')
        else:
            string.sub.append(append)
        return string

    def rewrite_xxx(self, string):
        return self._rewrite_prepend_append(string, u"xxx")

    def rewrite_bracket(self, string):
        return self._rewrite_prepend_append(string, u"[", u"]")

    def rewrite_en(self, string):
        if not isinstance(string, StringElem):
            string = StringElem(string)
        return string

    def rewrite_blank(self, string):
        return StringElem(u"")

    def rewrite_chef(self, string):
        """Rewrite using Mock Swedish as made famous by Monty Python"""
        if not isinstance(string, StringElem):
            string = StringElem(string)
        # From Dive into Python which itself got it elsewhere
        # http://www.renderx.com/demos/examples/diveintopython.pdf
        subs = (
               (r'a([nu])', r'u\1'),
               (r'A([nu])', r'U\1'),
               (r'a\B', r'e'),
               (r'A\B', r'E'),
               (r'en\b', r'ee'),
               (r'\Bew', r'oo'),
               (r'\Be\b', r'e-a'),
               (r'\be', r'i'),
               (r'\bE', r'I'),
               (r'\Bf', r'ff'),
               (r'\Bir', r'ur'),
               (r'(\w*?)i(\w*?)$', r'\1ee\2'),
               (r'\bow', r'oo'),
               (r'\bo', r'oo'),
               (r'\bO', r'Oo'),
               (r'the', r'zee'),
               (r'The', r'Zee'),
               (r'th\b', r't'),
               (r'\Btion', r'shun'),
               (r'\Bu', r'oo'),
               (r'\BU', r'Oo'),
               (r'v', r'f'),
               (r'V', r'F'),
               (r'w', r'w'),
               (r'W', r'W'),
               (r'([a-z])[.]', r'\1. Bork Bork Bork!'))
        for a, b in subs:
            self.apply_to_translatables(string, lambda s: re.sub(a, b, s))
        return string

    REWRITE_UNICODE_MAP = u"ȦƁƇḒḖƑƓĦĪĴĶĿḾȠǾƤɊŘŞŦŬṼẆẊẎẐ" + u"[\\]^_`" + u"ȧƀƈḓḗƒɠħīĵķŀḿƞǿƥɋřşŧŭṽẇẋẏẑ"
    def rewrite_unicode(self, string):
        """Convert to Unicode characters that look like the source string"""
        if not isinstance(string, StringElem):
            string = StringElem(string)
        def transpose(char):
            loc = ord(char)-65
            if loc < 0 or loc > 56:
                return char
            return self.REWRITE_UNICODE_MAP[loc]
        def transformer(s):
            return ''.join([transpose(c) for c in s])
        self.apply_to_translatables(string, transformer)
        return string

    REWRITE_FLIPPED_MAP = u"¡„#$%⅋,()⁎+´-·/012Ɛᔭ59Ƚ86:;<=>?@" + \
            u"∀ԐↃᗡƎℲ⅁HIſӼ⅂WNOԀÒᴚS⊥∩ɅＭX⅄Z" + u"[\\]ᵥ_," + \
            u"ɐqɔpǝɟƃɥıɾʞʅɯuodbɹsʇnʌʍxʎz"
        # Brackets should be swapped if the string will be reversed in memory.
        # If a right-to-left override is used, the brackets should be
        # unchanged.
        #Some alternatives:
        # D: ᗡ◖
        # K: Ж⋊Ӽ
        # @: Ҩ - Seems only related in Dejavu Sans
        # Q: Ὄ Ό Ὀ Ὃ Ὄ Ṑ Ò Ỏ
        # _: ‾ - left out for now for the sake of GTK accelerators
    def rewrite_flipped(self, string):
        """Convert the string to look flipped upside down."""
        if not isinstance(string, StringElem):
            string = StringElem(string)
        def transpose(char):
            loc = ord(char)-33
            if loc < 0 or loc > 89:
                return char
            return self.REWRITE_FLIPPED_MAP[loc]
        def transformer(s):
            return u"\u202e" + u''.join([transpose(c) for c in s])
            # To reverse instead of using the RTL override:
            #return u''.join(reversed([transpose(c) for c in s]))
        self.apply_to_translatables(string, transformer)
        return string

    def ignorelist(cls):
        return [ignore.replace("ignore_", "") for ignore in dir(cls) if ignore.startswith("ignore_")]
    ignorelist = classmethod(ignorelist)

    def ignore_openoffice(self, unit):
        for location in unit.getlocations():
            if location.startswith("Common.xcu#..Common.View.Localisation"):
                return True
            elif location.startswith("profile.lng#STR_DIR_MENU_NEW_"):
                return True
            elif location.startswith("profile.lng#STR_DIR_MENU_WIZARD_"):
                return True
        return False

    def ignore_mozilla(self, unit):
        locations = unit.getlocations()
        if len(locations) == 1 and locations[0].lower().endswith(".accesskey"):
            return True
        for location in locations:
            if dtd2po.is_css_entity(location):
                return True
            if location in ["brandShortName", "brandFullName", "vendorShortName"]:
                return True
            if location.lower().endswith(".commandkey") or location.endswith(".key"):
                return True
        return False

    def ignore_gtk(self, unit):
        if unit.source == "default:LTR":
            return True
        return False

    def ignore_kde(self, unit):
        if unit.source == "LTR":
            return True
        return False

    def convertunit(self, unit, prefix):
        if self.ignorefunc:
            if self.ignorefunc(unit):
                return unit
        if prefix.find("@hash_placeholder@") != -1:
            if unit.getlocations():
                hashable = unit.getlocations()[0]
            else:
                hashable = unit.source
            prefix = prefix.replace("@hash_placeholder@", hash.md5_f(hashable).hexdigest()[:self.hash_len])
        rich_source = unit.rich_source
        if not isinstance(rich_source, StringElem):
            rich_source = [rich_parse(string, podebug_parsers) for string in rich_source]
        if self.rewritefunc:
            rewritten = [self.rewritefunc(string) for string in rich_source]
            if rewritten:
                unit.rich_target = rewritten
        elif not unit.istranslated():
            unit.rich_target = unit.rich_source
        unit.rich_target = add_prefix(prefix, unit.rich_target)
        return unit

    def convertstore(self, store):
        filename = self.shrinkfilename(store.filename)
        prefix = self.format
        for formatstr in re.findall("%[0-9c]*[sfFbBdh]", self.format):
            if formatstr.endswith("s"):
                formatted = self.shrinkfilename(store.filename)
            elif formatstr.endswith("f"):
                formatted = store.filename
                formatted = os.path.splitext(formatted)[0]
            elif formatstr.endswith("F"):
                formatted = store.filename
            elif formatstr.endswith("b"):
                formatted = os.path.basename(store.filename)
                formatted = os.path.splitext(formatted)[0]
            elif formatstr.endswith("B"):
                formatted = os.path.basename(store.filename)
            elif formatstr.endswith("d"):
                formatted = os.path.dirname(store.filename)
            elif formatstr.endswith("h"):
                try:
                    self.hash_len = int(filter(str.isdigit, formatstr[1:-1]))
                except ValueError:
                    self.hash_len = 4
                formatted = "@hash_placeholder@"
            else:
                continue
            formatoptions = formatstr[1:-1]
            if formatoptions and not formatstr.endswith("h"):
                if "c" in formatoptions and formatted:
                    formatted = formatted[0] + filter(lambda x: x.lower() not in "aeiou", formatted[1:])
                length = filter(str.isdigit, formatoptions)
                if length:
                    formatted = formatted[:int(length)]
            prefix = prefix.replace(formatstr, formatted)
        for unit in store.units:
            if not unit.istranslatable():
                continue
            unit = self.convertunit(unit, prefix)
        return store

    def shrinkfilename(self, filename):
        if filename.startswith("." + os.sep):
            filename = filename.replace("." + os.sep, "", 1)
        dirname = os.path.dirname(filename)
        dirparts = dirname.split(os.sep)
        if not dirparts:
            dirshrunk = ""
        else:
            dirshrunk = dirparts[0][:4] + "-"
            if len(dirparts) > 1:
                dirshrunk += "".join([dirpart[0] for dirpart in dirparts[1:]]) + "-"
        baseshrunk = os.path.basename(filename)[:4]
        if "." in baseshrunk:
            baseshrunk = baseshrunk[:baseshrunk.find(".")]
        return dirshrunk + baseshrunk

def convertpo(inputfile, outputfile, templatefile, format=None, rewritestyle=None, ignoreoption=None):
    """Reads in inputfile, changes it to have debug strings, writes to outputfile."""
    # note that templatefile is not used, but it is required by the converter...
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty():
        return 0
    convertor = podebug(format=format, rewritestyle=rewritestyle, ignoreoption=ignoreoption)
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return 1

def main():
    from translate.convert import convert
    formats = {"po":("po", convertpo), "pot":("po", convertpo), "xlf":("xlf", convertpo)}
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    # TODO: add documentation on format strings...
    parser.add_option("-f", "--format", dest="format", default="",
        help="specify format string")
    parser.add_option("", "--rewrite", dest="rewritestyle",
        type="choice", choices=podebug.rewritelist(), metavar="STYLE",
        help="the translation rewrite style: %s" % ", ".join(podebug.rewritelist()))
    parser.add_option("", "--ignore", dest="ignoreoption",
        type="choice", choices=podebug.ignorelist(), metavar="APPLICATION",
        help="apply tagging ignore rules for the given application: %s" % ", ".join(podebug.ignorelist()))
    parser.passthrough.append("format")
    parser.passthrough.append("rewritestyle")
    parser.passthrough.append("ignoreoption")
    parser.run()


if __name__ == '__main__':
    main()
