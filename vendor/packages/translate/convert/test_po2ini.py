#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import importorskip

from translate.convert import po2ini, test_convert
from translate.misc import wStringIO
from translate.storage import po


importorskip("iniparse")


class TestPO2Ini:

    def po2ini(self, posource):
        """helper that converts po source to .ini source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2ini.reini()
        outputini = convertor.convertstore(inputpo)
        return outputini

    def merge2ini(self, inisource, posource, dialect="default"):
        """helper that merges po translations to .ini source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(inisource)
        convertor = po2ini.reini(templatefile, inputpo, dialect=dialect)
        outputini = convertor.convertstore()
        print(outputini)
        return outputini

    def test_merging_simple(self):
        """check the simplest case of merging a translation"""
        posource = '''#: [section]prop\nmsgid "value"\nmsgstr "waarde"\n'''
        initemplate = '''[section]\nprop=value\n'''
        iniexpected = '''[section]\nprop=waarde\n'''
        inifile = self.merge2ini(initemplate, posource)
        print(inifile)
        assert inifile == iniexpected

    def test_space_preservation(self):
        """check that we preserve any spacing in ini files when merging"""
        posource = '''#: [section]prop\nmsgid "value"\nmsgstr "waarde"\n'''
        initemplate = '''[section]\nprop  =  value\n'''
        iniexpected = '''[section]\nprop  =  waarde\n'''
        inifile = self.merge2ini(initemplate, posource)
        print(inifile)
        assert inifile == iniexpected

    def test_merging_blank_entries(self):
        """check that we can correctly merge entries that are blank in the template"""
        posource = r'''#: [section]accesskey-accept
msgid ""
"_: accesskey-accept\n"
""
msgstr ""'''
        initemplate = '[section]\naccesskey-accept=\n'
        iniexpected = '[section]\naccesskey-accept=\n'
        inifile = self.merge2ini(initemplate, posource)
        print(inifile)
        assert inifile == iniexpected

    def test_merging_fuzzy(self):
        """check merging a fuzzy translation"""
        posource = '''#: [section]prop\n#, fuzzy\nmsgid "value"\nmsgstr "waarde"\n'''
        initemplate = '''[section]\nprop=value\n'''
        iniexpected = '''[section]\nprop=value\n'''
        inifile = self.merge2ini(initemplate, posource)
        print(inifile)
        assert inifile == iniexpected

    def test_merging_propertyless_template(self):
        """check that when merging with a template with no ini values that we copy the template"""
        posource = ""
        initemplate = "# A comment\n"
        iniexpected = initemplate
        inifile = self.merge2ini(initemplate, posource)
        print(inifile)
        assert inifile == iniexpected

    def test_empty_value(self):
        """test that we handle an value in translation that is missing in the template"""
        posource = '''#: [section]key
msgctxt "key"
msgid ""
msgstr "translated"
'''
        initemplate = '''[section]\nkey =\n'''
        iniexpected = '''[section]\nkey =translated\n'''
        inifile = self.merge2ini(initemplate, posource)
        print(inifile)
        assert inifile == iniexpected

    def test_dialects_inno(self):
        """test that we output correctly for Inno files."""
        posource = ur'''#: [section]prop
msgid "value\tvalue2\n"
msgstr "ṽḁḽṻḝ\tṽḁḽṻḝ2\n"
'''
        initemplate = '''[section]\nprop  =  value%tvalue%n\n'''
        iniexpected = '''[section]\nprop  =  ṽḁḽṻḝ%tṽḁḽṻḝ2%n\n'''
        inifile = self.merge2ini(initemplate, posource, "inno")
        print(inifile)
        assert inifile == iniexpected


class TestPO2IniCommand(test_convert.TestConvertCommand, TestPO2Ini):
    """Tests running actual po2ini commands on files"""
    convertmodule = po2ini
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--threshold=PERCENT")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy", last=True)
