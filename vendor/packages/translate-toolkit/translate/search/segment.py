#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006 Zuza Software Foundation
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

"""Module to deal with different types and uses of segmentation"""

#XXX: This module is now deprecated: Use language specific segmenters in the
# lang package (character_iter, word_iter, sentence_iter, etc.).

punctuation = u".,;:!?-@#$%^*_()[]{}/\\'\"<>‘’‚‛“”„‟′″‴‵‶‷‹›«»±³¹²°¿©®×£¥"

def character_iter(text):
    """Returns an iterator over the characters in text."""
    #We don't return more than one consecutive whitespace character
    prev = 'A'
    for c in text:
        if c.isspace() and prev.isspace():
            continue
        prev = c
        if not (c in punctuation):
            yield c.lower()

def characters(text):
    """Returns a list of characters in text."""
    return [c for c in character_iter(text)]

def word_iter(text):
    """Returns an iterator over the words in text."""
    #TODO: Consider replacing puctuation with space before split()
    for w in text.split():
        yield w.strip(punctuation).lower()

def words(text):
    """Returns a list of words in text."""
    return [w for w in word_iter(text)]

def sentence_iter(text):
    """Returns an iterator over the senteces in text."""
    #TODO: This is very naïve. We really should consider all punctuation,
    #and return the punctuation with the sentence.
    #TODO: Search for capital letter start with next sentence to avoid
    #confusion with abbreviations. And remember Afrikaans "'n" :-)
    for s in text.split(". "):
        yield s.strip()

def sentences(text):
    """Returns a list of senteces in text."""
    return [s for s in sentence_iter(text)]
