#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('ar')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg."
    assert language.punctranslate(u"abc, efg; d?") == u"abc، efg؛ d؟"

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('ar')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"يوجد بالفعل مجلد بالإسم \"%s\". أترغب في استبداله؟")
    print sentences
    assert sentences == [u"يوجد بالفعل مجلد بالإسم \"%s\".", u"أترغب في استبداله؟"]
    # This probably doesn't make sense: it is just the above reversed, to make sure
    # we test the '؟' as an end of sentence marker.
    sentences = language.sentences(u"أترغب في استبداله؟ يوجد بالفعل مجلد بالإسم \"%s\".")
    print sentences
    assert sentences == [u"أترغب في استبداله؟", u"يوجد بالفعل مجلد بالإسم \"%s\"."]

