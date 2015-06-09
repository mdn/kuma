#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import importorskip

from translate.convert import po2sub, test_convert
from translate.misc import wStringIO
from translate.storage import po


# Technically subtitles can also use an older gaupol
importorskip("aeidon")


class TestPO2Sub:

    def po2sub(self, posource):
        """helper that converts po source to subtitle source without requiring
        files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2sub.resub()
        outputsub = convertor.convertstore(inputpo)
        return outputsub

    def merge2sub(self, subsource, posource):
        """helper that merges po translations to subtitle source without
        requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(subsource)
        convertor = po2sub.resub(templatefile, inputpo)
        outputsub = convertor.convertstore()
        print(outputsub)
        return outputsub

    def test_subrip(self):
        """test SubRip or .srt files."""
        posource = u'''#: 00:00:20.000-->00:00:24.400
msgid "Altocumulus clouds occur between six thousand"
msgstr "Blah blah blah blah"

#: 00:00:24.600-->00:00:27.800
msgid "and twenty thousand feet above ground level."
msgstr "Koei koei koei koei"
'''
        subtemplate = '''1
00:00:20,000 --> 00:00:24,400
Altocumulus clouds occur between six thousand

2
00:00:24,600 --> 00:00:27,800
and twenty thousand feet above ground level.
'''
        subexpected = '''1
00:00:20,000 --> 00:00:24,400
Blah blah blah blah

2
00:00:24,600 --> 00:00:27,800
Koei koei koei koei
'''
        subfile = self.merge2sub(subtemplate, posource)
        print(subexpected)
        assert subfile == subexpected


class TestPO2SubCommand(test_convert.TestConvertCommand, TestPO2Sub):
    """Tests running actual po2sub commands on files"""
    convertmodule = po2sub
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--threshold=PERCENT")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy", last=True)
