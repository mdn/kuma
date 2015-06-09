#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tiki unit tests
# Author: Wil Clouser <wclouser@mozilla.com>
# Date: 2008-12-01
from translate.storage import tiki


class TestTikiUnit:

    def test_locations(self):
        unit = tiki.TikiUnit("one")
        unit.addlocation('blah')
        assert unit.getlocations() == []
        unit.addlocation('unused')
        assert unit.getlocations() == ['unused']

    def test_to_unicode(self):
        unit = tiki.TikiUnit("one")
        unit.settarget('two')
        assert unicode(unit) == '"one" => "two",\n'

        unit2 = tiki.TikiUnit("one")
        unit2.settarget('two')
        unit2.addlocation('untranslated')
        assert unicode(unit2) == '// "one" => "two",\n'


class TestTikiStore:

    def test_parse_simple(self):
        tikisource = r'"Top authors" => "Top autoren",'
        tikifile = tiki.TikiStore(tikisource)
        assert len(tikifile.units) == 1
        assert tikifile.units[0].source == "Top authors"
        assert tikifile.units[0].target == "Top autoren"

    def test_parse_encode(self):
        """Make sure these tiki special symbols come through correctly"""
        tikisource = r'"test: |\n \r \t \\ \$ \"|" => "test: |\n \r \t \\ \$ \"|",'
        tikifile = tiki.TikiStore(tikisource)
        assert tikifile.units[0].source == r"test: |\n \r \t \\ \$ \"|"
        assert tikifile.units[0].target == r"test: |\n \r \t \\ \$ \"|"

    def test_parse_locations(self):
        """This function will test to make sure the location matching is working.  It
        tests that locations are detected, the default "translated" case, and that
        "unused" lines can start with //"""
        tikisource = """
"zero_source" => "zero_target",
// ### Start of unused words
"one_source" => "one_target",
// ### end of unused words
"two_source" => "two_target",
// ### start of untranslated words
// "three_source" => "three_target",
// ### end of untranslated words
"four_source" => "four_target",
// ### start of possibly untranslated words
"five_source" => "five_target",
// ### end of possibly untranslated words
"six_source" => "six_target",
        """
        tikifile = tiki.TikiStore(tikisource)
        assert len(tikifile.units) == 7
        assert tikifile.units[0].location == ["translated"]
        assert tikifile.units[1].location == ["unused"]
        assert tikifile.units[2].location == ["translated"]
        assert tikifile.units[3].location == ["untranslated"]
        assert tikifile.units[4].location == ["translated"]
        assert tikifile.units[5].location == ["possiblyuntranslated"]
        assert tikifile.units[6].location == ["translated"]

    def test_parse_ignore_extras(self):
        """Tests that we ignore extraneous lines"""
        tikisource = """<?php
$lang = Array(
"zero_source" => "zero_target",
// ###
// this is a blank line:

"###end###"=>"###end###");
        """
        tikifile = tiki.TikiStore(tikisource)
        assert len(tikifile.units) == 1
        assert tikifile.units[0].source == "zero_source"
        assert tikifile.units[0].target == "zero_target"
