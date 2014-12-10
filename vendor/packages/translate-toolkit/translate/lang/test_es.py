#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('es')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg."
    assert language.punctranslate(u"abc efg?") == u"¿abc efg?"
    assert language.punctranslate(u"abc efg!") == u"¡abc efg!"
    # We have to be a bit more gentle on the code by using capitals correctly.
    # Can we be more robust with this witout affecting sentence segmentation?
    assert language.punctranslate(u"Abc efg? Hij.") == u"¿Abc efg? Hij."
    assert language.punctranslate(u"Abc efg! Hij.") == u"¡Abc efg! Hij."
    #TODO: we should be doing better, but at the only we only support the first sentence

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('es')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"El archivo <b>%1</b> ha sido modificado. ¿Desea guardarlo?")
    print sentences
    assert sentences == [u"El archivo <b>%1</b> ha sido modificado.", u"¿Desea guardarlo?"]
