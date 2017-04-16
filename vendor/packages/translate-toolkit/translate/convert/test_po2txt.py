#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import po2txt
from translate.convert import test_convert
from translate.misc import wStringIO

class TestPO2Txt:
    def po2txt(self, posource, txttemplate=None):
        """helper that converts po source to txt source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        print inputfile.getvalue()
        outputfile = wStringIO.StringIO()
        if txttemplate:
            templatefile = wStringIO.StringIO(txttemplate)
        else:
            templatefile = None
        assert po2txt.converttxt(inputfile, outputfile, templatefile)
        print outputfile.getvalue()
        return outputfile.getvalue()

    def test_basic(self):
        """test basic conversion"""
        txttemplate = "Heading\n\nBody text"
        posource = 'msgid "Heading"\nmsgstr "Opskrif"\n\nmsgid "Body text"\nmsgstr "Lyfteks"\n'
        assert self.po2txt(posource, txttemplate) == "Opskrif\n\nLyfteks"

    def test_nonascii(self):
        """test conversion with non-ascii text"""
        txttemplate = "Heading\n\nFile content"
        posource = 'msgid "Heading"\nmsgstr "Opskrif"\n\nmsgid "File content"\nmsgstr "Lêerinhoud"\n'
        assert self.po2txt(posource, txttemplate) == "Opskrif\n\nLêerinhoud"

    def test_blank_handling(self):
        """check that we discard blank messages"""
        txttemplate = "Heading\n\nBody text"
        posource = 'msgid "Heading"\nmsgstr "Opskrif"\n\nmsgid "Body text"\nmsgstr ""\n'
        assert self.po2txt(posource) == "Opskrif\n\nBody text"
        assert self.po2txt(posource, txttemplate) == "Opskrif\n\nBody text"

    def test_fuzzy_handling(self):
        """check that we handle fuzzy message correctly"""
        txttemplate = "Heading\n\nBody text"
        posource = '#, fuzzy\nmsgid "Heading"\nmsgstr "Opskrif"\n\nmsgid "Body text"\nmsgstr "Lyfteks"\n'
        assert self.po2txt(posource) == "Heading\n\nLyfteks"
        assert self.po2txt(posource, txttemplate) == "Heading\n\nLyfteks"

class TestPO2TxtCommand(test_convert.TestConvertCommand, TestPO2Txt):
    """Tests running actual po2txt commands on files"""
    convertmodule = po2txt
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy")
        options = self.help_check(options, "--encoding")
        options = self.help_check(options, "-w WRAP, --wrap=WRAP", last=True)
