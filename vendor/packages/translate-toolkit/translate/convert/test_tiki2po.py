#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tiki2po unit tests
# Author: Wil Clouser <wclouser@mozilla.com>
# Date: 2008-12-01

from translate.convert import tiki2po
from translate.storage import tiki
from translate.convert import test_convert
from translate.misc import wStringIO

class TestTiki2Po:
    def test_converttiki_defaults(self):
        inputfile = """
"zero_source" => "zero_target",
// ### Start of unused words
"one_source" => "one_target",
// ### end of unused words
        """
        outputfile = wStringIO.StringIO()
        tiki2po.converttiki(inputfile, outputfile)

        output =  outputfile.getvalue()

        assert '#: translated' in output
        assert 'msgid "zero_source"' in output
        assert "one_source" not in output

    def test_converttiki_includeunused(self):
        inputfile = """
"zero_source" => "zero_target",
// ### Start of unused words
"one_source" => "one_target",
// ### end of unused words
        """
        outputfile = wStringIO.StringIO()
        tiki2po.converttiki(inputfile, outputfile, includeunused=True)

        output =  outputfile.getvalue()

        assert '#: translated' in output
        assert 'msgid "zero_source"' in output
        assert '#: unused' in output
        assert 'msgid "one_source"' in output


class TestTiki2PoCommand(test_convert.TestConvertCommand, TestTiki2Po):
    """Tests running actual tiki2po commands on files"""
    convertmodule = tiki2po
    defaultoptions = {}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "--include-unused")
