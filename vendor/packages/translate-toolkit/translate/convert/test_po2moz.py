#!/usr/bin/env python

from translate.convert import po2moz
from translate.convert import test_convert

class TestPO2Moz:
    pass

class TestPO2MozCommand(test_convert.TestConvertCommand, TestPO2Moz):
    """Tests running actual po2moz commands on files"""
    convertmodule = po2moz
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "-l LOCALE, --locale=LOCALE")
        options = self.help_check(options, "--clonexpi=CLONEXPI")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy", last=True)
