#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('ko')
    # Nothing should be translated
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg."
    assert language.punctranslate(u"abc efg. hij.") == u"abc efg. hij."
    assert language.punctranslate(u"abc efg!") == u"abc efg!"
    assert language.punctranslate(u"abc efg? hij!") == u"abc efg? hij!"
    assert language.punctranslate(u"Delete file: %s?") == u"Delete file: %s?"

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('ko')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"이 연락처에 바뀐 부분이 있습니다. 바뀐 사항을 저장하시겠습니까?")
    print sentences
    assert sentences == [u"이 연락처에 바뀐 부분이 있습니다.", u"바뀐 사항을 저장하시겠습니까?"]

