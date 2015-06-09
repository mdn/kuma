#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import po2mozlang, test_convert
from translate.misc import wStringIO
from translate.storage import po


class TestPO2Lang:

    def po2lang(self, posource):
        """helper that converts po source to .lang source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2mozlang.po2lang(mark_active=False)
        outputlang = convertor.convertstore(inputpo)
        return outputlang

    def test_simple(self):
        """check the simplest case of merging a translation"""
        posource = '''#: prop\nmsgid "Source"\nmsgstr "Target"\n'''
        propexpected = ''';Source\nTarget\n'''
        langfile = self.po2lang(posource)
        print(langfile)
        assert str(langfile) == propexpected

    def test_comment(self):
        """Simple # comments"""
        posource = '''#. Comment\n#: prop\nmsgid "Source"\nmsgstr "Target"\n'''
        propexpected = '''# Comment\n;Source\nTarget\n'''
        langfile = self.po2lang(posource)
        print(langfile)
        assert str(langfile) == propexpected

    def test_fuzzy(self):
        """What happens with a fuzzy string"""
        posource = '''#. Comment\n#: prop\n#, fuzzy\nmsgid "Source"\nmsgstr "Target"\n'''
        propexpected = '''# Comment\n;Source\nSource\n'''
        langfile = self.po2lang(posource)
        print(langfile)
        assert str(langfile) == propexpected

    def test_ok_marker(self):
        """The {ok} marker"""
        posource = '''#: prop\nmsgid "Same"\nmsgstr "Same"\n'''
        propexpected = ''';Same\nSame {ok}\n'''
        langfile = self.po2lang(posource)
        print(langfile)
        assert str(langfile) == propexpected


class TestPO2LangCommand(test_convert.TestConvertCommand, TestPO2Lang):
    """Tests running actual po2prop commands on files"""
    convertmodule = po2mozlang
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--threshold=PERCENT")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--mark-active")
        options = self.help_check(options, "--nofuzzy", last=True)
