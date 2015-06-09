#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import catkeys, test_base


class TestCatkeysUnit(test_base.TestTranslationUnit):
    UnitClass = catkeys.CatkeysUnit

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
            print("unit.source:", repr(unit.source) + '|')
            print("special:", repr(special) + '|')
            assert unit.source == special

    def test_newlines(self):
        """Wordfast does not like real newlines"""
        unit = self.UnitClass("One\nTwo")
        assert unit.dict['source'] == "One\\nTwo"

    def test_istranslated(self):
        unit = self.UnitClass()
        assert not unit.istranslated()
        unit.source = "Test"
        assert not unit.istranslated()
        unit.target = "Rest"
        assert unit.istranslated()

    def test_note_sanity(self):
        """Override test, since the format doesn't support notes."""
        pass


class TestCatkeysFile(test_base.TestTranslationStore):
    StoreClass = catkeys.CatkeysFile
