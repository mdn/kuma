#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
pytest.importorskip("vobject")

from translate.convert import po2ical, test_convert
from translate.misc import wStringIO
from translate.storage import po


icalboiler = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//hacksw/handcal//NONSGML v1.0//EN
BEGIN:VEVENT
UID:uid1@example.com
DTSTART:19970714T170000Z
DTEND:19970715T035959Z
DTSTAMP:19970714T170000Z
ORGANIZER;CN=John Doe:MAILTO:john.doe@example.com
SUMMARY:%s
END:VEVENT
END:VCALENDAR
'''.replace("\n", "\r\n")


class TestPO2Ical:

    def po2ical(self, posource):
        """helper that converts po source to .ics source without requiring
        files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2ical.reical()
        outputical = convertor.convertstore(inputpo)
        return outputical

    def merge2ical(self, propsource, posource):
        """helper that merges po translations to .ics source without requiring
        files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(propsource)
        #templateprop = properties.propfile(templatefile)
        convertor = po2ical.reical(templatefile, inputpo)
        outputical = convertor.convertstore()
        print(outputical)
        return outputical

    def test_simple_summary(self):
        """test that we output correctly for Inno files."""
        posource = ur'''#: [uid1@example.com]SUMMARY
msgid "Value"
msgstr "Waarde"
'''
        icaltemplate = icalboiler % "Value"
        icalexpected = icalboiler % "Waarde"
        icalfile = self.merge2ical(icaltemplate, posource)
        print(icalexpected)
        assert icalfile == icalexpected

    # FIXME we should also test for DESCRIPTION, LOCATION and COMMENT
    # The library handle any special encoding issues, we might want to test
    # those


class TestPO2IcalCommand(test_convert.TestConvertCommand, TestPO2Ical):
    """Tests running actual po2ical commands on files"""
    convertmodule = po2ical
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--threshold=PERCENT")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy", last=True)
