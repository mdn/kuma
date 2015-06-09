#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.filters import autocorrect


class TestAutocorrect:

    def correct(self, msgid, msgstr, expected):
        """helper to run correct function from autocorrect module"""
        corrected = autocorrect.correct(msgid, msgstr)
        print(repr(msgid))
        print(repr(msgstr))
        print(msgid.encode('utf-8'))
        print(msgstr.encode('utf-8'))
        print((corrected or u"").encode('utf-8'))
        assert corrected == expected

    def test_empty_target(self):
        """test that we do nothing with an empty target"""
        self.correct(u"String...", u"", None)

    def test_correct_ellipsis(self):
        """test that we convert single … or ... to match source and target"""
        self.correct(u"String...", u"Translated…", u"Translated...")
        self.correct(u"String…", u"Translated...", u"Translated…")

    def test_correct_spacestart_spaceend(self):
        """test that we can correct leading and trailing space errors"""
        self.correct(u"Simple string", u"Dimpled ring  ", u"Dimpled ring")
        self.correct(u"Simple string", u"  Dimpled ring", u"Dimpled ring")
        self.correct(u"  Simple string", u"Dimpled ring", u"  Dimpled ring")
        self.correct(u"Simple string  ", u"Dimpled ring", u"Dimpled ring  ")

    def test_correct_start_capitals(self):
        """test that we can correct the starting capital"""
        self.correct(u"Simple string", u"dimpled ring", u"Dimpled ring")
        self.correct(u"simple string", u"Dimpled ring", u"dimpled ring")

    def test_correct_end_punc(self):
        """test that we can correct end punctuation"""
        self.correct(u"Simple string:", u"Dimpled ring", u"Dimpled ring:")
        #self.correct(u"Simple string: ", u"Dimpled ring", u"Dimpled ring: ")
        self.correct(u"Simple string.", u"Dimpled ring", u"Dimpled ring.")
        #self.correct(u"Simple string. ", u"Dimpled ring", u"Dimpled ring. ")
        self.correct(u"Simple string?", u"Dimpled ring", u"Dimpled ring?")

    def test_correct_combinations(self):
        """test that we can correct combinations of failures"""
        self.correct(u"Simple string:", u"Dimpled ring ", u"Dimpled ring:")
        self.correct(u"simple string ", u"Dimpled ring", u"dimpled ring ")
        self.correct(u"Simple string...", u"dimpled ring..", u"Dimpled ring...")
        self.correct(u"Simple string:", u"Dimpled ring ", u"Dimpled ring:")

    def test_nothing_to_do(self):
        """test that when nothing changes we return None"""
        self.correct(u"Some text", u"A translation", None)
