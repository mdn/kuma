#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory


def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('nqo')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg."
    assert language.punctranslate(u"abc efg!") == u"abc efg߹"
    assert language.punctranslate(u"abc, efg; d?") == u"abc߸ efg؛ d؟"
    # See https://github.com/translate/translate/issues/1819
    assert language.punctranslate(u"It is called “abc”") == u"It is called ”abc“"


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('nqo')
    sentences = language.sentences(u"")
    assert sentences == []

    # this text probably does not make sense, I just copied it from Firefox
    # translation and added some punctuation marks
    sentences = language.sentences(u"ߡߍ߲ ߠߎ߬ ߦߋ߫ ߓߊ߯ߙߊ߫ ߟߊ߫ ߢߐ߲߮ ߝߍ߬ ߞߊ߬ ߓߟߐߟߐ ߟߊߞߊ߬ߣߍ߲ ߕߏ߫. ߖߊ߬ߡߊ ߣߌ߫ ߓߍ߯ ߛߊ߬ߥߏ ߘߐ߫.")
    print(sentences)
    assert sentences == [u"ߡߍ߲ ߠߎ߬ ߦߋ߫ ߓߊ߯ߙߊ߫ ߟߊ߫ ߢߐ߲߮ ߝߍ߬ ߞߊ߬ ߓߟߐߟߐ ߟߊߞߊ߬ߣߍ߲ ߕߏ߫.", u"ߖߊ߬ߡߊ ߣߌ߫ ߓߍ߯ ߛߊ߬ߥߏ ߘߐ߫."]
    sentences = language.sentences(u"ߡߍ߲ ߠߎ߬ ߦߋ߫ ߓߊ߯ߙߊ߫ ߟߊ߫ ߢߐ߲߮ ߝߍ߬ ߞߊ߬ ߓߟߐߟߐ ߟߊߞߊ߬ߣߍ߲ ߕߏ߫? ߖߊ߬ߡߊ ߣߌ߫ ߓߍ߯ ߛߊ߬ߥߏ ߘߐ߫.")
    print(sentences)
    assert sentences == [u"ߡߍ߲ ߠߎ߬ ߦߋ߫ ߓߊ߯ߙߊ߫ ߟߊ߫ ߢߐ߲߮ ߝߍ߬ ߞߊ߬ ߓߟߐߟߐ ߟߊߞߊ߬ߣߍ߲ ߕߏ߫?", u"ߖߊ߬ߡߊ ߣߌ߫ ߓߍ߯ ߛߊ߬ߥߏ ߘߐ߫."]
