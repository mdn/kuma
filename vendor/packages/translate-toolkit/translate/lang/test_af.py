#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('af')
    sentences = language.sentences(u"Normal case. Nothing interesting.")
    assert sentences == [u"Normal case.", "Nothing interesting."]
    sentences = language.sentences(u"Wat? 'n Fout?")
    assert sentences == [u"Wat?", "'n Fout?"]
    sentences = language.sentences(u"Dit sal a.g.v. 'n fout gebeur.")
    assert sentences == [u"Dit sal a.g.v. 'n fout gebeur."]

def test_capsstart():
    """Tests that the indefinite article ('n) doesn't confuse startcaps()."""
    language = factory.getlanguage('af')
    assert not language.capsstart("")
    assert language.capsstart("Koeie kraam koeie")
    assert language.capsstart("'Koeie' kraam koeie")
    assert not language.capsstart("koeie kraam koeie")
    assert language.capsstart("\n\nKoeie kraam koeie")
    assert language.capsstart("'n Koei kraam koeie")
    assert language.capsstart("'n 'Koei' kraam koeie")
    assert not language.capsstart("'n koei kraam koeie")
    assert language.capsstart("\n\n'n Koei kraam koeie")

