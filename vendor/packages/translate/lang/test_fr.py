#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory


def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('fr')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg."
    assert language.punctranslate(u"abc efg!") == u"abc efg\u00a0!"
    assert language.punctranslate(u"abc efg? hij!") == u"abc efg\u00a0? hij\u00a0!"
    assert language.punctranslate(u"Delete file: %s?") == u"Delete file\u00a0: %s\u00a0?"
    assert language.punctranslate(u'"root" is powerful') == u"«\u00a0root\u00a0» is powerful"
    assert language.punctranslate(u"'root' is powerful") == u"«\u00a0root\u00a0» is powerful"
    assert language.punctranslate(u"`root' is powerful") == u"«\u00a0root\u00a0» is powerful"
    assert language.punctranslate(u'The user "root"') == u"The user «\u00a0root\u00a0»"
    assert language.punctranslate(u"The user 'root'") == u"The user «\u00a0root\u00a0»"
    assert language.punctranslate(u"The user `root'") == u"The user «\u00a0root\u00a0»"
    assert language.punctranslate(u'The user "root"?') == u"The user «\u00a0root\u00a0»\u00a0?"
    assert language.punctranslate(u"The user 'root'?") == u"The user «\u00a0root\u00a0»\u00a0?"
    assert language.punctranslate(u"The user `root'?") == u"The user «\u00a0root\u00a0»\u00a0?"
    assert language.punctranslate(u'Watch the " mark') == u'Watch the " mark'
    assert language.punctranslate(u"Watch the ' mark") == u"Watch the ' mark"
    assert language.punctranslate(u"Watch the ` mark") == u"Watch the ` mark"
    assert language.punctranslate(u'Watch the “mark”') == u"Watch the «\u00a0mark\u00a0»"
    assert language.punctranslate(u'The <a href="info">user</a> "root"?') == u'The <a href="info">user</a> «\u00a0root\u00a0»\u00a0?'
    assert language.punctranslate(u"The <a href='info'>user</a> 'root'?") == u"The <a href='info'>user</a> «\u00a0root\u00a0»\u00a0?"
    #Broken because we test for equal number of ` and ' in the string
    #assert language.punctranslate(u"The <a href='info'>user</a> `root'?") == u"The <a href='info'>user</a> «\u00a0root\u00a0»\u00a0?"
    assert language.punctranslate(u"The <a href='http://koeie'>user</a>") == u"The <a href='http://koeie'>user</a>"

    assert language.punctranslate(u"Copying `%s' to `%s'") == u"Copying «\u00a0%s\u00a0» to «\u00a0%s\u00a0»"


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('fr')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"Normal case. Nothing interesting.")
    assert sentences == [u"Normal case.", u"Nothing interesting."]
    sentences = language.sentences(u"Is that the case ? Sounds interesting !")
    assert sentences == [u"Is that the case ?", u"Sounds interesting !"]
