#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('am')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg።"
    assert language.punctranslate(u"abc efg. hij.") == u"abc efg። hij።"
    assert language.punctranslate(u"abc efg, hij;") == u"abc efg፣ hij፤"
    assert language.punctranslate(u"Delete file: %s?") == u"Delete file: %s?"

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('am')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"ለምልክቱ መግቢያ የተለየ መለያ። ይህ የሚጠቅመው የታሪኩን ዝርዝር ለማስቀመጥ ነው።")
    print sentences
    assert sentences == [u"ለምልክቱ መግቢያ የተለየ መለያ።", u"ይህ የሚጠቅመው የታሪኩን ዝርዝር ለማስቀመጥ ነው።"]
