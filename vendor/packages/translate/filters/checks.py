#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2011 Zuza Software Foundation
# 2013 F Wolff
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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""This is a set of validation checks that can be performed on translation
units.

Derivatives of UnitChecker (like StandardUnitChecker) check translation units,
and derivatives of TranslationChecker (like StandardChecker) check
(source, target) translation pairs.

When adding a new test here, please document and explain their behaviour on the
:doc:`pofilter tests </commands/pofilter_tests>` page.
"""

import logging
import re

from translate.filters import decoration, helpers, prefilters, spelling
from translate.filters.decorators import (cosmetic, critical, extraction,
                                          functional)
from translate.lang import data, factory
from translate.misc import lru


logger = logging.getLogger(__name__)

# These are some regular expressions that are compiled for use in some tests

# printf syntax based on http://en.wikipedia.org/wiki/Printf which doesn't
# cover everything we leave \w instead of specifying the exact letters as
# this should capture printf types defined in other platforms.
# Extended to support Python named format specifiers and objective-C special
# "%@" format specifier
# (see https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/Strings/Articles/formatSpecifiers.html)
printf_pat = re.compile('''
        %(                          # initial %
        (?P<boost_ord>\d+)%         # boost::format style variable order, like %1%
        |
              (?:(?P<ord>\d+)\$|    # variable order, like %1$s
              \((?P<key>\w+)\))?    # Python style variables, like %(var)s
        (?P<fullvar>
            [+#-]*                  # flags
            (?:\d+)?                # width
            (?:\.\d+)?              # precision
            (hh\|h\|l\|ll)?         # length formatting
            (?P<type>[\w@]))        # type (%s, %d, etc.)
        )''', re.VERBOSE)

# The name of the XML tag
tagname_re = re.compile("<[\s]*([\w\/]*).*?(/)?[\s]*>", re.DOTALL)

# We allow escaped quotes, probably for old escaping style of OOo helpcontent
#TODO: remove escaped strings once usage is audited
property_re = re.compile(" (\w*)=((\\\\?\".*?\\\\?\")|(\\\\?'.*?\\\\?'))")

# The whole tag
tag_re = re.compile("<[^>]+>")

gconf_attribute_re = re.compile('"[a-z_]+?"')

# XML/HTML tags in LibreOffice help and readme, exclude short tags
lo_tag_re = re.compile('''<[/]??[a-z][a-z_\-]+?(?:| +[a-z]+?=".*?") *>''')

def tagname(string):
    """Returns the name of the XML/HTML tag in string"""
    tagname_match = tagname_re.match(string)
    return tagname_match.groups(1)[0] + tagname_match.groups('')[1]


def intuplelist(pair, list):
    """Tests to see if pair == (a,b,c) is in list, but handles None entries in
    list as wildcards (only allowed in positions "a" and "c"). We take a
    shortcut by only considering "c" if "b" has already matched."""
    a, b, c = pair

    if (b, c) == (None, None):
        #This is a tagname
        return pair

    for pattern in list:
        x, y, z = pattern

        if (x, y) in [(a, b), (None, b)]:
            if z in [None, c]:
                return pattern

    return pair


def tagproperties(strings, ignore):
    """Returns all the properties in the XML/HTML tag string as
    (tagname, propertyname, propertyvalue), but ignore those combinations
    specified in ignore."""
    properties = []

    for string in strings:
        tag = tagname(string)
        properties += [(tag, None, None)]
        #Now we isolate the attribute pairs.
        pairs = property_re.findall(string)

        for property, value, a, b in pairs:
            #Strip the quotes:
            value = value[1:-1]

            canignore = False

            if (tag, property, value) in ignore or \
               intuplelist((tag, property, value), ignore) != (tag, property, value):
                canignore = True
                break

            if not canignore:
                properties += [(tag, property, value)]

    return properties


class FilterFailure(Exception):
    """This exception signals that a Filter didn't pass, and gives an
    explanation or a comment.
    """

    def __init__(self, messages):
        if not isinstance(messages, list):
            messages = [messages]

        assert isinstance(messages[0], unicode)  # Assumption: all of same type

        self.messages = messages

    def __unicode__(self):
        return unicode(u", ".join(self.messages))

    def __str__(self):
        return str(u", ".join(self.messages))


class SeriousFilterFailure(FilterFailure):
    """This exception signals that a Filter didn't pass, and the bad translation
    might break an application (so the string will be marked fuzzy)"""
    pass

#(tag, attribute, value) specifies a certain attribute which can be changed/
#ignored if it exists inside tag. In the case where there is a third element
#in the tuple, it indicates a property value that can be ignored if present
#(like defaults, for example)
#If a certain item is None, it indicates that it is relevant for all values of
#the property/tag that is specified as None. A non-None value of "value"
#indicates that the value of the attribute must be taken into account.
common_ignoretags = [(None, "xml-lang", None)]
common_canchangetags = [
    ("img", "alt", None),
    (None, "title", None),
    (None, "dir", None),
    (None, "lang", None),
]
# Actually the title tag is allowed on many tags in HTML (but probably not all)


class CheckerConfig(object):
    """Object representing the configuration of a checker."""

    def __init__(self, targetlanguage=None, accelmarkers=None, varmatches=None,
                 notranslatewords=None, musttranslatewords=None,
                 validchars=None, punctuation=None, endpunctuation=None,
                 ignoretags=None, canchangetags=None, criticaltests=None,
                 credit_sources=None):
        # Init lists
        self.accelmarkers = self._init_list(accelmarkers)
        self.varmatches = self._init_list(varmatches)
        self.criticaltests = self._init_list(criticaltests)
        self.credit_sources = self._init_list(credit_sources)

        # Lang data
        self.updatetargetlanguage(targetlanguage)
        self.sourcelang = factory.getlanguage('en')

        # Inits with default values
        self.punctuation = self._init_default(data.normalized_unicode(punctuation),
                                              self.lang.punctuation)
        self.endpunctuation = self._init_default(data.normalized_unicode(endpunctuation),
                                                 self.lang.sentenceend)
        self.ignoretags = self._init_default(ignoretags, common_ignoretags)
        self.canchangetags = self._init_default(canchangetags, common_canchangetags)

        # Other data
        # TODO: allow user configuration of untranslatable words
        self.notranslatewords = dict.fromkeys([data.normalized_unicode(key) for key in self._init_list(notranslatewords)])
        self.musttranslatewords = dict.fromkeys([data.normalized_unicode(key) for key in self._init_list(musttranslatewords)])
        validchars = data.normalized_unicode(validchars)
        self.validcharsmap = {}
        self.updatevalidchars(validchars)


    def _init_list(self, list):
        """initialise configuration paramaters that are lists

        :type list: List
        :param list: None (we'll initialise a blank list) or a list paramater
        :rtype: List
        """
        if list is None:
            list = []

        return list


    def _init_default(self, param, default):
        """Initialise parameters that can have default options.

        :param param: the user supplied paramater value
        :param default: default values when param is not specified
        :return: the paramater as specified by the user of the default settings
        """
        if param is None:
            return default

        return param


    def update(self, otherconfig):
        """Combines the info in ``otherconfig`` into this config object."""
        self.targetlanguage = otherconfig.targetlanguage or self.targetlanguage
        self.updatetargetlanguage(self.targetlanguage)
        self.accelmarkers.extend([c for c in otherconfig.accelmarkers if not c in self.accelmarkers])
        self.varmatches.extend(otherconfig.varmatches)
        self.notranslatewords.update(otherconfig.notranslatewords)
        self.musttranslatewords.update(otherconfig.musttranslatewords)
        self.validcharsmap.update(otherconfig.validcharsmap)
        self.punctuation += otherconfig.punctuation
        self.endpunctuation += otherconfig.endpunctuation
        #TODO: consider also updating in the following cases:
        self.ignoretags = otherconfig.ignoretags
        self.canchangetags = otherconfig.canchangetags
        self.criticaltests.extend(otherconfig.criticaltests)
        self.credit_sources = otherconfig.credit_sources


    def updatevalidchars(self, validchars):
        """Updates the map that eliminates valid characters."""
        if validchars is None:
            return True

        validcharsmap = dict([(ord(validchar), None) for validchar in data.normalized_unicode(validchars)])
        self.validcharsmap.update(validcharsmap)


    def updatetargetlanguage(self, langcode):
        """Updates the target language in the config to the given target
        language.
        """
        self.targetlanguage = langcode
        self.lang = factory.getlanguage(langcode)


def cache_results(f):

    def cached_f(self, param1):
        key = (f.__name__, param1)
        res_cache = self.results_cache

        if key in res_cache:
            return res_cache[key]
        else:
            value = f(self, param1)
            res_cache[key] = value
            return value

    return cached_f


class UnitChecker(object):
    """Parent Checker class which does the checking based on functions available
    in derived classes.
    """
    preconditions = {}

    #: Categories where each checking function falls into
    #: Function names are used as keys, categories are the values
    categories = {}


    def __init__(self, checkerconfig=None, excludefilters=None,
                 limitfilters=None, errorhandler=None):
        self.errorhandler = errorhandler

        if checkerconfig is None:
            self.setconfig(CheckerConfig())
        else:
            self.setconfig(checkerconfig)

        # Exclude functions defined in UnitChecker from being treated as tests.
        self.helperfunctions = {}

        for functionname in dir(UnitChecker):
            function = getattr(self, functionname)

            if callable(function):
                self.helperfunctions[functionname] = function

        self.defaultfilters = self.getfilters(excludefilters, limitfilters)
        self.results_cache = {}


    def getfilters(self, excludefilters=None, limitfilters=None):
        """Returns dictionary of available filters, including/excluding those
        in the given lists.
        """
        filters = {}

        if limitfilters is None:
            # use everything available unless instructed
            limitfilters = dir(self)

        if excludefilters is None:
            excludefilters = {}

        for functionname in limitfilters:

            if functionname in excludefilters:
                continue

            if functionname in self.helperfunctions:
                continue

            if functionname == "errorhandler":
                continue

            filterfunction = getattr(self, functionname, None)
            if not callable(filterfunction):
                continue

            filters[functionname] = filterfunction

        return filters


    def setconfig(self, config):
        """Sets the accelerator list."""
        self.config = config
        self.accfilters = [prefilters.filteraccelerators(accelmarker) for accelmarker in self.config.accelmarkers]
        self.varfilters = [prefilters.filtervariables(startmatch, endmatch, prefilters.varname)
                for startmatch, endmatch in self.config.varmatches]
        self.removevarfilter = [prefilters.filtervariables(startmatch, endmatch,
                                                           prefilters.varnone)
                for startmatch, endmatch in self.config.varmatches]


    def setsuggestionstore(self, store):
        """Sets the filename that a checker should use for evaluating
        suggestions.
        """
        self.suggestion_store = store

        if self.suggestion_store:
            self.suggestion_store.require_index()


    def filtervariables(self, str1):
        """Filter out variables from ``str1``."""
        return helpers.multifilter(str1, self.varfilters)
    filtervariables = cache_results(filtervariables)

    def removevariables(self, str1):
        """Remove variables from ``str1``."""
        return helpers.multifilter(str1, self.removevarfilter)
    removevariables = cache_results(removevariables)

    def filteraccelerators(self, str1):
        """Filter out accelerators from ``str1``."""
        return helpers.multifilter(str1, self.accfilters, None)
    filteraccelerators = cache_results(filteraccelerators)


    def filteraccelerators_by_list(self, str1, acceptlist=None):
        """Filter out accelerators from ``str1``."""
        return helpers.multifilter(str1, self.accfilters, acceptlist)


    def filterwordswithpunctuation(self, str1):
        """Replaces words with punctuation with their unpunctuated
        equivalents.
        """
        return prefilters.filterwordswithpunctuation(str1)
    filterwordswithpunctuation = cache_results(filterwordswithpunctuation)


    def filterxml(self, str1):
        """Filter out XML from the string so only text remains."""
        return tag_re.sub("", str1)
    filterxml = cache_results(filterxml)


    def run_test(self, test, unit):
        """Runs the given test on the given unit.

        Note that this can raise a :exc:`FilterFailure` as part of normal operation.
        """
        return test(unit)

    def run_filters(self, unit, categorised=False):
        """Run all the tests in this suite.

        :rtype: Dictionary
        :return: Content of the dictionary is as follows::

           {'testname': { 'message': message_or_exception, 'category': failure_category } }
        """
        self.results_cache = {}
        failures = {}
        ignores = self.config.lang.ignoretests[:]
        functionnames = self.defaultfilters.keys()
        priorityfunctionnames = self.preconditions.keys()
        otherfunctionnames = filter(lambda functionname: functionname not in self.preconditions, functionnames)

        for functionname in priorityfunctionnames + otherfunctionnames:
            if functionname in ignores:
                continue

            filterfunction = getattr(self, functionname, None)

            # This filterfunction may only be defined on another checker if
            # using TeeChecker
            if filterfunction is None:
                continue

            filtermessage = filterfunction.__doc__

            try:
                filterresult = self.run_test(filterfunction, unit)
            except FilterFailure as e:
                filterresult = False
                filtermessage = unicode(e)
            except Exception as e:
                if self.errorhandler is None:
                    raise ValueError("error in filter %s: %r, %r, %s" %
                                     (functionname, unit.source, unit.target, e))
                else:
                    filterresult = self.errorhandler(functionname, unit.source,
                                                     unit.target, e)

            if not filterresult:
                # We test some preconditions that aren't actually a cause for
                # failure
                if functionname in self.defaultfilters:
                    failures[functionname] = {
                            'message': filtermessage,
                            'category': self.categories[functionname],
                            }

                if functionname in self.preconditions:
                    for ignoredfunctionname in self.preconditions[functionname]:
                        ignores.append(ignoredfunctionname)

        self.results_cache = {}

        if not categorised:
            for name, info in failures.iteritems():
                failures[name] = info['message']
        return failures


class TranslationChecker(UnitChecker):
    """A checker that passes source and target strings to the checks, not the
    whole unit.

    This provides some speedup and simplifies testing.
    """

    def __init__(self, checkerconfig=None, excludefilters=None,
                 limitfilters=None, errorhandler=None):
        super(TranslationChecker, self).__init__(checkerconfig, excludefilters,
                                                 limitfilters, errorhandler)

        # caches for spell checking results across units/runs
        self.source_spell_cache = lru.LRUCachingDict(256, cullsize=5, aggressive_gc=False)
        self.target_spell_cache = lru.LRUCachingDict(512, cullsize=5, aggressive_gc=False)

    def run_test(self, test, unit):
        """Runs the given test on the given unit.

        Note that this can raise a :exc:`FilterFailure` as part of normal
        operation.
        """
        if self.hasplural:
            filtermessages = []
            filterresult = True

            for pluralform in unit.target.strings:
                try:
                    if not test(self.str1, unicode(pluralform)):
                        filterresult = False
                except FilterFailure as e:
                    filterresult = False
                    filtermessages.extend(e.messages)

            if not filterresult and filtermessages:
                raise FilterFailure(filtermessages)
            else:
                return filterresult
        else:
            return test(self.str1, self.str2)


    def run_filters(self, unit, categorised=False):
        """Do some optimisation by caching some data of the unit for the
        benefit of :meth:`~TranslationChecker.run_test`.
        """
        self.str1 = data.normalized_unicode(unit.source) or u""
        self.str2 = data.normalized_unicode(unit.target) or u""
        self.hasplural = unit.hasplural()
        self.locations = unit.getlocations()

        return super(TranslationChecker, self).run_filters(unit, categorised)


class TeeChecker:
    """A Checker that controls multiple checkers."""

    #: Categories where each checking function falls into
    #: Function names are used as keys, categories are the values
    categories = {}


    def __init__(self, checkerconfig=None, excludefilters=None,
                 limitfilters=None, checkerclasses=None, errorhandler=None,
                 languagecode=None):
        """construct a TeeChecker from the given checkers"""
        self.limitfilters = limitfilters

        if checkerclasses is None:
            checkerclasses = [StandardChecker]

        self.checkers = [checkerclass(checkerconfig=checkerconfig,
                                      excludefilters=excludefilters,
                                      limitfilters=limitfilters,
                                      errorhandler=errorhandler) for checkerclass in checkerclasses]

        if languagecode:
            for checker in self.checkers:
                checker.config.updatetargetlanguage(languagecode)

            # Let's hook up the language specific checker
            lang_checker = self.checkers[0].config.lang.checker

            if lang_checker:
                self.checkers.append(lang_checker)

        self.combinedfilters = self.getfilters(excludefilters, limitfilters)
        self.config = checkerconfig or self.checkers[0].config


    def getfilters(self, excludefilters=None, limitfilters=None):
        """Returns a dictionary of available filters, including/excluding
        those in the given lists.
        """
        if excludefilters is None:
            excludefilters = {}

        filterslist = [checker.getfilters(excludefilters, limitfilters) for checker in self.checkers]
        self.combinedfilters = {}

        for filters in filterslist:
            self.combinedfilters.update(filters)

        # TODO: move this somewhere more sensible (a checkfilters method?)
        if limitfilters is not None:

            for filtername in limitfilters:

                if not filtername in self.combinedfilters:
                    logger.warning("could not find filter %s", filtername)

        return self.combinedfilters


    def run_filters(self, unit, categorised=False):
        """Run all the tests in the checker's suites."""
        failures = {}

        for checker in self.checkers:
            failures.update(checker.run_filters(unit, categorised))

        return failures


    def setsuggestionstore(self, store):
        """Sets the filename that a checker should use for evaluating
        suggestions.
        """
        for checker in self.checkers:
            checker.setsuggestionstore(store)


class StandardChecker(TranslationChecker):
    """The basic test suite for source -> target translations."""


    @extraction
    def untranslated(self, str1, str2):
        """Checks whether a string has been translated at all.

        This check is really only useful if you want to extract untranslated
        strings so that they can be translated independently of the main work.
        """
        str2 = prefilters.removekdecomments(str2)

        return not (len(str1.strip()) > 0 and len(str2) == 0)


    @functional
    def unchanged(self, str1, str2):
        """Checks whether a translation is basically identical to the original
        string.

        This checks to see if the translation isn’t just a copy of the English
        original. Sometimes, this is what you want, but other times you will
        detect words that should have been translated.
        """
        str1 = self.filteraccelerators(self.removevariables(str1)).strip()
        str2 = self.filteraccelerators(self.removevariables(str2)).strip()

        if len(str1) < 2:
            return True

        # If the whole string is upperase, or nothing in the string can go
        # towards uppercase, let's assume there is nothing translatable
        # TODO: reconsider
        if (str1.isupper() or str1.upper() == str1) and str1 == str2:
            return True

        if self.config.notranslatewords:
            words1 = str1.split()
            if len(words1) == 1 and [word for word in words1 if word in self.config.notranslatewords]:
                #currently equivalent to:
                #   if len(words1) == 1 and words1[0] in self.config.notranslatewords:
                #why do we only test for one notranslate word?
                return True

        # we could also check for things like str1.isnumeric(), but the test
        # above (str1.upper() == str1) makes this unnecessary
        if str1.lower() == str2.lower():
            raise FilterFailure(u"Consider translating")

        return True


    @functional
    def blank(self, str1, str2):
        """Checks whether a translation is totally blank.

        This will check to see if a translation has inadvertently been
        translated as blank i.e. as spaces. This is different from untranslated
        which is completely empty. This test is useful in that if something is
        translated as "  " it will appear to most tools as if it is translated.
        """
        len1 = len(str1.strip())
        len2 = len(str2.strip())

        if len1 > 0 and len(str2) != 0 and len2 == 0:
            raise FilterFailure(u"Translation is empty")
        else:
            return True


    @functional
    def short(self, str1, str2):
        """Checks whether a translation is much shorter than the original
        string.

        This is most useful in the special case where the translation is 1
        characters long while the source text is multiple characters long.
        Otherwise, we use a general ratio that will catch very big differences
        but is set conservatively to limit the number of false positives.
        """
        len1 = len(str1.strip())
        len2 = len(str2.strip())

        if (len1 > 0) and (0 < len2 < (len1 * 0.1)) or ((len1 > 1) and (len2 == 1)):
            raise FilterFailure(u"The translation is much shorter than the original")
        else:
            return True


    @functional
    def long(self, str1, str2):
        """Checks whether a translation is much longer than the original
        string.

        This is most useful in the special case where the translation is
        multiple characters long while the source text is only 1 character
        long. Otherwise, we use a general ratio that will catch very big
        differences but is set conservatively to limit the number of false
        positives.
        """
        len1 = len(str1.strip())
        len2 = len(str2.strip())

        if (len1 > 0) and (0 < len1 < (len2 * 0.1)) or ((len1 == 1) and (len2 > 1)):
            raise FilterFailure(u"The translation is much longer than the original")
        else:
            return True


    @critical
    def escapes(self, str1, str2):
        """Checks whether escaping is consistent between the two strings.

        Checks escapes such as ``\\n`` ``\uNNNN`` to ensure that if they exist
        in the original string you also have them in the translation.
        """
        if not helpers.countsmatch(str1, str2, (u"\\", u"\\\\")):
            escapes1 = u", ".join([u"'%s'" % word for word in str1.split() if u"\\" in word])
            escapes2 = u", ".join([u"'%s'" % word for word in str2.split() if u"\\" in word])

            raise SeriousFilterFailure(u"Escapes in original (%s) don't match "
                                       "escapes in translation (%s)" %
                                       (escapes1, escapes2))
        else:
            return True


    @critical
    def newlines(self, str1, str2):
        """Checks whether newlines are consistent between the two strings.

        Counts the number of ``\\n`` newlines (and variants such as ``\\r\\n``)
        and reports and error if they differ.
        """
        if not helpers.countsmatch(str1, str2, (u"\n", u"\r")):
            raise FilterFailure(u"Different line endings")

        if str1.endswith(u"\n") and not str2.endswith(u"\n"):
            raise FilterFailure(u"Newlines different at end")

        if str1.startswith(u"\n") and not str2.startswith(u"\n"):
            raise FilterFailure(u"Newlines different at beginning")

        return True


    @critical
    def tabs(self, str1, str2):
        """Checks whether tabs are consistent between the two strings.

        Counts the number of ``\\t`` tab markers and reports an error if they
        differ.
        """
        if not helpers.countmatch(str1, str2, "\t"):
            raise SeriousFilterFailure(u"Different tabs")
        else:
            return True


    @cosmetic
    def singlequoting(self, str1, str2):
        """Checks whether singlequoting is consistent between the two strings.

        The same as doublequoting but checks for the ``'`` character. Because
        this is used in contractions like it's and in possessive forms like
        user's, this test can output spurious errors if your language doesn't
        use such forms. If a quote appears at the end of a sentence in the
        translation, i.e. ``'.``, this might not be detected properly by the
        check.
        """
        str1 = self.filterwordswithpunctuation(self.filteraccelerators(self.filtervariables(str1)))
        str1 = self.config.lang.punctranslate(str1)

        str2 = self.filterwordswithpunctuation(self.filteraccelerators(self.filtervariables(str2)))

        if helpers.countsmatch(str1, str2, (u"'", u"''", u"\\'")):
            return True
        else:
            raise FilterFailure(u"Different quotation marks")


    @cosmetic
    def doublequoting(self, str1, str2):
        """Checks whether doublequoting is consistent between the two strings.

        Checks on double quotes ``"`` to ensure that you have the same number
        in both the original and the translated string. This tests takes into
        account that several languages use different quoting characters, and
        will test for them instead.
        """
        str1 = self.filteraccelerators(self.filtervariables(str1))
        str1 = self.filterxml(str1)
        str1 = self.config.lang.punctranslate(str1)

        str2 = self.filteraccelerators(self.filtervariables(str2))
        str2 = self.filterxml(str2)

        if helpers.countsmatch(str1, str2, (u'"', u'""', u'\\"', u"«",
                                        u"»", u"“", u"”")):
            return True
        else:
            raise FilterFailure(u"Different quotation marks")


    @cosmetic
    def doublespacing(self, str1, str2):
        """Checks for bad double-spaces by comparing to original.

        This will identify if you have [space][space] in when you don't have it
        in the original or it appears in the original but not in your
        translation. Some of these are spurious and how you correct them
        depends on the conventions of your language.
        """
        str1 = self.filteraccelerators(str1)
        str2 = self.filteraccelerators(str2)

        if helpers.countmatch(str1, str2, u"  "):
            return True
        else:
            raise FilterFailure(u"Different use of double spaces")


    @cosmetic
    def puncspacing(self, str1, str2):
        """Checks for bad spacing after punctuation.

        In the case of [full-stop][space] in the original, this test checks
        that your translation does not remove the space. It checks also for
        [comma], [colon], etc.

        Some languages don't use spaces after common punctuation marks,
        especially where full-width punctuation marks are used. This check will
        take that into account.
        """
        # Convert all nbsp to space, and just check spaces. Useful intermediate
        # step to stricter nbsp checking?
        str1 = self.filteraccelerators(self.filtervariables(str1))
        str1 = self.config.lang.punctranslate(str1)
        str1 = str1.replace(u"\u00a0", u" ")

        if str1.find(u" ") == -1:
            return True

        str2 = self.filteraccelerators(self.filtervariables(str2))
        str2 = str2.replace(u"\u00a0", u" ")

        for puncchar in self.config.punctuation:
            plaincount1 = str1.count(puncchar)

            if not plaincount1:
                continue

            plaincount2 = str2.count(puncchar)

            if plaincount1 != plaincount2:
                continue

            spacecount1 = str1.count(puncchar + u" ")
            spacecount2 = str2.count(puncchar + u" ")

            if spacecount1 != spacecount2:
                # Handle extra spaces that are because of transposed punctuation

                if abs(spacecount1 - spacecount2) == 1 and str1.endswith(puncchar) != str2.endswith(puncchar):
                    continue

                raise FilterFailure(u"Different spacing around punctuation")

        return True


    @critical
    def printf(self, str1, str2):
        """Checks whether printf format strings match.

        If the printf formatting variables are not identical, then this will
        indicate an error. Printf statements are used by programs to format
        output in a human readable form (they are placeholders for variable
        data). They allow you to specify lengths of string variables, string
        padding, number padding, precision, etc. Generally they will look like
        this: ``%d``, ``%5.2f``, ``%100s``, etc. The test can also manage
        variables-reordering using the ``%1$s`` syntax. The variables' type and
        details following data are tested to ensure that they are strictly
        identical, but they may be reordered.

        See also `printf Format String
        <http://en.wikipedia.org/wiki/Printf_format_string>`_.
        """
        count1 = count2 = plural = None

        # self.hasplural only set by run_filters, not always available
        if 'hasplural' in self.__dict__:
            plural = self.hasplural

        for var_num2, match2 in enumerate(printf_pat.finditer(str2)):
            count2 = var_num2 + 1
            str2ord = match2.group('ord') if not match2.group('boost_ord') else match2.group('boost_ord')
            str2key = match2.group('key')
            str2fullvar = match2.group('fullvar') if not match2.group('boost_ord') else '%'

            if str2ord:
                str1ord = None
                gotmatch = False

                for var_num1, match1 in enumerate(printf_pat.finditer(str1)):
                    count1 = var_num1 + 1
                    localstr1ord = match1.group('ord') if not match1.group('boost_ord') else match1.group('boost_ord')

                    if localstr1ord:
                        if str2ord == localstr1ord:
                            str1ord = str2ord
                            str1fullvar = match1.group('fullvar') if not match1.group('boost_ord') else '%'

                            if str2fullvar == str1fullvar:
                                gotmatch = True
                    elif int(str2ord) == var_num1 + 1:
                        str1ord = str2ord
                        str1fullvar = match1.group('fullvar') if not match1.group('boost_ord') else '%'

                        if str2fullvar == str1fullvar:
                            gotmatch = True

                if str1ord is None:
                    raise FilterFailure(u"Added printf variable: %s" % match2.group())

                if not gotmatch:
                    raise FilterFailure(u"Different printf variable: %s" % match2.group())
            elif str2key:
                str1key = None

                for var_num1, match1 in enumerate(printf_pat.finditer(str1)):
                    count1 = var_num1 + 1
                    str1fullvar = match1.group('fullvar') if not match1.group('boost_ord') else '%'

                    if match1.group('key') and str2key == match1.group('key'):
                        str1key = match1.group('key')

                        # '%.0s' "placeholder" in plural will match anything
                        if plural and str2fullvar == '.0s':
                            continue

                        if str1fullvar != str2fullvar:
                            raise FilterFailure(u"Different printf variable: %s" % match2.group())

                if str1key is None:
                    raise FilterFailure(u"Added printf variable: %s" % match2.group())
            else:
                for var_num1, match1 in enumerate(printf_pat.finditer(str1)):
                    count1 = var_num1 + 1
                    str1fullvar = match1.group('fullvar') if not match1.group('boost_ord') else '%'

                    # '%.0s' "placeholder" in plural will match anything
                    if plural and str2fullvar == '.0s':
                        continue

                    if (var_num1 == var_num2) and (str1fullvar != str2fullvar):
                        raise FilterFailure(u"Different printf variable: %s" % match2.group())

        if count2 is None:
            str1_variables = list(m.group() for m in printf_pat.finditer(str1))

            if str1_variables:
                raise FilterFailure(u"Missing printf variable: %s" % u", ".join(str1_variables))

        if (count1 or count2) and (count1 != count2):
            raise FilterFailure(u"Different number of printf variables")

        return 1


    @critical
    def pythonbraceformat(self, str1, str2):
        """Checks whether python brace format strings match."""

        # Helper function
        def max_anons(anons):
            """
            Takes a list of anonymous placeholder variables, e.g.
            ['', '1', ...]
            Determines how many anonymous formatting args the string
            they come from requires. Motivation for this function:
              * max_anons(vars_from_original) tells us how many
                anonymous placeholders are supported (at least).
              * max_anons(vars_from_translation) should not
                exceed it.
            """

            # implicit_n: you need at least as many anonymous args as
            # there are anonymous placeholders.
            implicit_n = anons.count('')
            # explicit_n: you need at least as many anonymous args as
            # the highest '{99}'-style placeholder. (The `+ 1` is to
            # correct for 0-indexing)
            try:
                explicit_n = max([
                    int(numbered_anon) + 1
                    for numbered_anon in anons
                    if len(numbered_anon) >= 1
                ])
            except ValueError:
                explicit_n = 0

            highest_n = max(implicit_n, explicit_n)

            return highest_n

        messages = []
        # Possible failure states: 0 = ok, 1 = mild, 2 = serious
        STATE_OK, STATE_MILD, STATE_SERIOUS = 0, 1, 2
        failure_state = STATE_OK
        pythonbraceformat_pat = re.compile('{[^}]*}')
        data1 = {}
        data2 = {}

        # Populate the data1 and data2 dicts.
        for data_, str_ in [(data1, str1),
                            (data2, str2)]:
            # Remove all escaped braces {{ and }}
            data_['strclean'] = re.sub('{{|}}', '', str_)
            data_['allvars'] = pythonbraceformat_pat.findall(data_['strclean'])
            data_['anonvars'] = [
                var[1:-1]
                for var in data_['allvars']
                if re.match(r'^{[0-9]*}$', var)
            ]
            data_['namedvars'] = [
                var
                for var in data_['allvars']
                if not re.match(r'^{[0-9]*}$', var)
            ]

        max1 = max_anons(data1['anonvars'])
        max2 = max_anons(data2['anonvars'])

        if max1 == max2:
            pass
        elif max1 < max2:
            failure_state = max(failure_state, STATE_SERIOUS)
            messages.append(
                u"Translation requires %s anonymous formatting args, original only %s." %
                    (max2, max1)
            )
        else:
            failure_state = max(failure_state, STATE_MILD)
            messages.append(
                u"Highest anonymous placeholder in original is %s, in translation %s" %
                    (max1, max2)
            )

        if set(data1['namedvars']) == set(data2['namedvars']):
            pass

        extra_in_2 = set(data2['namedvars']).difference(set(data1['namedvars']))
        if 0 < len(extra_in_2):
            failure_state = max(failure_state, STATE_SERIOUS)
            messages.append(
                u"Unknown named placeholders in translation: %s\n" %
                    ', '.join(extra_in_2)
            )

        extra_in_1 = set(data1['namedvars']).difference(set(data2['namedvars']))
        if 0 < len(extra_in_1):
            failure_state = max(failure_state, STATE_MILD)
            messages.append(
                u"Named placeholders absent in translation: %s" %
                    ', '.join(extra_in_1)
            )

        if failure_state == STATE_OK:
            return 1
        elif failure_state == STATE_MILD:
            raise FilterFailure(messages)
        elif failure_state == STATE_SERIOUS:
            raise SeriousFilterFailure(messages)
        else:
            raise ValueError(u"Something wrong in python brace checks: unreachable state reached.")


    @functional
    def accelerators(self, str1, str2):
        """Checks whether accelerators are consistent between the two strings.

        This test is capable of checking the different type of accelerators
        that are used in different projects, like Mozilla or KDE. The test will
        pick up accelerators that are missing and ones that shouldn't be there.

        See `accelerators on the localization guide
        <http://docs.translatehouse.org/projects/localization-guide/en/latest/guide/translation/accelerators.html>`_
        for a full description on accelerators.
        """
        str1 = self.filtervariables(str1)
        str2 = self.filtervariables(str2)
        messages = []

        for accelmarker in self.config.accelmarkers:
            counter1 = decoration.countaccelerators(accelmarker, self.config.sourcelang.validaccel)
            counter2 = decoration.countaccelerators(accelmarker, self.config.lang.validaccel)
            count1, countbad1 = counter1(str1)
            count2, countbad2 = counter2(str2)
            getaccel = decoration.getaccelerators(accelmarker, self.config.lang.validaccel)
            accel2, bad2 = getaccel(str2)

            if count1 == count2:
                continue

            if count1 == 1 and count2 == 0:
                if countbad2 == 1:
                    messages.append(u"Accelerator '%s' appears before an invalid "
                                    "accelerator character '%s'" %
                                    (accelmarker, bad2[0]))
                else:
                    messages.append(u"Missing accelerator '%s'" %
                                    accelmarker)
            elif count1 == 0:
                messages.append(u"Added accelerator '%s'" % accelmarker)
            elif count1 == 1 and count2 > count1:
                messages.append(u"Accelerator '%s' is repeated in translation" %
                                accelmarker)
            else:
                messages.append(u"Accelerator '%s' occurs %d time(s) in original "
                                "and %d time(s) in translation" %
                                (accelmarker, count1, count2))

        if messages:
            if "accelerators" in self.config.criticaltests:
                raise SeriousFilterFailure(messages)
            else:
                raise FilterFailure(messages)

        return True

#    def acceleratedvariables(self, str1, str2):
#        """checks that no variables are accelerated"""
#        messages = []
#        for accelerator in self.config.accelmarkers:
#            for variablestart, variableend in self.config.varmatches:
#                error = accelerator + variablestart
#                if str1.find(error) >= 0:
#                    messages.append(u"original has an accelerated variable")
#                if str2.find(error) >= 0:
#                    messages.append(u"translation has an accelerated variable")
#        if messages:
#            raise FilterFailure(messages)
#        return True


    @critical
    def variables(self, str1, str2):
        """Checks whether variables of various forms are consistent between the
        two strings.

        This checks to make sure that variables that appear in the original
        also appear in the translation. It can handle variables from projects
        like KDE or OpenOffice. It does not at the moment cope with variables
        that use the reordering syntax of Gettext PO files.
        """
        messages = []
        mismatch1, mismatch2 = [], []
        varnames1, varnames2 = [], []

        for startmarker, endmarker in self.config.varmatches:
            varchecker = decoration.getvariables(startmarker, endmarker)

            if startmarker and endmarker:
                if isinstance(endmarker, int):
                    redecorate = lambda var: startmarker + var
                else:
                    redecorate = lambda var: startmarker + var + endmarker
            elif startmarker:
                redecorate = lambda var: startmarker + var
            else:
                redecorate = lambda var: var

            vars1 = varchecker(str1)
            vars2 = varchecker(str2)

            if vars1 != vars2:
                # we use counts to compare so we can handle multiple variables
                vars1, vars2 = [var for var in vars1 if vars1.count(var) > vars2.count(var)], \
                               [var for var in vars2 if vars1.count(var) < vars2.count(var)]
                # filter variable names we've already seen, so they aren't
                # matched by more than one filter...
                vars1, vars2 = [var for var in vars1 if var not in varnames1], [var for var in vars2 if var not in varnames2]
                varnames1.extend(vars1)
                varnames2.extend(vars2)
                vars1 = map(redecorate, vars1)
                vars2 = map(redecorate, vars2)
                mismatch1.extend(vars1)
                mismatch2.extend(vars2)

        if mismatch1:
            messages.append(u"Do not translate: %s" % u", ".join(mismatch1))
        elif mismatch2:
            messages.append(u"Added variables: %s" % u", ".join(mismatch2))

        if messages and mismatch1:
            raise SeriousFilterFailure(messages)
        elif messages:
            raise FilterFailure(messages)

        return True


    @functional
    def functions(self, str1, str2):
        """Checks that function names are not translated.

        Checks that function names e.g. ``rgb()`` or ``getEntity.Name()`` are
        not translated.
        """
        # We can't just use helpers.funcmatch() since it doesn't ignore order
        if not set(decoration.getfunctions(str1)).symmetric_difference(set(decoration.getfunctions(str2))):
            return True
        else:
            raise FilterFailure(u"Different functions")


    @functional
    def emails(self, str1, str2):
        """Checks that emails are not translated.

        Generally you should not be translating email addresses. This check
        will look to see that email addresses e.g. ``info@example.com`` are not
        translated. In some cases of course you should translate the address
        but generally you shouldn't.
        """
        if helpers.funcmatch(str1, str2, decoration.getemails):
            return True
        else:
            raise FilterFailure(u"Different e-mails")


    @functional
    def urls(self, str1, str2):
        """Checks that URLs are not translated.

        This checks only basic URLs (http, ftp, mailto etc.) not all URIs (e.g.
        afp, smb, file). Generally, you don't want to translate URLs, unless
        they are example URLs (http://your_server.com/filename.html). If the
        URL is for configuration information, then you need to query the
        developers about placing configuration information in PO files. It
        shouldn't really be there, unless it is very clearly marked: such
        information should go into a configuration file.
        """
        if helpers.funcmatch(str1, str2, decoration.geturls):
            return True
        else:
            raise FilterFailure(u"Different URLs")


    @functional
    def numbers(self, str1, str2):
        """Checks whether numbers of various forms are consistent between the
        two strings.

        You will see some errors where you have either written the number in
        full or converted it to the digit in your translation. Also changes in
        order will trigger this error.
        """
        if helpers.countsmatch(str1, str2, decoration.getnumbers(str1)):
            return True
        else:
            raise FilterFailure(u"Different numbers")


    @cosmetic
    def startwhitespace(self, str1, str2):
        """Checks whether whitespace at the beginning of the strings matches.

        As in endwhitespace but you will see fewer errors.
        """
        if helpers.funcmatch(str1, str2, decoration.spacestart):
            return True
        else:
            raise FilterFailure(u"Different whitespace at the start")


    @cosmetic
    def endwhitespace(self, str1, str2):
        """Checks whether whitespace at the end of the strings matches.

        Operates the same as endpunc but is only concerned with whitespace.
        This filter is particularly useful for those strings which will
        evidently be followed by another string in the program, e.g.
        [Password: ] or [Enter your username: ]. The whitespace is an inherent
        part of the string. This filter makes sure you don't miss those
        important but otherwise invisible spaces!

        If your language uses full-width punctuation (like Chinese), the visual
        spacing in the character might be enough without an added extra space.
        """
        str1 = self.config.lang.punctranslate(str1)

        if helpers.funcmatch(str1, str2, decoration.spaceend):
            return True
        else:
            raise FilterFailure(u"Different whitespace at the end")


    @cosmetic
    def startpunc(self, str1, str2):
        """Checks whether punctuation at the beginning of the strings match.

        Operates as endpunc but you will probably see fewer errors.
        """
        str1 = self.filterxml(self.filterwordswithpunctuation(self.filteraccelerators(self.filtervariables(str1))))
        str1 = self.config.lang.punctranslate(str1)
        str2 = self.filterxml(self.filterwordswithpunctuation(self.filteraccelerators(self.filtervariables(str2))))

        if helpers.funcmatch(str1, str2, decoration.puncstart, self.config.punctuation):
            return True
        else:
            raise FilterFailure(u"Different punctuation at the start")


    @cosmetic
    def endpunc(self, str1, str2):
        """Checks whether punctuation at the end of the strings match.

        This will ensure that the ending of your translation has the same
        punctuation as the original. E.g. if it ends in :[space] then so should
        yours. It is useful for ensuring that you have ellipses [...] in all
        your translations, not simply three separate full-stops. You may pick
        up some errors in the original: feel free to keep your translation and
        notify the programmers. In some languages, characters such as ``?`` or
        ``!`` are always preceded by a space e.g. [space]? — do what your
        language customs dictate. Other false positives you will notice are,
        for example, if through changes in word-order you add "), etc. at the
        end of the sentence. Do not change these: your language word-order
        takes precedence.

        It must be noted that if you are tempted to leave out [full-stop] or
        [colon] or add [full-stop] to a sentence, that often these have been
        done for a reason, e.g. a list where fullstops make it look cluttered.
        So, initially match them with the English, and make changes once the
        program is being used.

        This check is aware of several language conventions for punctuation
        characters, such as the custom question marks for Greek and Arabic,
        Devanagari Danda, full-width punctuation for CJK languages, etc.
        Support for your language can be added easily if it is not there yet.
        """
        str1 = self.filtervariables(str1)
        str1 = self.config.lang.punctranslate(str1)
        str2 = self.filtervariables(str2)
        str1 = str1.rstrip()
        str2 = str2.rstrip()

        if helpers.funcmatch(str1, str2, decoration.puncend, self.config.endpunctuation + u":"):
            return True
        else:
            raise FilterFailure(u"Different punctuation at the end")


    @functional
    def purepunc(self, str1, str2):
        """Checks that strings that are purely punctuation are not changed.

        This extracts strings like ``+`` or ``-`` as these usually should not
        be changed.
        """
        # this test is a subset of startandend
        if (decoration.ispurepunctuation(str1)):
            success = str1 == str2
        else:
            success = not decoration.ispurepunctuation(str2)

        if success:
            return True
        else:
            raise FilterFailure(u"Consider not translating punctuation")


    @cosmetic
    def brackets(self, str1, str2):
        """Checks that the number of brackets in both strings match.

        If ``([{`` or ``}])`` appear in the original this will check that the
        same number appear in the translation.
        """
        str1 = self.filtervariables(str1)
        str2 = self.filtervariables(str2)

        messages = []
        missing = []
        extra = []

        for bracket in (u"[", u"]", u"{", u"}", u"(", u")"):
            count1 = str1.count(bracket)
            count2 = str2.count(bracket)

            if count2 < count1:
                missing.append(u"'%s'" % bracket)
            elif count2 > count1:
                extra.append(u"'%s'" % bracket)

        if missing:
            messages.append(u"Missing %s" % u", ".join(missing))

        if extra:
            messages.append(u"Added %s" % u", ".join(extra))

        if messages:
            raise FilterFailure(messages)

        return True


    @functional
    def sentencecount(self, str1, str2):
        """Checks that the number of sentences in both strings match.

        Adds the number of sentences to see that the sentence count is the same
        between the original and translated string. You may not always want to
        use this test, if you find you often need to reformat your translation,
        because the original is badly-expressed, or because the structure of
        your language works better that way. Do what works best for your
        language: it's the meaning of the original you want to convey, not the
        exact way it was written in the English.
        """
        str1 = self.filteraccelerators(str1)
        str2 = self.filteraccelerators(str2)

        sentences1 = len(self.config.sourcelang.sentences(str1))
        sentences2 = len(self.config.lang.sentences(str2))

        if not sentences1 == sentences2:
            raise FilterFailure(u"Different number of sentences: "
                                u"%d ≠ %d" % (sentences1, sentences2))

        return True


    @functional
    def options(self, str1, str2):
        """Checks that command line options are not translated.

        In messages that contain command line options, such as ``--help``,
        this test will check that these remain untranslated. These could be
        translated in the future if programs can create a mechanism to allow
        this, but currently they are not translated. If the options has a
        parameter, e.g. ``--file=FILE``, then the test will check that the
        parameter has been translated.
        """
        str1 = self.filtervariables(str1)

        for word1 in str1.split():
            if word1 != u"--" and word1.startswith(u"--") and word1[-1].isalnum():
                parts = word1.split(u"=")

                if not parts[0] in str2:
                    raise FilterFailure(u"Missing or translated option '%s'" % parts[0])

                if len(parts) > 1 and parts[1] in str2:
                    raise FilterFailure(u"Consider translating parameter "
                                        u"'%(param)s' of option '%(option)s'"
                                                                % {"param": parts[1],
                                                                "option": parts[0]})

        return True


    @cosmetic
    def startcaps(self, str1, str2):
        """Checks that the message starts with the correct capitalisation.

        After stripping whitespace and common punctuation characters, it then
        checks to see that the first remaining character is correctly
        capitalised. So, if the sentence starts with an upper-case letter, and
        the translation does not, an error is produced.

        This check is entirely disabled for many languages that don't make a
        distinction between upper and lower case. Contact us if this is not yet
        disabled for your language.
        """
        str1 = self.filteraccelerators(str1)
        str2 = self.filteraccelerators(str2)

        if len(str1) > 1 and len(str2) > 1:
            if self.config.sourcelang.capsstart(str1) == self.config.lang.capsstart(str2):
                return True
            elif self.config.sourcelang.numstart(str1) or self.config.lang.numstart(str2):
                return True
            else:
                raise FilterFailure(u"Different capitalization at the start")

        if len(str1) == 0 and len(str2) == 0:
            return True

        if len(str1) == 0 or len(str2) == 0:
            raise FilterFailure(u"Different capitalization at the start")

        return True


    @cosmetic
    def simplecaps(self, str1, str2):
        """Checks the capitalisation of two strings isn't wildly different.

        This will pick up many false positives, so don't be a slave to it. It
        is useful for identifying translations that don't start with a capital
        letter (upper-case letter) when they should, or those that do when they
        shouldn't. It will also highlight sentences that have extra capitals;
        depending on the capitalisation convention of your language, you might
        want to change these to Title Case, or change them all to normal
        sentence case.
        """
        str1 = self.removevariables(str1)
        str2 = self.removevariables(str2)
        # TODO: review this. The 'I' is specific to English, so it probably
        # serves no purpose to get sourcelang.sentenceend
        str1 = re.sub(u"[^%s]( I )" % self.config.sourcelang.sentenceend, u" i ", str1)

        capitals1 = helpers.filtercount(str1, unicode.isupper)
        capitals2 = helpers.filtercount(str2, unicode.isupper)

        alpha1 = helpers.filtercount(str1, unicode.isalpha)
        alpha2 = helpers.filtercount(str2, unicode.isalpha)

        # Capture the all caps case
        if capitals1 == alpha1:
            if capitals2 == alpha2:
                return True
            else:
                raise FilterFailure(u"Different capitalization")

        # some heuristic tests to try and see that the style of capitals is
        # vaguely the same
        if capitals1 == 0 or capitals1 == 1:
            success = capitals2 == capitals1
        elif capitals1 < len(str1) / 10:
            success = capitals2 <= len(str2) / 8
        elif len(str1) < 10:
            success = abs(capitals1 - capitals2) < 3
        elif capitals1 > len(str1) * 6 / 10:
            success = capitals2 > len(str2) * 6 / 10
        else:
            success = abs(capitals1 - capitals2) < (len(str1) + len(str2)) / 6

        if success:
            return True
        else:
            raise FilterFailure(u"Different capitalization")


    @functional
    def acronyms(self, str1, str2):
        """Checks that acronyms that appear are unchanged.

        If an acronym appears in the original this test will check that it
        appears in the translation. Translating acronyms is a language decision
        but many languages leave them unchanged. In that case this test is
        useful for tracking down translations of the acronym and correcting
        them.
        """
        acronyms = []
        allowed = []

        for startmatch, endmatch in self.config.varmatches:
            allowed += decoration.getvariables(startmatch, endmatch)(str1)

        allowed += self.config.musttranslatewords.keys()
        str1 = self.filteraccelerators(self.filtervariables(str1))
        iter = self.config.lang.word_iter(str1)
        str2 = self.filteraccelerators(self.filtervariables(str2))

        #TODO: strip XML? - should provide better error messsages
        # see mail/chrome/messanger/smime.properties.po
        #TODO: consider limiting the word length for recognising acronyms to
        #something like 5/6 characters
        for word in iter:
            if word.isupper() and len(word) > 1 and word not in allowed:
                if str2.find(word) == -1:
                    acronyms.append(word)

        if acronyms:
            raise FilterFailure(u"Consider not translating acronyms: %s" %
                                u", ".join(acronyms))

        return True


    @cosmetic
    def doublewords(self, str1, str2):
        """Checks for repeated words in the translation.

        Words that have been repeated in a translation will be highlighted with
        this test e.g. "the the", "a a". These are generally typos that need
        correcting. Some languages may have valid repeated words in their
        structure, in that case either ignore those instances or switch this
        test off.
        """
        lastword = ""
        without_newlines = "\n".join(str2.split("\n"))
        words = self.filteraccelerators(self.removevariables(self.filterxml(without_newlines))).replace(u".", u"").lower().split()

        for word in words:
            if word == lastword and word not in self.config.lang.validdoublewords:
                raise FilterFailure(u"The word '%s' is repeated" % word)
            lastword = word

        return True


    @functional
    def notranslatewords(self, str1, str2):
        """Checks that words configured as untranslatable appear in the
        translation too.

        Many brand names should not be translated, this test allows you to
        easily make sure that words like: Word, Excel, Impress, Calc, etc. are
        not translated. You must specify a file containing all of the
        *no translate* words using ``--notranslatefile``.
        """
        if not self.config.notranslatewords:
            return True

        str1 = self.filtervariables(str1)
        str2 = self.filtervariables(str2)

        #The above is full of strange quotes and things in utf-8 encoding.
        #single apostrophe perhaps problematic in words like "doesn't"
        for seperator in self.config.punctuation:
            str1 = str1.replace(seperator, u" ")
            str2 = str2.replace(seperator, u" ")

        words1 = self.filteraccelerators(str1).split()
        words2 = self.filteraccelerators(str2).split()
        stopwords = [word for word in words1 if word in self.config.notranslatewords and word not in words2]

        if stopwords:
            raise FilterFailure(u"Do not translate: %s" %
                                (u", ".join(stopwords)))

        return True


    @functional
    def musttranslatewords(self, str1, str2):
        """Checks that words configured as definitely translatable don't appear
        in the translation.

        If for instance in your language you decide that you must translate
        'OK' then this test will flag any occurrences of 'OK' in the
        translation if it appeared in the source string. You must specify a
        file containing all of the *must translate* words using
        ``--musttranslatefile``.
        """
        if not self.config.musttranslatewords:
            return True

        str1 = self.removevariables(str1)
        str2 = self.removevariables(str2)

        # The above is full of strange quotes and things in utf-8 encoding.
        # single apostrophe perhaps problematic in words like "doesn't"
        for seperator in self.config.punctuation:
            str1 = str1.replace(seperator, u" ")
            str2 = str2.replace(seperator, u" ")

        words1 = self.filteraccelerators(str1).split()
        words2 = self.filteraccelerators(str2).split()
        stopwords = [word for word in words1 if word.lower() in self.config.musttranslatewords and word in words2]

        if stopwords:
            raise FilterFailure(u"Please translate: %s" % (u", ".join(stopwords)))

        return True


    @cosmetic
    def validchars(self, str1, str2):
        """Checks that only characters specified as valid appear in the
        translation.

        Often during character conversion to and from UTF-8 you get some
        strange characters appearing in your translation. This test presents a
        simple way to try and identify such errors.

        This test will only run of you specify the ``--validcharsfile`` command
        line option. This file contains all the characters that are valid in
        your language. You must use UTF-8 encoding for the characters in the
        file.

        If the test finds any characters not in your valid characters file then
        the test will print the character together with its Unicode value
        (e.g. 002B).
        """
        if not self.config.validcharsmap:
            return True

        invalid1 = str1.translate(self.config.validcharsmap)
        invalid2 = str2.translate(self.config.validcharsmap)
        invalidchars = [u"'%s' (\\u%04x)" % (invalidchar, ord(invalidchar)) for invalidchar in invalid2 if invalidchar not in invalid1]

        if invalidchars:
            raise FilterFailure(u"Invalid characters: %s" % (u", ".join(invalidchars)))

        return True


    @functional
    def filepaths(self, str1, str2):
        """Checks that file paths have not been translated.

        Checks that paths such as ``/home/user1`` have not been translated.
        Generally you do not translate a file path, unless it is being used as
        an example, e.g. ``your_user_name/path/to/filename.conf``.
        """
        for word1 in self.filteraccelerators(self.filterxml(str1)).split():
            if word1.startswith(u"/"):
                if not helpers.countsmatch(str1, str2, (word1,)):
                    raise FilterFailure(u"Different file paths")

        return True


    @critical
    def xmltags(self, str1, str2):
        """Checks that XML/HTML tags have not been translated.

        This check finds the number of tags in the source string and checks
        that the same number are in the translation. If the counts don't match
        then either the tag is missing or it was mistakenly translated by the
        translator, both of which are errors.

        The check ignores tags or things that look like tags that cover the
        whole string e.g. ``<Error>`` but will produce false positives for
        things like ``An <Error> occurred`` as here ``Error`` should be
        translated. It also will allow translation of the *alt* attribute in
        e.g. ``<img src="bob.png" alt="Image description">`` or similar
        translatable attributes in OpenOffice.org help files.
        """
        tags1 = tag_re.findall(str1)

        if len(tags1) > 0:
            if (len(tags1[0]) == len(str1)) and not u"=" in tags1[0]:
                return True

            tags2 = tag_re.findall(str2)
            properties1 = tagproperties(tags1, self.config.ignoretags)
            properties2 = tagproperties(tags2, self.config.ignoretags)

            filtered1 = []
            filtered2 = []

            for property1 in properties1:
                filtered1 += [intuplelist(property1, self.config.canchangetags)]

            for property2 in properties2:
                filtered2 += [intuplelist(property2, self.config.canchangetags)]

            # TODO: consider the consequences of different ordering of
            # attributes/tags
            if filtered1 != filtered2:
                raise FilterFailure(u"Different XML tags")
        else:
            # No tags in str1, let's just check that none were added in str2.
            # This might be useful for fuzzy strings wrongly unfuzzied.
            tags2 = tag_re.findall(str2)

            if len(tags2) > 0:
                raise FilterFailure(u"Added XML tags")

        return True


    @functional
    def kdecomments(self, str1, str2):
        """Checks to ensure that no KDE style comments appear in the
        translation.

        KDE style translator comments appear in PO files as
        ``"_: comment\\n"``. New translators often translate the comment. This
        test tries to identify instances where the comment has been translated.
        """
        return str2.find(u"\n_:") == -1 and not str2.startswith(u"_:")


    @extraction
    def compendiumconflicts(self, str1, str2):
        """Checks for Gettext compendium conflicts (#-#-#-#-#).

        When you use msgcat to create a PO compendium it will insert
        ``#-#-#-#-#`` into entries that are not consistent. If the compendium
        is used later in a message merge then these conflicts will appear in
        your translations. This test quickly extracts those for correction.
        """
        return str2.find(u"#-#-#-#-#") == -1


    @cosmetic
    def simpleplurals(self, str1, str2):
        """Checks for English style plural(s) for you to review.

        This test will extract any message that contains words with a final
        "(s)" in the source text. You can then inspect the message, to check
        that the correct plural form has been used for your language. In some
        languages, plurals are made by adding text at the beginning of words,
        making the English style messy. In this case, they often revert to the
        plural form. This test allows an editor to check that the plurals used
        are correct. Be aware that this test may create a number of false
        positives.

        For languages with no plural forms (only one noun form) this test will
        simply test that nothing like "(s)" was used in the translation.
        """

        def numberofpatterns(string, patterns):
            number = 0

            for pattern in patterns:
                number += len(re.findall(pattern, string))

            return number

        sourcepatterns = ["\(s\)"]
        targetpatterns = ["\(s\)"]
        sourcecount = numberofpatterns(str1, sourcepatterns)
        targetcount = numberofpatterns(str2, targetpatterns)

        if self.config.lang.nplurals == 1:
            if targetcount:
                raise FilterFailure(u"Plural(s) were kept in translation")
            else:
                return True

        if sourcecount == targetcount:
            return True
        else:
            raise FilterFailure(u"The original uses plural(s)")


    @functional
    def spellcheck(self, str1, str2):
        """Checks words that don't pass a spell check.

        This test will check for misspelled words in your translation. The test
        first checks for misspelled words in the original (usually English)
        text, and adds those to an exclusion list. The advantage of this
        exclusion is that many words that are specific to the application will
        not raise errors e.g. program names, brand names, function names.

        The checker works with `PyEnchant
        <http://pythonhosted.org/pyenchant/>`_. You need to have PyEnchant
        installed as well as a dictionary for your language (for example, one
        of the `Hunspell <https://wiki.openoffice.org/wiki/Dictionaries>`_ or
        `aspell <http://ftp.gnu.org/gnu/aspell/dict/>`_ dictionaries). This
        test will only work if you have specified the ``--language`` option.

        The pofilter error that is created, lists the misspelled word, plus
        suggestions returned from the spell checker. That makes it easy for you
        to identify the word and select a replacement.
        """
        if not self.config.targetlanguage:
            return True

        if not spelling.available:
            return True

        # TODO: filterxml?
        str1 = self.filteraccelerators_by_list(self.removevariables(str1),
                                               self.config.sourcelang.validaccel)
        str2 = self.filteraccelerators_by_list(self.removevariables(str2),
                                               self.config.lang.validaccel)
        errors = set()

        # We cache spelling results of source texts:
        ignore1 = self.source_spell_cache.get(str1, None)
        if ignore1 is None:
            ignore1 = set(spelling.simple_check(str1, lang=self.config.sourcelang.code))
            self.source_spell_cache[str1] = ignore1

        # We cache spelling results of target texts sentence-by-sentence. This
        # way we can reuse most of the results while someone is typing a long
        # segment in Virtaal.
        sentences2 = self.config.lang.sentences(str2)
        for sentence in sentences2:
            sentence_errors = self.target_spell_cache.get(sentence, None)
            if sentence_errors is None:
                sentence_errors = spelling.simple_check(sentence, lang=self.config.targetlanguage)
                self.target_spell_cache[sentence] = sentence_errors
            errors.update(sentence_errors)

        errors.difference_update(ignore1, self.config.notranslatewords)

        if errors:
            messages = [u"Check the spelling of: %s" % u", ".join(errors)]
            raise FilterFailure(messages)

        return True


    @extraction
    def credits(self, str1, str2):
        """Checks for messages containing translation credits instead of
        normal translations.

        Some projects have consistent ways of giving credit to translators by
        having a unit or two where translators can fill in their name and
        possibly their contact details. This test allows you to find these
        units easily to check that they are completed correctly and also
        disables other tests that might incorrectly get triggered for these
        units (such as urls, emails, etc.)
        """
        if str1 in self.config.credit_sources:
            raise FilterFailure(u"Don't translate. Just credit the translators.")
        else:
            return True


    # If the precondition filter is run and fails then the other tests listed are ignored
    preconditions = {
        "untranslated": ("simplecaps", "variables", "startcaps",
                         "accelerators", "brackets", "endpunc",
                         "acronyms", "xmltags", "startpunc",
                         "endwhitespace", "startwhitespace",
                         "escapes", "doublequoting", "singlequoting",
                         "filepaths", "purepunc", "doublespacing",
                         "sentencecount", "numbers", "isfuzzy",
                         "isreview", "notranslatewords", "musttranslatewords",
                         "emails", "simpleplurals", "urls", "printf",
                         "pythonbraceformat",
                         "tabs", "newlines", "functions", "options",
                         "blank", "nplurals", "gconf", "dialogsizes",
                         "validxml"),
          "blank": ("simplecaps", "variables", "startcaps",
                    "accelerators", "brackets", "endpunc",
                    "acronyms", "xmltags", "startpunc",
                    "endwhitespace", "startwhitespace",
                    "escapes", "doublequoting", "singlequoting",
                    "filepaths", "purepunc", "doublespacing",
                    "sentencecount", "numbers", "isfuzzy",
                    "isreview", "notranslatewords", "musttranslatewords",
                    "emails", "simpleplurals", "urls", "printf",
                    "pythonbraceformat",
                    "tabs", "newlines", "functions", "options",
                    "gconf", "dialogsizes", "validxml"),
          "credits": ("simplecaps", "variables", "startcaps",
                      "accelerators", "brackets", "endpunc",
                      "acronyms", "xmltags", "startpunc",
                      "escapes", "doublequoting", "singlequoting",
                      "filepaths", "doublespacing",
                      "sentencecount", "numbers",
                      "emails", "simpleplurals", "urls", "printf",
                      "pythonbraceformat",
                      "tabs", "newlines", "functions", "options",
                      "validxml"),
         "purepunc": ("startcaps", "options"),
         # This is causing some problems since Python 2.6, as
         # startcaps is now seen as an important one to always execute
         # and could now be done before it is blocked by a failing
         # "untranslated" or "blank" test. This is probably happening
         # due to slightly different implementation of the internal
         # dict handling since Python 2.6. We should never have relied
         # on this ordering anyway.
         #"startcaps": ("simplecaps",),
         "endwhitespace": ("endpunc",),
         "startwhitespace": ("startpunc",),
         "unchanged": ("doublewords",),
         "compendiumconflicts": ("accelerators", "brackets", "escapes",
                          "numbers", "startpunc", "long", "variables",
                          "startcaps", "sentencecount", "simplecaps",
                          "doublespacing", "endpunc", "xmltags",
                          "startwhitespace", "endwhitespace",
                          "singlequoting", "doublequoting",
                          "filepaths", "purepunc", "doublewords", "printf",
                          "newlines", "validxml"),
         }

# code to actually run the tests (use unittest?)

openofficeconfig = CheckerConfig(
    accelmarkers=["~"],
    varmatches=[("&", ";"), ("%", "%"), ("%", None), ("%", 0), ("$(", ")"),
                ("$", "$"), ("${", "}"), ("#", "#"), ("#", 1), ("#", 0),
                ("($", ")"), ("$[", "]"), ("[", "]"), ("@", "@"),
                ("$", None)],
    ignoretags=[("alt", "xml-lang", None), ("ahelp", "visibility", "visible"),
                ("img", "width", None), ("img", "height", None)],
    canchangetags=[("link", "name", None)],
)


class OpenOfficeChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(openofficeconfig)
        StandardChecker.__init__(self, **kwargs)

libreofficeconfig = CheckerConfig(
    accelmarkers=["~"],
    varmatches=[("&", ";"), ("%", "%"), ("%", None), ("%", 0), ("$(", ")"),
                ("$", "$"), ("${", "}"), ("#", "#"), ("#", 1), ("#", 0),
                ("($", ")"), ("$[", "]"), ("[", "]"), ("@", "@"),
                ("$", None)],
    ignoretags=[("alt", "xml-lang", None), ("ahelp", "visibility", "visible"),
                ("img", "width", None), ("img", "height", None)],
    canchangetags=[("link", "name", None)],
)


class LibreOfficeChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(libreofficeconfig)
        checkerconfig.update(openofficeconfig)
        StandardChecker.__init__(self, **kwargs)


    @critical
    def validxml(self, str1, str2):
        """Check that all XML/HTML open/close tags has close/open
        pair in the translation."""
        for location in self.locations:
            if location.endswith(".xrm") or location.endswith(".xhp"):
                opentags = []
                match = re.search(lo_tag_re, str2)
                while match:
                    acttag = match.group(0)
                    if acttag.startswith("</"):
                        if len(opentags) == 0:
                            raise FilterFailure(u"There is no open tag for %s" % (acttag))
                        opentag = opentags.pop()
                        if tagname(acttag) != "/" + tagname(opentag):
                            raise FilterFailure(u"Open tag %s and close tag %s "
                                                 "don't match" % (opentag, acttag))
                    else:
                        opentags.append(acttag)
                    str2 = str2[match.end(0):]
                    match = re.search(lo_tag_re, str2)
                if len(opentags) != 0:
                    raise FilterFailure(u"There is no close tag for %s" % (opentags.pop()))
        return True


mozillaconfig = CheckerConfig(
    accelmarkers=["&"],
    varmatches=[("&", ";"), ("%", "%"), ("%", 1), ("$", "$"), ("$", None),
                ("#", 1), ("${", "}"), ("$(^", ")"), ("{{", "}}"), ],
    criticaltests=["accelerators"],
)


class MozillaChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(mozillaconfig)
        StandardChecker.__init__(self, **kwargs)


    @extraction
    def credits(self, str1, str2):
        """Checks for messages containing translation credits instead of
        normal translations.

        Some projects have consistent ways of giving credit to translators by
        having a unit or two where translators can fill in their name and
        possibly their contact details. This test allows you to find these
        units easily to check that they are completed correctly and also
        disables other tests that might incorrectly get triggered for these
        units (such as urls, emails, etc.)
        """
        for location in self.locations:
            if location in ['MOZ_LANGPACK_CONTRIBUTORS', 'credit.translation']:
                raise FilterFailure(u"Don't translate. Just credit the translators.")

        return True


    mozilla_dialog_re = re.compile("""(                          # option pair "key: value;"
                                      (?P<key>[-a-z]+)           # key
                                      :\s+                       # seperator
                                      (?P<number>\d+(?:[.]\d+)?) # number
                                      (?P<unit>[a-z][a-z]);?     # units
                                      )+                         # multiple pairs
                                   """, re.VERBOSE)
    mozilla_dialog_valid_units = ['em', 'px', 'ch']


    @critical
    def dialogsizes(self, str1, str2):
        """Checks that dialog sizes are not translated.

        This is a Mozilla specific test. Mozilla uses a language called XUL to
        define dialogues and screens. This can make use of CSS to specify
        properties of the dialogue. These properties include things such as the
        width and height of the box. The size might need to be changed if the
        dialogue size changes due to longer translations. Thus translators can
        change these settings. But you are only meant to change the number not
        translate the words 'width' or 'height'. This check capture instances
        where these are translated. It will also catch other types of errors in
        these units.
        """
        # Example: "width: 635px; height: 400px;"
        if "width" in str1 or "height" in str1:
            str1pairs = self.mozilla_dialog_re.findall(str1)

            if str1pairs:
                str2pairs = self.mozilla_dialog_re.findall(str2)

                if len(str1pairs) != len(str2pairs):
                    raise FilterFailure(u"A dialog pair is missing")

                for i, pair1 in enumerate(str1pairs):
                    pair2 = str2pairs[i]

                    if pair1[0] != pair2[0]:  # Only check pairs that differ
                        if len(pair2) != 4:
                            raise FilterFailure(u"A part of the dialog pair is missing")

                        if pair1[1] not in pair2:  # key
                            raise FilterFailure(u"Do not translate the key '%s'" % pair1[1])

                        # FIXME we could check more carefully for numbers in pair1[2]
                        if pair2[3] not in self.mozilla_dialog_valid_units:
                            raise FilterFailure(u"Units should be one of '%s'. "
                                                 "The source string uses '%s'" % (", ".join(self.mozilla_dialog_valid_units), pair1[3]))

        return True


    @functional
    def numbers(self, str1, str2):
        """Checks that numbers are not translated.

        Special handling for Mozilla to ignore entries that are dialog sizes.
        """
        if self.mozilla_dialog_re.findall(str1):
            return True

        return super(MozillaChecker, self).numbers(str1, str2)


    @functional
    def unchanged(self, str1, str2):
        """Checks whether a translation is basically identical to the original
        string.

        Special handling for Mozilla to ignore entries that are dialog sizes.
        """
        if (self.mozilla_dialog_re.findall(str1) or
            str1.strip().lstrip('0123456789') in self.mozilla_dialog_valid_units):
            return True

        return super(MozillaChecker, self).unchanged(str1, str2)

    @cosmetic
    def accelerators(self, str1, str2):
        """Checks whether accelerators are consistent between the
        two strings.

        For Mozilla we lower the severity to cosmetic.
        """
        return super(MozillaChecker, self).accelerators(str1, str2)

drupalconfig = CheckerConfig(
    varmatches=[("%", None), ("@", None), ("!", None)],
)


class DrupalChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(drupalconfig)
        StandardChecker.__init__(self, **kwargs)


gnomeconfig = CheckerConfig(
    accelmarkers=["_"],
    varmatches=[("%", 1), ("$(", ")")],
    credit_sources=[u"translator-credits"],
)


class GnomeChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(gnomeconfig)
        StandardChecker.__init__(self, **kwargs)


    @functional
    def gconf(self, str1, str2):
        """Checks if we have any gconf config settings translated.

        Gconf settings should not be translated so this check checks that gconf
        settings such as "name" or "modification_date" are not translated in
        the translation. It allows you to change the surrounding quotes but
        will ensure that the setting values remain untranslated.
        """
        for location in self.locations:
            if location.find('schemas.in') != -1 or location.find('gschema.xml.in') != -1:
                gconf_attributes = gconf_attribute_re.findall(str1)
                #stopwords = [word for word in words1 if word in self.config.notranslatewords and word not in words2]
                stopwords = [word for word in gconf_attributes if word[1:-1] not in str2]

                if stopwords:
                    raise FilterFailure(u"Do not translate GConf attributes: %s" %
                                        (u", ".join(stopwords)))

                return True

        return True


kdeconfig = CheckerConfig(
    accelmarkers=["&"],
    varmatches=[("%", 1)],
    credit_sources=[u"Your names", u"Your emails", u"ROLES_OF_TRANSLATORS"],
)


class KdeChecker(StandardChecker):

    def __init__(self, **kwargs):
        # TODO allow setup of KDE plural and translator comments so that they do
        # not create false postives
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(kdeconfig)
        StandardChecker.__init__(self, **kwargs)


cclicenseconfig = CheckerConfig(varmatches=[("@", "@")])


class CCLicenseChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(cclicenseconfig)
        StandardChecker.__init__(self, **kwargs)


termconfig = CheckerConfig()


class TermChecker(StandardChecker):

    def __init__(self, **kwargs):
        checkerconfig = kwargs.get("checkerconfig", None)

        if checkerconfig is None:
            checkerconfig = CheckerConfig()
            kwargs["checkerconfig"] = checkerconfig

        checkerconfig.update(termconfig)
        StandardChecker.__init__(self, **kwargs)


projectcheckers = {
    "openoffice": OpenOfficeChecker,
    "libreoffice": LibreOfficeChecker,
    "mozilla": MozillaChecker,
    "kde": KdeChecker,
    "wx": KdeChecker,
    "gnome": GnomeChecker,
    "creativecommons": CCLicenseChecker,
    "drupal": DrupalChecker,
    "terminology": TermChecker,
}


class StandardUnitChecker(UnitChecker):
    """The standard checks for common checks on translation units."""


    @extraction
    def isfuzzy(self, unit):
        """Check if the unit has been marked fuzzy.

        If a message is marked fuzzy in the PO file then it is extracted.
        Note this is different from ``--fuzzy`` and ``--nofuzzy`` options which
        specify whether tests should be performed against messages marked
        fuzzy.
        """
        return not unit.isfuzzy()


    @extraction
    def isreview(self, unit):
        """Check if the unit has been marked review.

        If you have made use of the 'review' flags in your translations::

          # (review) reason for review
          # (pofilter) testname: explanation for translator

        Then if a message is marked for review in the PO file it will be
        extracted. Note this is different from ``--review`` and ``--noreview``
        options which specify whether tests should be performed against
        messages already marked as under review.
        """
        return not unit.isreview()


    @critical
    def nplurals(self, unit):
        """Checks for the correct number of noun forms for plural translations.

        This uses the plural information in the language module of the
        Translate Toolkit. This is the same as the Gettext nplural value. It
        will check that the number of plurals required is the same as the
        number supplied in your translation.
        """
        if unit.hasplural():
            # if we don't have a valid nplurals value, don't run the test
            nplurals = self.config.lang.nplurals

            if nplurals > 0:
                return len(filter(None, unit.target.strings)) == nplurals

        return True


    @extraction
    def hassuggestion(self, unit):
        """Checks if there is at least one suggested translation for this unit.

        If a message has a suggestion (an alternate translation stored in
        alt-trans units in XLIFF and .pending files in PO) then these will be
        extracted. This is used by Pootle and is probably only useful in
        pofilter when using XLIFF files.
        """
        self.suggestion_store = getattr(self, 'suggestion_store', None)
        suggestions = []

        if self.suggestion_store:
            suggestions = self.suggestion_store.findunits(unit.source)
        elif getattr(unit, "getalttrans", None):
            # TODO: we probably want to filter them somehow
            suggestions = unit.getalttrans()

        return not bool(suggestions)


def runtests(str1, str2, ignorelist=()):
    """Verifies that the tests pass for a pair of strings."""
    from translate.storage import base
    str1 = data.normalized_unicode(str1)
    str2 = data.normalized_unicode(str2)
    unit = base.TranslationUnit(str1)
    unit.target = str2
    checker = StandardChecker(excludefilters=ignorelist)
    failures = checker.run_filters(unit)

    for test in failures:
        print("failure: %s: %s\n  %r\n  %r" % \
              (test, failures[test]['message'], str1, str2))

    return failures


def batchruntests(pairs):
    """Runs test on a batch of string pairs."""
    passed, numpairs = 0, len(pairs)

    for str1, str2 in pairs:
        if runtests(str1, str2):
            passed += 1

    print("\ntotal: %d/%d pairs passed" % (passed, numpairs))


if __name__ == '__main__':
    testset = [(r"simple", r"somple"),
            (r"\this equals \that", r"does \this equal \that?"),
            (r"this \'equals\' that", r"this 'equals' that"),
            (r" start and end! they must match.",
             r"start and end! they must match."),
            (r"check for matching %variables marked like %this",
             r"%this %variable is marked"),
            (r"check for mismatching %variables marked like %this",
             r"%that %variable is marked"),
            (r"check for mismatching %variables% too",
             r"how many %variable% are marked"),
            (r"%% %%", r"%%"),
            (r"Row: %1, Column: %2", r"Mothalo: %1, Kholomo: %2"),
            (r"simple lowercase", r"it is all lowercase"),
            (r"simple lowercase", r"It Is All Lowercase"),
            (r"Simple First Letter Capitals", r"First Letters"),
            (r"SIMPLE CAPITALS", r"First Letters"),
            (r"SIMPLE CAPITALS", r"ALL CAPITALS"),
            (r"forgot to translate", r"  "),
            ]
    batchruntests(testset)
