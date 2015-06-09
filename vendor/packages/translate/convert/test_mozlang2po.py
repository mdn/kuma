#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import mozlang2po, test_convert
from translate.misc import wStringIO
from translate.storage import mozilla_lang as lang


class TestLang2PO:

    def lang2po(self, source):
        """helper that converts .lang source to po source without requiring files"""
        inputfile = wStringIO.StringIO(source)
        inputlang = lang.LangStore(inputfile)
        convertor = mozlang2po.lang2po()
        outputpo = convertor.convertstore(inputlang)
        return outputpo

    def convertlng(self, source):
        """call the convertlng, return the outputfile"""
        inputfile = wStringIO.StringIO(source)
        outputfile = wStringIO.StringIO()
        templatefile = None
        assert lang2po.convertlang(inputfile, outputfile, templatefile)
        return outputfile.getvalue()

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.units) == 2
        assert pofile.units[0].isheader()
        print(pofile)
        return pofile.units[1]

    def countelements(self, pofile):
        """counts the number of non-header entries"""
        assert pofile.units[0].isheader()
        print(pofile)
        return len(pofile.units) - 1

    def test_simpleentry(self):
        """checks that a simple lang entry converts properly to a po entry"""
        source = ';One\nEen\n'
        pofile = self.lang2po(source)
        pounit = self.singleelement(pofile)
        assert pounit.source == "One"
        assert pounit.target == "Een"

    def test_simpleentry(self):
        """Handle simple comments"""
        source = '# Comment\n;One\nEen\n'
        pofile = self.lang2po(source)
        pounit = self.singleelement(pofile)
        assert pounit.source == "One"
        assert pounit.target == "Een"
        assert pounit.getnotes() == "Comment"


class TestLang2POCommand(test_convert.TestConvertCommand, TestLang2PO):
    """Tests running actual lang2po commands on files"""
    convertmodule = mozlang2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "--encoding=ENCODING")
        options = self.help_check(options, "--duplicates=DUPLICATESTYLE", last=True)
