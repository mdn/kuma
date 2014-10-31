#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
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

"""Module to provide statistics and related functionality.

@organization: Zuza Software Foundation
@copyright: 2007 Zuza Software Foundation
@license: U{GPL <http://www.fsf.org/licensing/licenses/gpl.html>}
"""

from translate import lang
from translate.lang import factory

# calling classifyunits() in the constructor is probably not ideal. 
# idea: have a property for .classification that calls it if necessary

# If we add units or change translations, statistics are out of date
# Compare with modules/Status.py in pootling that uses a bitmask to 
# filter units

# Add support for reading and writing Pootle style .stats files

# Consider providing quickstats

class Statistics(object):
    """Manages statistics for storage objects."""

    def __init__(self, sourcelanguage='en', targetlanguage='en', checkerstyle=None):
        self.sourcelanguage = sourcelanguage
        self.targetlanguage = targetlanguage
        self.language = lang.factory.getlanguage(self.sourcelanguage)
#        self.init_checker(checkerstyle)
        
        self.classification = {}

    def init_checker(self, checkerstyle=None):
        from translate.filters import checks
        from translate.filters import pofilter
        checkerclasses = [checkerstyle or checks.StandardChecker, pofilter.StandardPOChecker]
        self.checker = pofilter.POTeeChecker(checkerclasses=checkerclasses)

    def fuzzy_units(self):
        """Return a list of fuzzy units."""
        if not self.classification:
            self.classifyunits()
        units = self.getunits()
        return [units[item] for item in self.classification["fuzzy"]]

    def fuzzy_unitcount(self):
        """Returns the number of fuzzy units."""
        return len(self.fuzzy_units())

    def translated_units(self):
        """Return a list of translated units."""
        if not self.classification:
            self.classifyunits()
        units = self.getunits()
        return [units[item] for item in self.classification["translated"]]

    def translated_unitcount(self):
        """Returns the number of translated units."""
        return len(self.translated_units())

    def untranslated_units(self):
        """Return a list of untranslated units."""
        if not self.classification:
            self.classifyunits()
        units = self.getunits()
        return [units[item] for item in self.classification["blank"]]

    def untranslated_unitcount(self):
        """Returns the number of untranslated units."""

        return len(self.untranslated_units())

    def getunits(self):
        """Returns a list of all units in this object."""
        return []

    def get_source_text(self, units):
        """Joins the unit source strings in a single string of text."""
        source_text = ""
        for unit in units:
            source_text += unit.source + "\n"
            plurals = getattr(unit.source, "strings", [])
            if plurals:
                source_text += "\n".join(plurals[1:])
        return source_text

    def wordcount(self, text):
        """Returns the number of words in the given text."""
        return len(self.language.words(text))

    def source_wordcount(self):
        """Returns the number of words in the source text."""
        source_text = self.get_source_text(self.getunits())
        return self.wordcount(source_text)

    def translated_wordcount(self):
        """Returns the number of translated words in this object."""

        text = self.get_source_text(self.translated_units())
        return self.wordcount(text)

    def untranslated_wordcount(self):
        """Returns the number of untranslated words in this object."""

        text = self.get_source_text(self.untranslated_units())
        return self.wordcount(text)

    def classifyunit(self, unit):
        """Returns a list of the classes that the unit belongs to.
        
        @param unit: the unit to classify
        """
        classes = ["total"]
        if unit.isfuzzy():
            classes.append("fuzzy")
        if unit.gettargetlen() == 0:
            classes.append("blank")
        if unit.istranslated():
            classes.append("translated")
        #TODO: we don't handle checking plurals at all yet, as this is tricky...
        source = unit.source
        target = unit.target
        if isinstance(source, str) and isinstance(target, unicode):
            source = source.decode(getattr(unit, "encoding", "utf-8"))
        #TODO: decoding should not be done here
#        checkresult = self.checker.run_filters(unit, source, target)
        checkresult = {}
        for checkname, checkmessage in checkresult.iteritems():
            classes.append("check-" + checkname)
        return classes

    def classifyunits(self):
        """Makes a dictionary of which units fall into which classifications.
        
        This method iterates over all units.
        """
        self.classification = {}
        self.classification["fuzzy"] = []
        self.classification["blank"] = []
        self.classification["translated"] = []
        self.classification["has-suggestion"] = []
        self.classification["total"] = []
#        for checkname in self.checker.getfilters().keys():
#            self.classification["check-" + checkname] = []
        for item, unit in enumerate(self.unit_iter()):
            classes = self.classifyunit(unit)
#            if self.basefile.getsuggestions(item):
#                classes.append("has-suggestion")
            for classname in classes:
                if classname in self.classification:
                    self.classification[classname].append(item)
                else:
                    self.classification[classname] = item
        self.countwords()

    def countwords(self):
        """Counts the source and target words in each of the units."""
        self.sourcewordcounts = []
        self.targetwordcounts = []
        for unit in self.unit_iter():
            self.sourcewordcounts.append([self.wordcount(text) for text in getattr(unit.source, "strings", [""])])
            self.targetwordcounts.append([self.wordcount(text) for text in getattr(unit.target, "strings", [""])])

    def reclassifyunit(self, item):
        """Updates the classification of a unit in self.classification.
        
        @param item: an integer that is an index in .getunits().
        """
        unit = self.getunits()[item]
        self.sourcewordcounts[item] = [self.wordcount(text) for text in unit.source.strings]
        self.targetwordcounts[item] = [self.wordcount(text) for text in unit.target.strings]
        classes = self.classifyunit(unit)
#        if self.basefile.getsuggestions(item):
#            classes.append("has-suggestion")
        for classname, matchingitems in self.classification.items():
            if (classname in classes) != (item in matchingitems):
                if classname in classes:
                    self.classification[classname].append(item)
                else:
                    self.classification[classname].remove(item)
                self.classification[classname].sort()
#        self.savestats()


