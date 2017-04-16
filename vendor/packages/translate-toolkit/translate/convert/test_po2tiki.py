#!/usr/bin/env python
# -*- coding: utf-8 -*-

# po2tiki unit tests
# Author: Wil Clouser <wclouser@mozilla.com>
# Date: 2008-12-01

from translate.convert import po2tiki
from translate.storage import tiki
from translate.convert import test_convert
from translate.misc import wStringIO

class TestPo2Tiki:
    def test_convertpo(self):
        inputfile = """
#: translated
msgid "zero_source"
msgstr "zero_target"

#: unused
msgid "one_source"
msgstr "one_target"
        """
        outputfile = wStringIO.StringIO()
        po2tiki.convertpo(inputfile, outputfile)

        output =  outputfile.getvalue()

        assert '"one_source" => "one_target",' in output
        assert '"zero_source" => "zero_target",' in output


class TestPo2TikiCommand(test_convert.TestConvertCommand, TestPo2Tiki):
    """Tests running actual po2tiki commands on files"""
    convertmodule = po2tiki
    defaultoptions = {}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
