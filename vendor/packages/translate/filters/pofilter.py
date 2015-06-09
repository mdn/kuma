#!/usr/bin/env python
#
# Copyright 2004-2007 Zuza Software Foundation
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

"""Perform quality checks on Gettext PO, XLIFF and TMX localization files.

Snippet files are created whenever a test fails.  These can be examined,
corrected and merged back into the originals using pomerge.

See:
http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/pofilter.html
for examples and usage instructions and
http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/pofilter_tests.html
for full descriptions of all tests.
"""

import os

from translate.filters import autocorrect, checks
from translate.misc import optrecurse
from translate.storage import factory
from translate.storage.poheader import poheader


def build_checkerconfig(options):
    """Prepare the checker config from the given options.  This is mainly
    factored out for the sake of unit tests."""
    checkerconfig = checks.CheckerConfig(targetlanguage=options.targetlanguage)

    if options.notranslatefile:
        options.notranslatefile = os.path.expanduser(options.notranslatefile)

        if not os.path.exists(options.notranslatefile):
            self.error("notranslatefile %r does not exist" % options.notranslatefile)

        notranslatewords = [line.strip() for line in open(options.notranslatefile).readlines()]
        notranslatewords = dict.fromkeys([key for key in notranslatewords])

        checkerconfig.notranslatewords.update(notranslatewords)

    if options.musttranslatefile:
        options.musttranslatefile = os.path.expanduser(options.musttranslatefile)

        if not os.path.exists(options.musttranslatefile):
            self.error("musttranslatefile %r does not exist" % options.musttranslatefile)

        musttranslatewords = [line.strip() for line in open(options.musttranslatefile).readlines()]
        musttranslatewords = dict.fromkeys([key for key in musttranslatewords])

        checkerconfig.musttranslatewords.update(musttranslatewords)

    if options.validcharsfile:
        options.validcharsfile = os.path.expanduser(options.validcharsfile)

        if not os.path.exists(options.validcharsfile):
            self.error("validcharsfile %r does not exist" % options.validcharsfile)

        validchars = open(options.validcharsfile).read()

        checkerconfig.updatevalidchars(validchars)

    return checkerconfig


class pocheckfilter:

    def __init__(self, options, checkerclasses=None, checkerconfig=None):
        # excludefilters={}, limitfilters=None, includefuzzy=True, includereview=True, autocorrect=False):
        """Builds a checkfilter using the given checker (a list is allowed too)"""
        if checkerclasses is None:
            checkerclasses = [checks.StandardChecker, checks.StandardUnitChecker]

        self.checker = checks.TeeChecker(checkerconfig=checkerconfig,
                                         excludefilters=options.excludefilters,
                                         limitfilters=options.limitfilters,
                                         checkerclasses=checkerclasses,
                                         languagecode=checkerconfig.targetlanguage)
        self.options = options


    def getfilterdocs(self):
        """Lists the docs for filters available on checker."""
        filterdict = self.checker.getfilters()
        filterdocs = ["%s\t%s" % (name, filterfunc.__doc__) for (name, filterfunc) in filterdict.iteritems()]
        filterdocs.sort()

        return "\n".join(filterdocs)


    def filterunit(self, unit):
        """Runs filters on an element."""

        if unit.isheader():
            return []

        if not self.options.includefuzzy and unit.isfuzzy():
            return []

        if not self.options.includereview and unit.isreview():
            return []

        failures = self.checker.run_filters(unit, categorised=True)

        if failures and self.options.autocorrect:
            # we can't get away with bad unquoting / requoting if we're going to change the result...
            correction = autocorrect.correct(unit.source, unit.target)

            if correction:
                unit.target = correction
                return autocorrect
            else:
                # ignore failures we can't correct when in autocorrect mode
                return []

        return failures


    def filterfile(self, transfile):
        """Runs filters on a translation store object.

        :param transfile: A translation store object.
        :return: A new translation store object with the results of
                 the filter included.
        """
        newtransfile = type(transfile)()
        newtransfile.setsourcelanguage(transfile.getsourcelanguage())
        newtransfile.settargetlanguage(transfile.gettargetlanguage())

        for unit in transfile.units:
            filter_result = self.filterunit(unit)

            if filter_result:
                if filter_result != autocorrect:
                    for filter_name in filter_result.iterkeys():
                        filter_message = filter_result[filter_name]['message']

                        if self.options.addnotes:
                            unit.adderror(filter_name, filter_message)
                        if isinstance(filter_message, checks.SeriousFilterFailure):
                            unit.markfuzzy()

                newtransfile.addunit(unit)

        if isinstance(newtransfile, poheader):
            newtransfile.updateheader(add=True, **transfile.parseheader())

        return newtransfile


class FilterOptionParser(optrecurse.RecursiveOptionParser):
    """A specialized Option Parser for filter tools..."""

    def __init__(self, formats):
        """Construct the specialized Option Parser."""
        optrecurse.RecursiveOptionParser.__init__(self, formats)

        self.set_usage()
        self.add_option("-l", "--listfilters", action="callback", dest='listfilters',
            default=False, callback_kwargs={'dest_value': True},
            callback=self.parse_noinput, help="list filters available")


    def parse_noinput(self, option, opt, value, parser, *args, **kwargs):
        """This sets an option to *True*, but also sets input to *-*
        to prevent an error."""
        setattr(parser.values, option.dest, kwargs['dest_value'])
        parser.values.input = "-"


    def run(self):
        """Parses the arguments, and runs recursiveprocess with the
        resulting options."""
        (options, args) = self.parse_args()

        if options.filterclass is None:
            checkerclasses = [checks.StandardChecker, checks.StandardUnitChecker]
        else:
            checkerclasses = [options.filterclass, checks.StandardUnitChecker]

        checkerconfig = build_checkerconfig(options)
        options.checkfilter = pocheckfilter(options, checkerclasses, checkerconfig)

        if not options.checkfilter.checker.combinedfilters:
            self.error("No valid filters were specified")

        options.inputformats = self.inputformats
        options.outputoptions = self.outputoptions

        if options.listfilters:
            print(options.checkfilter.getfilterdocs())
        else:
            self.recursiveprocess(options)


def runfilter(inputfile, outputfile, templatefile, checkfilter=None):
    """Reads in inputfile, filters using checkfilter, writes to outputfile."""
    fromfile = factory.getobject(inputfile)
    tofile = checkfilter.filterfile(fromfile)

    if tofile.isempty():
        return 0

    outputfile.write(str(tofile))

    return 1


def cmdlineparser():
    formats = {"po": ("po", runfilter), "pot": ("pot", runfilter),
            "xliff": ("xliff", runfilter), "xlf": ("xlf", runfilter),
            "tmx": ("tmx", runfilter),
            None: ("po", runfilter)}

    parser = FilterOptionParser(formats)

    parser.add_option("", "--review", dest="includereview",
        action="store_true", default=True,
        help="include units marked for review (default)")
    parser.add_option("", "--noreview", dest="includereview",
        action="store_false", default=True,
        help="exclude units marked for review")
    parser.add_option("", "--fuzzy", dest="includefuzzy",
        action="store_true", default=True,
        help="include units marked fuzzy (default)")
    parser.add_option("", "--nofuzzy", dest="includefuzzy",
        action="store_false", default=True,
        help="exclude units marked fuzzy")
    parser.add_option("", "--nonotes", dest="addnotes",
        action="store_false", default=True,
        help="don't add notes about the errors")
    parser.add_option("", "--autocorrect", dest="autocorrect",
        action="store_true", default=False,
        help="output automatic corrections where possible rather than describing issues")
    parser.add_option("", "--language", dest="targetlanguage", default=None,
        help="set target language code (e.g. af-ZA) [required for spell check and recommended in general]", metavar="LANG")
    parser.add_option("", "--openoffice", dest="filterclass",
        action="store_const", default=None, const=checks.OpenOfficeChecker,
        help="use the standard checks for OpenOffice translations")
    parser.add_option("", "--libreoffice", dest="filterclass",
        action="store_const", default=None, const=checks.LibreOfficeChecker,
        help="use the standard checks for LibreOffice translations")
    parser.add_option("", "--mozilla", dest="filterclass",
        action="store_const", default=None, const=checks.MozillaChecker,
        help="use the standard checks for Mozilla translations")
    parser.add_option("", "--drupal", dest="filterclass",
        action="store_const", default=None, const=checks.DrupalChecker,
        help="use the standard checks for Drupal translations")
    parser.add_option("", "--gnome", dest="filterclass",
        action="store_const", default=None, const=checks.GnomeChecker,
        help="use the standard checks for Gnome translations")
    parser.add_option("", "--kde", dest="filterclass",
        action="store_const", default=None, const=checks.KdeChecker,
        help="use the standard checks for KDE translations")
    parser.add_option("", "--wx", dest="filterclass",
        action="store_const", default=None, const=checks.KdeChecker,
        help="use the standard checks for wxWidgets translations")
    parser.add_option("", "--excludefilter", dest="excludefilters",
        action="append", default=[], type="string", metavar="FILTER",
        help="don't use FILTER when filtering")
    parser.add_option("-t", "--test", dest="limitfilters",
        action="append", default=None, type="string", metavar="FILTER",
        help="only use test FILTERs specified with this option when filtering")
    parser.add_option("", "--notranslatefile", dest="notranslatefile",
        default=None, type="string", metavar="FILE",
        help="read list of untranslatable words from FILE (must not be translated)")
    parser.add_option("", "--musttranslatefile", dest="musttranslatefile",
        default=None, type="string", metavar="FILE",
        help="read list of translatable words from FILE (must be translated)")
    parser.add_option("", "--validcharsfile", dest="validcharsfile",
        default=None, type="string", metavar="FILE",
        help="read list of all valid characters from FILE (must be in UTF-8)")

    parser.passthrough.append('checkfilter')
    parser.description = __doc__

    return parser


def main():
    parser = cmdlineparser()
    parser.run()


if __name__ == '__main__':
    main()
