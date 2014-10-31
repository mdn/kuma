#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('zh')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg。"
    assert language.punctranslate(u"(abc efg).") == u"(abc efg)。"
    assert language.punctranslate(u"(abc efg). hijk") == u"(abc efg)。hijk"
    assert language.punctranslate(u".") == u"。"
    assert language.punctranslate(u"abc efg...") == u"abc efg..."

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('zh')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"這個用戶名稱已經存在。現在會寄一封信給已登記的電郵地址。\n")
    assert sentences == [u"這個用戶名稱已經存在。", u"現在會寄一封信給已登記的電郵地址。"]

