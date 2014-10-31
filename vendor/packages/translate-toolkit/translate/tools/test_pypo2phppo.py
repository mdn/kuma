#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pypo2phppo unit tests
# Author: Wil Clouser <wclouser@mozilla.com>
# Date: 2009-12-03

from translate.tools import pypo2phppo
from translate.storage import po
from translate.convert import test_convert
from translate.misc import wStringIO

class TestPyPo2PhpPo:
    def test_single_po(self):
        inputfile = """
# This user comment refers to: {0}
#. This developer comment does too: {0}
#: some/path.php:111
#, php-format
msgid "I have {1} apples and {0} oranges"
msgstr "I have {1} apples and {0} oranges"
        """
        outputfile = wStringIO.StringIO()
        pypo2phppo.convertpy2php(inputfile, outputfile)

        output = outputfile.getvalue()

        assert "refers to: %1$s" in output
        assert "does too: %1$s" in output
        assert 'msgid "I have %2$s apples and %1$s oranges"' in output
        assert 'msgstr "I have %2$s apples and %1$s oranges"' in output

    def test_plural_po(self):
        inputfile = """
#. This developer comment refers to {0}
#: some/path.php:111
#, php-format
msgid "I have {0} apple"
msgid_plural "I have {0} apples"
msgstr[0] "I have {0} apple"
msgstr[1] "I have {0} apples"
        """
        outputfile = wStringIO.StringIO()
        pypo2phppo.convertpy2php(inputfile, outputfile)
        output =  outputfile.getvalue()

        assert 'msgid "I have %1$s apple"' in output
        assert 'msgid_plural "I have %1$s apples"' in output
        assert 'msgstr[0] "I have %1$s apple"' in output
        assert 'msgstr[1] "I have %1$s apples"' in output

class TestPyPo2PhpPoCommand(test_convert.TestConvertCommand, TestPyPo2PhpPo):
    """Tests running actual pypo2phppo commands on files"""
    convertmodule = pypo2phppo
    defaultoptions = {}
