#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('hy')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg։"
    assert language.punctranslate(u"abc efg. hij.") == u"abc efg։ hij։"
    assert language.punctranslate(u"abc efg!") == u"abc efg՜"
    assert language.punctranslate(u"Delete file: %s") == u"Delete file՝ %s"
    # TODO: Find out exactly how questions work

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('hy')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"Արխիվն արդեն գոյություն ունի։ Դուք ցանկանու՞մ եք կրկին գրել այն։")
    print sentences
    assert sentences == [u"Արխիվն արդեն գոյություն ունի։", u"Դուք ցանկանու՞մ եք կրկին գրել այն։"]
