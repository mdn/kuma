#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007-2008 Zuza Software Foundation
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

"""This module contains all the common features for languages.

   Supported features
   ==================
     - language code (km, af)
     - language name (Khmer, Afrikaans)
     - Plurals
       - Number of plurals (nplurals)
       - Plural equation
     - pofilter tests to ignore
   
   Segmentation
   ------------
     - characters
     - words
     - sentences
   
   TODOs and Ideas for possible features
   =====================================
     - Language-Team information
     - Segmentation
       - phrases
   
   Punctuation
   -----------
     - End of sentence
     - Start of sentence
     - Middle of sentence
     - Quotes
       - single
       - double
   
     - Valid characters
     - Accelerator characters
     - Special characters
     - Direction (rtl or ltr)
"""

from translate.lang import data
import re

class Common(object):
    """This class is the common parent class for all language classes."""
    
    code = ""
    """The ISO 639 language code, possibly with a country specifier or other 
    modifier.
    
    Examples::
        km
        pt_BR
        sr_YU@Latn
    """

    fullname = ""
    """The full (English) name of this language.

       Dialect codes should have the form of 
         - Khmer
         - Portugese (Brazil)
         - TODO: sr_YU@Latn?
    """
    
    nplurals = 0
    """The number of plural forms of this language.
    
    0 is not a valid value - it must be overridden.
    Any positive integer is valid (it should probably be between 1 and 6)
    @see: L{data}
    """
    
    pluralequation = "0"
    """The plural equation for selection of plural forms. 

    This is used for PO files to fill into the header.
    @see: U{Gettext manual<http://www.gnu.org/software/gettext/manual/html_node/gettext_150.html#Plural-forms>}
    @see: L{data}
    """
    # Don't change these defaults of nplurals or pluralequation willy-nilly:
    # some code probably depends on these for unrecognised languages
    
    listseperator = u", "
    """This string is used to separate lists of textual elements. Most 
    languages probably can stick with the default comma, but Arabic and some
    Asian languages might want to override this."""
    
    commonpunc = u".,;:!?-@#$%^*_()[]{}/\\'`\"<>"
    """These punctuation marks are common in English and most languages that 
    use latin script."""

    quotes = u"‘’‛“”„‟′″‴‵‶‷‹›«»"
    """These are different quotation marks used by various languages."""

    invertedpunc = u"¿¡"
    """Inveted punctuation sometimes used at the beginning of sentences in 
    Spanish, Asturian, Galician, and Catalan."""

    rtlpunc = u"،؟؛÷"
    """These punctuation marks are used by Arabic and Persian, for example."""

    CJKpunc = u"。、，；！？「」『』【】"
    """These punctuation marks are used in certain circumstances with CJK 
    languages."""

    indicpunc = u"।॥॰"
    """These punctuation marks are used by several Indic languages."""

    ethiopicpunc = u"።፤፣"
    """These punctuation marks are used by several Ethiopic languages."""

    miscpunc = u"…±°¹²³·©®×£¥€"
    """The middle dot (·) is used by Greek and Georgian."""

    punctuation = u"".join([commonpunc, quotes, invertedpunc, rtlpunc, CJKpunc,\
            indicpunc, ethiopicpunc, miscpunc])
    """We include many types of punctuation here, simply since this is only 
    meant to determine if something is punctuation. Hopefully we catch some 
    languages which might not be represented with modules. Most languages won't 
    need to override this."""

    sentenceend = u".!?…։؟।。！？።"
    """These marks can indicate a sentence end. Once again we try to account 
    for many languages. Most langauges won't need to override this."""

    #The following tries to account for a lot of things. For the best idea of 
    #what works, see test_common.py. We try to ignore abbreviations, for 
    #example, by checking that the following sentence doesn't start with lower 
    #case or numbers.
    sentencere = re.compile(r"""(?s)    #make . also match newlines
                            .*?         #anything, but match non-greedy
                            [%s]        #the puntuation for sentence ending
                            \s+         #the spacing after the puntuation
                            (?=[^a-z\d])#lookahead that next part starts with caps
                            """ % sentenceend, re.VERBOSE)
    
    puncdict = {}
    """A dictionary of punctuation transformation rules that can be used by 
    punctranslate()."""

    ignoretests = []
    """List of pofilter tests for this language that must be ignored."""

    checker = None
    """A language specific checker (see filters.checks).

    This doesn't need to be supplied, but will be used if it exists."""

    _languages = {}

    validaccel = None
    """Characters that can be used as accelerators (access keys) i.e. Alt+X 
    where X is the accelerator.  These can include combining diacritics as 
    long as they are accessible from the users keyboard in a single keystroke,
    but normally they would be at least precomposed characters. All characters,
    lower and upper, are included in the list."""

    validdoublewords = []
    """Some languages allow double words in certain cases.  This is a dictionary
    of such words."""

    def __new__(cls, code):
        """This returns the language class for the given code, following a 
        singleton like approach (only one object per language)."""
        code = code or ""
        # First see if a language object for this code already exists
        if code in cls._languages:
            return cls._languages[code]
        # No existing language. Let's build a new one and keep a copy
        language = cls._languages[code] = object.__new__(cls)

        language.code = code
        while code:
            langdata = data.languages.get(code, None)
            if langdata:
                language.fullname, language.nplurals, language.pluralequation = langdata
                break
            code = data.simplercode(code)
        if not code:
#            print >> sys.stderr, "Warning: No information found about language code %s" % code
            pass
        return language

    def __deepcopy__(self, memo={}):
        memo[id(self)] = self
        return self

    def __repr__(self):
        """Give a simple string representation without address information to 
        be able to store it in text for comparison later."""
        detail = ""
        if self.code:
            detail = "(%s)" % self.code
        return "<class 'translate.lang.common.Common%s'>" % detail

    def punctranslate(cls, text):
        """Converts the punctuation in a string according to the rules of the 
        language."""
#        TODO: look at po::escapeforpo() for performance idea
        if not text:
            return text
        ellipses_end = text.endswith(u"...")
        if ellipses_end:
            text = text[:-3]
        for source, target in cls.puncdict.iteritems():
            text = text.replace(source, target)
        if ellipses_end:
            if u"..." in cls.puncdict:
                text += cls.puncdict[u"..."]
            else:
                text += u"..."
        # Let's account for cases where a punctuation symbol plus a space is 
        # replaced, but the space won't exist at the end of a message.
        # As a simple improvement for messages ending in ellipses (...), we
        # test that the last character is different from the second last
        # This is only relevant if the string has two characters or more
        if (text[-1] + u" " in cls.puncdict) and (len(text) < 2 or text[-2] != text[-1]):
            text = text[:-1] + cls.puncdict[text[-1] + u" "].rstrip()
        return text
    punctranslate = classmethod(punctranslate)

    def length_difference(cls, len):
        """Returns an estimate to a likely change in length relative to an
        English string of length len."""
        # This is just a rudimentary heuristic guessing that most translations
        # will be somewhat longer than the source language
        expansion_factor = 0
        code = cls.code
        while code:
            expansion_factor = data.expansion_factors.get(cls.code, 0)
            if expansion_factor:
                break
            code = data.simplercode(code)
        else:
            expansion_factor = 0.1 # default
        constant = max(5, int(40*expansion_factor))
        # The default: return 5 + len/10
        return constant + int(expansion_factor * len)

    def alter_length(cls, text):
        """Converts the given string by adding or removing characters as an 
        estimation of translation length (with English assumed as source 
        language)."""
        def alter_it(text):
            l = len(text)
            if l > 9:
                extra = cls.length_difference(l)
                if extra > 0:
                    text = text[:extra].replace(u'\n', u'') + text
                else:
                    text = text[-extra:]
            return text
        expanded = []
        for subtext in text.split(u"\n\n"):
            expanded.append(alter_it(subtext))
        text = u"\n\n".join(expanded)
        return text

    def character_iter(cls, text):
        """Returns an iterator over the characters in text."""
        #We don't return more than one consecutive whitespace character
        prev = 'A'
        for c in text:
            if c.isspace() and prev.isspace():
                continue
            prev = c
            if not (c in cls.punctuation):
                yield c
    character_iter = classmethod(character_iter)

    def characters(cls, text):
        """Returns a list of characters in text."""
        return [c for c in cls.character_iter(text)]
    characters = classmethod(characters)

    def word_iter(cls, text):
        """Returns an iterator over the words in text."""
        #TODO: Consider replacing puctuation with space before split()
        for w in text.split():
            word = w.strip(cls.punctuation)
            if word:
                yield word
    word_iter = classmethod(word_iter)

    def words(cls, text):
        """Returns a list of words in text."""
        return [w for w in cls.word_iter(text)]
    words = classmethod(words)

    def sentence_iter(cls, text, strip=True):
        """Returns an iterator over the sentences in text."""
        lastmatch = 0
        text = text or ""
        iter = cls.sentencere.finditer(text)
        for item in iter:
            lastmatch = item.end()
            sentence = item.group()
            if strip: sentence = sentence.strip()
            if sentence: yield sentence
        remainder = text[lastmatch:]
        if strip: remainder = remainder.strip()
        if remainder: yield remainder
    sentence_iter = classmethod(sentence_iter)

    def sentences(cls, text, strip=True):
        """Returns a list of senteces in text."""
        return [s for s in cls.sentence_iter(text, strip=strip)]
    sentences = classmethod(sentences)

    def capsstart(cls, text):
        """Determines whether the text starts with a capital letter."""
        stripped = text.lstrip().lstrip(cls.punctuation)
        return stripped and stripped[0].isupper()
    capsstart = classmethod(capsstart)

