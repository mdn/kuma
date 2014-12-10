#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2009 Zuza Software Foundation
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

"""A class to calculate a similarity based on the Levenshtein 
distance. See http://en.wikipedia.org/wiki/Levenshtein_distance.

If available, the python-Levenshtein package will be used which will provide
better performance as it is implemented natively. See
http://trific.ath.cx/python/levenshtein/
"""

import math
import sys

def python_distance(a, b, stopvalue=-1):
    """Calculates the distance for use in similarity calculation. Python
    version."""
    l1 = len(a)
    l2 = len(b)
    if stopvalue == -1:
        stopvalue = l2
    current = range(l1+1)
    for i in range(1, l2+1):
        previous, current = current, [i]+[0]*l1
        least = l2
        for j in range(1, l1 + 1):
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            insert = previous[j] + 1
            delete = current[j-1] + 1
            current[j] = min(insert, delete, change)
            if least > current[j]:
                least = current[j]
        #The smallest value in the current array is the best (lowest) value
        #that can be attained in the end if the strings are identical further
        if least > stopvalue:
            return least

    return current[l1]

def native_distance(a, b, stopvalue=0):
    """Same as python_distance in functionality. This uses the fast C 
    version if we detected it earlier.

    Note that this does not support arbitrary sequence types, but only 
    string types."""
    return Levenshtein.distance(a, b)

try:
    import Levenshtein as Levenshtein
    distance = native_distance
except Exception:
    import logging
    logging.warning("Python-Levenshtein not found. Continuing with built-in (slower) fuzzy matching.")
    distance = python_distance

class LevenshteinComparer:
    def __init__(self, max_len=200):
        self.MAX_LEN = max_len

    def similarity(self, a, b, stoppercentage=40):
        similarity = self.similarity_real(a, b, stoppercentage)
        measurements = 1

#        chr_a = segment.characters(a)
#        chr_b = segment.characters(b)
#        if chr_a and chr_b and abs(len(chr_a) - len(a)) + abs(len(chr_b) - len(b)):
#            similarity += self.similarity_real(chr_a, chr_b, stoppercentage)
#            measurements += 1
#        else:
#            similarity *= 2
#            measurements += 1
#
#        wrd_a = segment.words(a)
#        wrd_b = segment.words(b)
#        if len(wrd_a) + len(wrd_b) > 2:
#            similarity += self.similarity_real(wrd_a, wrd_b, 0)
#            measurements += 1
        return similarity / measurements

    def similarity_real(self, a, b, stoppercentage=40):
        """Returns the similarity between a and b based on Levenshtein distance. It
           can stop prematurely as soon as it sees that a and b will be no simmilar than
           the percentage specified in stoppercentage.

           The Levenshtein distance is calculated, but the following should be noted:
               - Only the first MAX_LEN characters are considered. Long strings differing
                 at the end will therefore seem to match better than they should. See the
                 use of the variable penalty to lessen the effect of this.
               - Strings with widely different lengths give the opportunity for shortcut.
                 This is by definition of the Levenshtein distance: the distance will be 
                 at least as much as the difference in string length.
               - Calculation is stopped as soon as a similarity of stoppercentage becomes
                 unattainable. See the use of the variable stopvalue.
               - Implementation uses memory O(min(len(a), len(b))
               - Excecution time is O(len(a)*len(b))
        """
        l1, l2 = len(a), len(b)
        if l1 == 0 or l2 == 0:
            return 0
        #Let's make l1 the smallest
        if l1 > l2:
            l1, l2 = l2, l1
            a, b = b, a

        #maxsimilarity is the maximum similarity that can be attained as constrained
        #by the difference in string length
        maxsimilarity = 100 - 100.0*abs(l1 - l2)/l2
        if maxsimilarity < stoppercentage:
            return maxsimilarity * 1.0

        #Let's penalise the score in cases where we shorten strings
        penalty = 0
        if l2 > self.MAX_LEN:
            b = b[:self.MAX_LEN]
            l2 = self.MAX_LEN
            penalty += 7
            if l1 > self.MAX_LEN:
                a = a[:self.MAX_LEN]
                l1 = self.MAX_LEN
                penalty += 7

        #The actual value in the array that would represent a giveup situation:
        stopvalue = math.ceil((100.0 - stoppercentage)/100 * l2)
        dist = distance(a, b, stopvalue)
        if dist > stopvalue:
            return stoppercentage - 1.0

        #If MAX_LEN came into play, we consider the calculated distance to be 
        #representative of the distance between the whole, untrimmed strings
        if dist != 0:
            penalty = 0
        return 100 - (dist*1.0/l2)*100 - penalty


if __name__ == "__main__":
    from sys import argv
    comparer = LevenshteinComparer()
    print "Similarity:\n%s" % comparer.similarity(argv[1], argv[2], 50)
