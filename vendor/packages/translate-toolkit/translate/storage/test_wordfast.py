#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import test_base
from translate.storage import wordfast as wf

class TestWFTime(object):

    def test_timestring(self):
        """Setting and getting times set using a timestring"""
        wftime = wf.WordfastTime()
        assert wftime.timestring == None
        wftime.timestring = "19710820~050000"
        assert wftime.time[:6] == (1971, 8, 20, 5, 0, 0)

    def test_time(self):
        """Setting and getting times set using time tuple"""
        wftime = wf.WordfastTime()
        assert wftime.time == None
        wftime.time = (1999, 3, 27)
        wftime.timestring = "19990327~000000"
        
class TestWFUnit(test_base.TestTranslationUnit):
    UnitClass = wf.WordfastUnit

    def test_difficult_escapes(self):
        r"""Wordfast files need to perform magic with escapes.
        
           Wordfast does not accept line breaks in its TM (even though they would be
           valid in CSV) thus we turn \\n into \n and reimplement the base class test but
           eliminate a few of the actual tests.
        """
        unit = self.unit
        specials = ['\\"', '\\ ',
                    '\\\n', '\\\t', '\\\\r', '\\\\"']
        for special in specials:
            unit.source = special
            print "unit.source:", repr(unit.source) + '|'
            print "special:", repr(special) + '|'
            assert unit.source == special

    def test_wordfast_escaping(self):
        """Check handling of &'NN; style escaping"""
        def compare(real, escaped):
            unit = self.UnitClass(real)
            print real.encode('utf-8'), unit.source.encode('utf-8')
            assert unit.source == real
            assert unit.dict['source'] == escaped
            unit.target = real
            assert unit.target == real
            assert unit.dict['target'] == escaped
        for escaped, real in wf.WF_ESCAPE_MAP[:16]: # Only common and Windows, not testing Mac
            compare(real, escaped)
        # Real world cases
        unit = self.UnitClass("Open &File. ’n Probleem.")
        assert unit.dict['source'] == "Open &'26;File. &'92;n Probleem."

    def test_newlines(self):
        """Wordfast does not like real newlines"""
        unit = self.UnitClass("One\nTwo")
        assert unit.dict['source'] == "One\\nTwo"

    def test_language_setting(self):
        """Check that we can set the target language"""
        unit = self.UnitClass("Test")
        unit.targetlang = "AF"
        assert unit.dict['target-lang'] == 'AF'

    def test_istranslated(self):
        unit = self.UnitClass()
        assert not unit.istranslated()
        unit.source = "Test"
        assert not unit.istranslated()
        unit.target = "Rest"
        assert unit.istranslated()


class TestWFFile(test_base.TestTranslationStore):
    StoreClass = wf.WordfastTMFile
