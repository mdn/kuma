#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2009 Zuza Software Foundation
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

"""Class to perform translation memory matching from a store of translation units"""

import heapq
import re

from translate.search import lshtein
from translate.search import terminology
from translate.storage import base
from translate.storage import po
from translate.misc.multistring import multistring


def sourcelen(unit):
    """Returns the length of the source string"""
    return len(unit.source)


class matcher(object):
    """A class that will do matching and store configuration for the matching process"""

    sort_reverse = False

    def __init__(self, store, max_candidates=10, min_similarity=75, max_length=70, comparer=None, usefuzzy=False):
        """max_candidates is the maximum number of candidates that should be assembled,
        min_similarity is the minimum similarity that must be attained to be included in
        the result, comparer is an optional Comparer with similarity() function"""
        if comparer is None:
            comparer = lshtein.LevenshteinComparer(max_length)
        self.comparer = comparer
        self.setparameters(max_candidates, min_similarity, max_length)
        self.usefuzzy = usefuzzy
        self.inittm(store)
        self.addpercentage = True

    def usable(self, unit):
        """Returns whether this translation unit is usable for TM"""
        #TODO: We might want to consider more attributes, such as approved, reviewed, etc.
        source = unit.source
        target = unit.target
        if source and target and (self.usefuzzy or not unit.isfuzzy()):
            if len(source) < 2:
                return False
            if source in self.existingunits and self.existingunits[source] == target:
                return False
            else:
                self.existingunits[source] = target
                return True
        return False

    def inittm(self, stores, reverse=False):
        """Initialises the memory for later use. We use simple base units for
        speedup."""
        # reverse is deprectated - just use self.sort_reverse
        self.existingunits = {}
        self.candidates = base.TranslationStore()

        if isinstance(stores, base.TranslationStore):
            stores = [stores]
        for store in stores:
            self.extendtm(store.units, store=store, sort=False)
        self.candidates.units.sort(key=sourcelen, reverse=self.sort_reverse)
        # print "TM initialised with %d candidates (%d to %d characters long)" % \
        #        (len(self.candidates.units), len(self.candidates.units[0].source), len(self.candidates.units[-1].source))

    def extendtm(self, units, store=None, sort=True):
        """Extends the memory with extra unit(s).

        @param units: The units to add to the TM.
        @param store: Optional store from where some metadata can be retrieved
        and associated with each unit.
        @param sort:  Optional parameter that can be set to False to supress
        sorting of the candidates list. This should probably only be used in
        inittm().
        """
        if isinstance(units, base.TranslationUnit):
            units = [units]
        candidates = filter(self.usable, units)
        for candidate in candidates:
            simpleunit = base.TranslationUnit("")
            # We need to ensure that we don't pass multistrings futher, since
            # some modules (like the native Levenshtein) can't use it.
            if isinstance(candidate.source, multistring):
                if len(candidate.source.strings) > 1:
                    simpleunit.orig_source = candidate.source
                    simpleunit.orig_target = candidate.target
                simpleunit.source = unicode(candidate.source)
                simpleunit.target = unicode(candidate.target)
            else:
                simpleunit.source = candidate.source
                simpleunit.target = candidate.target
            # If we now only get translator comments, we don't get programmer
            # comments in TM suggestions (in Pootle, for example). If we get all
            # notes, pot2po adds all previous comments as translator comments
            # in the new po file
            simpleunit.addnote(candidate.getnotes(origin="translator"))
            simpleunit.fuzzy = candidate.isfuzzy()
            self.candidates.units.append(simpleunit)
        if sort:
            self.candidates.units.sort(key=sourcelen, reverse=self.sort_reverse)

    def setparameters(self, max_candidates=10, min_similarity=75, max_length=70):
        """Sets the parameters without reinitialising the tm. If a parameter
        is not specified, it is set to the default, not ignored"""
        self.MAX_CANDIDATES = max_candidates
        self.MIN_SIMILARITY = min_similarity
        self.MAX_LENGTH = max_length

    def getstoplength(self, min_similarity, text):
        """Calculates a length beyond which we are not interested.
        The extra fat is because we don't use plain character distance only."""
        return min(len(text) / (min_similarity/100.0), self.MAX_LENGTH)

    def getstartlength(self, min_similarity, text):
        """Calculates the minimum length we are interested in.
        The extra fat is because we don't use plain character distance only."""
        return max(len(text) * (min_similarity/100.0), 1)

    def matches(self, text):
        """Returns a list of possible matches for given source text.

        @type text: String
        @param text: The text that will be search for in the translation memory
        @rtype: list
        @return: a list of units with the source and target strings from the
        translation memory. If self.addpercentage is true (default) the match
        quality is given as a percentage in the notes.
        """
        bestcandidates = [(0.0, None)]*self.MAX_CANDIDATES
        #We use self.MIN_SIMILARITY, but if we already know we have max_candidates
        #that are better, we can adjust min_similarity upwards for speedup
        min_similarity = self.MIN_SIMILARITY

        # We want to limit our search in self.candidates, so we want to ignore
        # all units with a source string that is too short or too long. We use
        # a binary search to find the shortest string, from where we start our
        # search in the candidates.

        # minimum source string length to be considered
        startlength = self.getstartlength(min_similarity, text)
        startindex = 0
        endindex = len(self.candidates.units)
        while startindex < endindex:
            mid = (startindex + endindex) // 2
            if sourcelen(self.candidates.units[mid]) < startlength:
                startindex = mid + 1
            else:
                endindex = mid

        # maximum source string length to be considered
        stoplength = self.getstoplength(min_similarity, text)
        lowestscore = 0

        for candidate in self.candidates.units[startindex:]:
            cmpstring = candidate.source
            if len(cmpstring) > stoplength:
                break
            similarity = self.comparer.similarity(text, cmpstring, min_similarity)
            if similarity < min_similarity:
                continue
            if similarity > lowestscore:
                heapq.heapreplace(bestcandidates, (similarity, candidate))
                lowestscore = bestcandidates[0][0]
                if lowestscore >= 100:
                    break
                if min_similarity < lowestscore:
                    min_similarity = lowestscore
                    stoplength = self.getstoplength(min_similarity, text)

        #Remove the empty ones:
        def notzero(item):
            score = item[0]
            return score != 0
        bestcandidates = filter(notzero, bestcandidates)
        #Sort for use as a general list, and reverse so the best one is at index 0
        bestcandidates.sort(reverse=True)
        return self.buildunits(bestcandidates)

    def buildunits(self, candidates):
        """Builds a list of units conforming to base API, with the score in the comment"""
        units = []
        for score, candidate in candidates:
            if hasattr(candidate, "orig_source"):
                candidate.source = candidate.orig_source
                candidate.target = candidate.orig_target
            newunit = po.pounit(candidate.source)
            newunit.target = candidate.target
            newunit.markfuzzy(candidate.fuzzy)
            candidatenotes = candidate.getnotes().strip()
            if candidatenotes:
                newunit.addnote(candidatenotes)
            if self.addpercentage:
                newunit.addnote("%d%%" % score)
            units.append(newunit)
        return units


# We don't want to miss certain forms of words that only change a little
# at the end. Now we are tying this code to English, but it should serve
# us well. For example "category" should be found in "categories",
# "copy" should be found in "copied"
#
# The tuples define a regular expression to search for, and with what it
# should be replaced.
ignorepatterns = [
    ("y\s*$", "ie"),          #category/categories, identify/identifies, apply/applied
    ("[\s-]+", ""),           #down time / downtime, pre-order / preorder
    ("-", " "),               #pre-order / pre order
    (" ", "-"),               #pre order / pre-order
]

context_re = re.compile("\s+\(.*\)\s*$")

class terminologymatcher(matcher):
    """A matcher with settings specifically for terminology matching"""

    sort_reverse = True

    def __init__(self, store, max_candidates=10, min_similarity=75, max_length=500, comparer=None):
        if comparer is None:
            comparer = terminology.TerminologyComparer(max_length)
        matcher.__init__(self, store, max_candidates, min_similarity=10, max_length=max_length, comparer=comparer)
        self.addpercentage = False
        self.match_info = {}

    def inittm(self, store):
        """Normal initialisation, but convert all source strings to lower case"""
        matcher.inittm(self, store)
        extras = []
        for unit in self.candidates.units:
            source = unit.source = context_re.sub("", unit.source).lower()
            for ignorepattern in ignorepatterns:
                (newterm, occurrences) = re.subn(ignorepattern[0], ignorepattern[1], source)
                if occurrences:
                    new_unit = type(unit).buildfromunit(unit)
                    new_unit.source = newterm
                    # We mark it fuzzy to indicate that it isn't pristine
                    unit.markfuzzy()
                    extras.append(new_unit)
        self.candidates.units.sort(key=sourcelen, reverse=self.sort_reverse)
        if extras:
            # We don't sort, so that the altered forms are at the back and
            # considered last.
            self.extendtm(extras, sort=False)

    def getstartlength(self, min_similarity, text):
        # Let's number false matches by not working with terms of two
        # characters or less
        return 3

    def getstoplength(self, min_similarity, text):
        # Let's ignore terms with more than 30 characters. Perhaps someone
        # gave a file with normal (long) translations
        return 30

    def usable(self, unit):
        """Returns whether this translation unit is usable for terminology."""
        if not unit.istranslated():
            return False
        l = len(context_re.sub("", unit.source))
        return l <= self.MAX_LENGTH and l >= self.getstartlength(None, None)

    def matches(self, text):
        """Normal matching after converting text to lower case. Then replace
        with the original unit to retain comments, etc."""
        text = text.lower()
        comparer = self.comparer
        comparer.match_info = {}
        matches = []
        known = set()
        for cand in self.candidates.units:
            if (cand.source, cand.target) in known:
                continue
            source = cand.source
            if comparer.similarity(text, source, self.MIN_SIMILARITY):
                self.match_info[source] = {'pos': comparer.match_info[source]['pos']}
                matches.append(cand)
                known.add((cand.source, cand.target))
        return matches


# utility functions used by virtaal and tmserver to convert matching units in easily marshallable dictionaries
def unit2dict(unit):
    """converts a pounit to a simple dict structure for use over the web"""
    return {"source": unit.source, "target": unit.target,
            "quality": _parse_quality(unit.getnotes()), "context": unit.getcontext()}

def _parse_quality(comment):
    """extracts match quality from po comments"""
    quality = re.search('([0-9]+)%', comment)
    if quality:
        return quality.group(1)
