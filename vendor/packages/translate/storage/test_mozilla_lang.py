#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import mozilla_lang, test_base


class TestMozLangUnit(test_base.TestTranslationUnit):
    UnitClass = mozilla_lang.LangUnit

    def test_translate_but_same(self):
        """Mozilla allows {ok} to indicate a line that is the
        same in source and target on purpose"""
        unit = self.UnitClass("Open")
        unit.target = "Open"
        assert unit.target == "Open"
        assert str(unit).endswith(" {ok}")

    def test_untranslated(self):
        """The target is always written to files and is never blank. If it is
        truly untranslated then it won't end with '{ok}."""
        unit = self.UnitClass("Open")
        assert unit.target is None
        assert str(unit).find("Open") == 1
        assert str(unit).find("Open", 2) == 6
        assert not str(unit).endswith(" {ok}")

        unit = self.UnitClass("Closed")
        unit.target = ""
        assert unit.target == ""
        assert str(unit).find("Closed") == 1
        assert str(unit).find("Closed", 2) == 8
        assert not str(unit).endswith(" {ok}")

    def test_comments(self):
        """Comments start with #."""
        unit = self.UnitClass("One")
        unit.addnote("Hello")
        assert str(unit).find("Hello") == 2
        assert str(unit).find("# Hello") == 0


class TestMozLangFile(test_base.TestTranslationStore):
    StoreClass = mozilla_lang.LangStore

    def test_nonascii(self):
        # FIXME investigate why this doesn't pass or why we even do this
        # text with UTF-8 encoded strings
        pass

    def test_format_layout(self):
        """General test of layout of the format"""
        lang = ("# Comment\n"
                ";Source\n"
                "Target\n")
        store = self.StoreClass.parsestring(lang)
        store.mark_active = False
        unit = store.units[0]
        assert unit.source == "Source"
        assert unit.target == "Target"
        assert "Comment" in unit.getnotes()
        assert str(store) == lang

    def test_active_flag(self):
        """Test the ## active ## flag"""
        lang = ("## active ##\n"
                ";Source\n"
                "Target\n")
        store = self.StoreClass.parsestring(lang)
        assert store.is_active
        assert str(store) == lang

    def test_multiline_comments(self):
        """Ensure we can handle and preserve miltiline comments"""
        lang = ("## active ##\n"
                "# First comment\n"
                "# Second comment\n"
                "# Third comment\n"
                ";Source\n"
                "Target\n")
        store = self.StoreClass.parsestring(lang)
        assert str(store) == lang

    def test_template(self):
        """A template should have source == target, though it could be blank"""
        lang = (";Source\n"
                "Source\n")
        store = self.StoreClass.parsestring(lang)
        unit = store.units[0]
        assert unit.source == "Source"
        assert unit.target == ""
        assert str(store) == lang
        lang2 = (";Source\n"
                "\n"
                ";Source2\n")
        store2 = self.StoreClass.parsestring(lang2)
        assert store2.units[0].source == "Source"
        assert store2.units[0].target == ""
        assert store2.units[1].source == "Source2"
        assert store2.units[1].target == ""
