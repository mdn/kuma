#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2011 Zuza Software Foundation
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

"""class that handles all header functions for a header in a po file"""

import re
import time

try:
    from collections import OrderedDict
except ImportError:
    # Python <= 2.6 fallback
    from translate.misc.dictutils import ordereddict as OrderedDict

from translate import __version__
from translate.misc.dictutils import cidict


author_re = re.compile(r".*<\S+@\S+>.*\d{4,4}")

default_header = {
    "Project-Id-Version": "PACKAGE VERSION",
    "PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
    "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
    "Language-Team": "LANGUAGE <LL@li.org>",
    "Plural-Forms": "nplurals=INTEGER; plural=EXPRESSION;",
}


def parseheaderstring(input):
    """Parses an input string with the definition of a PO header and returns
    the interpreted values as a dictionary."""
    headervalues = OrderedDict()
    for line in input.split("\n"):
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        #We don't want unicode keys
        key = str(key.strip())
        headervalues[key] = value.strip()
    return headervalues


def tzstring():
    """Returns the timezone as a string in the format [+-]0000, eg +0200.

    :rtype: str"""
    if time.daylight:
        tzoffset = time.altzone
    else:
        tzoffset = time.timezone

    hours, minutes = time.gmtime(abs(tzoffset))[3:5]
    if tzoffset > 0:
        hours *= -1
    tz = str("%+d" % hours).zfill(3) + str(minutes).zfill(2)
    return tz


def update(existing, add=False, **kwargs):
    """Update an existing header dictionary with the values in kwargs, adding new values
    only if add is true.

    :return: Updated dictionary of header entries
    :rtype: dict
    """
    headerargs = OrderedDict()
    fixedargs = cidict()
    for key, value in kwargs.items():
        key = key.replace("_", "-")
        if key.islower():
            key = key.title()
        fixedargs[key] = value
    removed = []
    for key in poheader.header_order:
        if key in existing:
            if key in fixedargs:
                headerargs[key] = fixedargs.pop(key)
            else:
                headerargs[key] = existing[key]
            removed.append(key)
        elif add and key in fixedargs:
            headerargs[key] = fixedargs.pop(key)
    for key, value in existing.iteritems():
        if not key in removed:
            headerargs[key] = value
    if add:
        for key in fixedargs:
            headerargs[key] = fixedargs[key]
    return headerargs


class poheader(object):
    """This class implements functionality for manipulation of po file headers.
    This class is a mix-in class and useless on its own. It must be used from all
    classes which represent a po file"""

    x_generator = "Translate Toolkit %s" % __version__.sver

    header_order = [
        "Project-Id-Version",
        "Report-Msgid-Bugs-To",
        "POT-Creation-Date",
        "PO-Revision-Date",
        "Last-Translator",
        "Language-Team",
        "Language",
        "MIME-Version",
        "Content-Type",
        "Content-Transfer-Encoding",
        "Plural-Forms",
        "X-Generator",
    ]

    def init_headers(self, charset='UTF-8', encoding='8bit', **kwargs):
        """sets default values for po headers"""
        #FIXME: we need to allow at least setting target language, pluralforms and generator
        headerdict = self.makeheaderdict(charset=charset, encoding=encoding, **kwargs)
        self.updateheader(add=True, **headerdict)
        return self.header()

    def makeheaderdict(self,
            charset="CHARSET",
            encoding="ENCODING",
            project_id_version=None,
            pot_creation_date=None,
            po_revision_date=None,
            last_translator=None,
            language_team=None,
            mime_version=None,
            plural_forms=None,
            report_msgid_bugs_to=None,
            **kwargs):
        """Create a header dictionary with useful defaults.

        pot_creation_date can be None (current date) or a value (datetime or string)
        po_revision_date can be None (form), False (=pot_creation_date), True (=now),
        or a value (datetime or string)

        :return: Dictionary with the header items
        :rtype: dict
        """
        if project_id_version is None:
            project_id_version = "PACKAGE VERSION"
        if pot_creation_date is None or pot_creation_date == True:
            pot_creation_date = time.strftime("%Y-%m-%d %H:%M") + tzstring()
        if isinstance(pot_creation_date, time.struct_time):
            pot_creation_date = time.strftime("%Y-%m-%d %H:%M", pot_creation_date) + tzstring()
        if po_revision_date is None:
            po_revision_date = "YEAR-MO-DA HO:MI+ZONE"
        elif po_revision_date == False:
            po_revision_date = pot_creation_date
        elif po_revision_date == True:
            po_revision_date = time.strftime("%Y-%m-%d %H:%M") + tzstring()
        if isinstance(po_revision_date, time.struct_time):
            po_revision_date = time.strftime("%Y-%m-%d %H:%M", po_revision_date) + tzstring()
        if last_translator is None:
            last_translator = "FULL NAME <EMAIL@ADDRESS>"
        if language_team is None:
            language_team = "LANGUAGE <LL@li.org>"
        if mime_version is None:
            mime_version = "1.0"
        if report_msgid_bugs_to is None:
            report_msgid_bugs_to = ""

        defaultargs = OrderedDict()
        defaultargs["Project-Id-Version"] = project_id_version
        defaultargs["Report-Msgid-Bugs-To"] = report_msgid_bugs_to
        defaultargs["POT-Creation-Date"] = pot_creation_date
        defaultargs["PO-Revision-Date"] = po_revision_date
        defaultargs["Last-Translator"] = last_translator
        defaultargs["Language-Team"] = language_team
        defaultargs["MIME-Version"] = mime_version
        defaultargs["Content-Type"] = "text/plain; charset=%s" % charset
        defaultargs["Content-Transfer-Encoding"] = encoding
        if plural_forms:
            defaultargs["Plural-Forms"] = plural_forms
        defaultargs["X-Generator"] = self.x_generator

        return update(defaultargs, add=True, **kwargs)

    def header(self):
        """Returns the header element, or None. Only the first element is allowed
        to be a header. Note that this could still return an empty header element,
        if present."""
        if len(self.units) == 0:
            return None
        candidate = self.units[0]
        if candidate.isheader():
            return candidate
        else:
            return None

    def parseheader(self):
        """Parses the PO header and returns the interpreted values as a
        dictionary."""
        header = self.header()
        if not header:
            return {}
        return parseheaderstring(header.target)

    def updateheader(self, add=False, **kwargs):
        """Updates the fields in the PO style header.

        This will create a header if add == True."""
        header = self.header()
        if not header:
            if add:
                header = self.makeheader(**kwargs)
                self._insert_header(header)
        else:
            headeritems = update(self.parseheader(), add, **kwargs)
            keys = headeritems.keys()
            if not "Content-Type" in keys or "charset=CHARSET" in headeritems["Content-Type"]:
                headeritems["Content-Type"] = "text/plain; charset=UTF-8"
            if not "Content-Transfer-Encoding" in keys or "ENCODING" in headeritems["Content-Transfer-Encoding"]:
                headeritems["Content-Transfer-Encoding"] = "8bit"
            headerString = ""
            for key, value in headeritems.items():
                if value is not None:
                    headerString += "%s: %s\n" % (key, value)
            header.target = headerString
            header.markfuzzy(False)    # TODO: check why we do this?
        return header

    def _insert_header(self, header):
        # we should be using .addunit() or some equivalent in case the
        # unit needs to refer back to the store, etc. This might be
        # subtly broken for POXLIFF, since we don't dupliate the code
        # from lisa::addunit().
        header._store = self
        self.units.insert(0, header)

    def getheaderplural(self):
        """Returns the nplural and plural values from the header."""
        header = self.parseheader()
        pluralformvalue = header.get('Plural-Forms', None)
        if pluralformvalue is None:
            return None, None
        nplural = re.findall("nplurals=(.+?);", pluralformvalue)
        plural = re.findall("plural=(.+?);?$", pluralformvalue)
        if not nplural or nplural[0] == "INTEGER":
            nplural = None
        else:
            nplural = nplural[0]
        if not plural or plural[0] == "EXPRESSION":
            plural = None
        else:
            plural = plural[0]
        return nplural, plural

    def updateheaderplural(self, nplurals, plural):
        """Update the Plural-Form PO header."""
        if isinstance(nplurals, basestring):
            nplurals = int(nplurals)
        self.updateheader(add=True, Plural_Forms="nplurals=%d; plural=%s;" % (nplurals, plural))

    def gettargetlanguage(self):
        """Return the target language based on information in the header.

        The target language is determined in the following sequence:
          1. Use the 'Language' entry in the header.
          2. Poedit's custom headers.
          3. Analysing the 'Language-Team' entry.
        """
        header = self.parseheader()
        lang = header.get('Language', None)
        if lang is not None:
            from translate.lang.data import langcode_ire
            if langcode_ire.match(lang):
                return lang
            else:
                lang = None
        if 'X-Poedit-Language' in header:
            from translate.lang import poedit
            language = header.get('X-Poedit-Language')
            country = header.get('X-Poedit-Country')
            return poedit.isocode(language, country)
        if 'Language-Code' in header:  # Used in Plone files
            return header.get('Language-Code')
        if 'Language-Team' in header:
            from translate.lang.team import guess_language
            return guess_language(header.get('Language-Team'))
        return None

    def settargetlanguage(self, lang):
        """Set the target language in the header.

        This removes any custom Poedit headers if they exist.

        :param lang: the new target language code
        :type lang: str
        """
        if isinstance(lang, basestring) and len(lang) > 1:
            self.updateheader(add=True, Language=lang, X_Poedit_Language=None, X_Poedit_Country=None)

    def getprojectstyle(self):
        """Return the project based on information in the header.

        The project is determined in the following sequence:
          1. Use the 'X-Project-Style' entry in the header.
          2. Use 'Report-Msgid-Bug-To' entry
          3. Use the 'X-Accelerator' entry
          4. Use the Project ID
          5. Analyse the file itself (not yet implemented)
        """
        header = self.parseheader()
        project = header.get('X-Project-Style', None)
        if project is not None:
            return project
        bug_address = header.get('Report-Msgid-Bugs-To', None)
        if bug_address is not None:
            if 'bugzilla.gnome.org' in bug_address:
                return 'gnome'
            if 'bugs.kde.org' in bug_address:
                return 'kde'
        accelerator = header.get('X-Accelerator-Marker', None)
        if accelerator is not None:
            if accelerator == "~":
                return "openoffice"
            elif accelerator == "&":
                return "mozilla"
        project_id = header.get('Project-Id-Version', None)
        if project_id is not None:
            if 'gnome' in project_id.lower():
                return "gnome"
        # TODO Call some project guessing code and probably move all of the above there also
        return None

    def setprojectstyle(self, project_style):
        """Set the project in the header.

        :param project_style: the new project
        :type project_style: str
        """
        from translate.filters.checks import projectcheckers
        if project_style in projectcheckers:
            self.updateheader(add=True, X_Project_Style=project_style)

    def mergeheaders(self, otherstore):
        """Merges another header with this header.

        This header is assumed to be the template.

        :type otherstore: :class:`~translate.storage.base.TranslationStore`
        """

        newvalues = otherstore.parseheader()
        retain_list = ("Project-Id-Version", "PO-Revision-Date", "Last-Translator",
                       "Language-Team", "Plural-Forms")
        retain = dict((key, newvalues[key]) for key in retain_list if newvalues.get(key, None) and newvalues[key] != default_header.get(key, None))
        self.updateheader(**retain)

    def updatecontributor(self, name, email=None):
        """Add contribution comments if necessary."""
        header = self.header()
        if not header:
            return
        prelines = []
        contriblines = []
        postlines = []
        contribexists = False
        incontrib = False
        outcontrib = False
        for line in header.getnotes("translator").split('\n'):
            line = line.strip()
            if line == u"FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.":
                incontrib = True
                continue
            if author_re.match(line):
                incontrib = True
                contriblines.append(line)
                continue
            if line == "" and incontrib:
                incontrib = False
                outcontrib = True
            if incontrib:
                contriblines.append(line)
            elif not outcontrib:
                prelines.append(line)
            else:
                postlines.append(line)

        year = time.strftime("%Y")
        contribexists = False
        for i in range(len(contriblines)):
            line = contriblines[i]
            if name in line and (email is None or email in line):
                contribexists = True
                if year in line:
                    break
                else:
                    #The contributor is there, but not for this year
                    if line[-1] == '.':
                        line = line[:-1]
                    contriblines[i] = "%s, %s." % (line, year)

        if not contribexists:
            # Add a new contributor
            if email:
                contriblines.append("%s <%s>, %s." % (name, email, year))
            else:
                contriblines.append("%s, %s." % (name, year))

        header.removenotes()
        header.addnote("\n".join(prelines))
        header.addnote("\n".join(contriblines))
        header.addnote("\n".join(postlines))

    def makeheader(self, **kwargs):
        """Create a header for the given filename.

        Check .makeheaderdict() for information on parameters."""
        headerpo = self.UnitClass("", encoding=self._encoding)
        headerpo.markfuzzy()
        headeritems = self.makeheaderdict(**kwargs)
        headervalue = ""
        for (key, value) in headeritems.items():
            if value is None:
                continue
            headervalue += "%s: %s\n" % (key, value)
        headerpo.target = headervalue
        return headerpo
