#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory


def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('th')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg"
    assert language.punctranslate(u"abc efg. hij") == u"abc efg hij"


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    # We can forget to do this well without extra help.
    language = factory.getlanguage('th')
    sentences = language.sentences(u"")
    assert sentences == []
