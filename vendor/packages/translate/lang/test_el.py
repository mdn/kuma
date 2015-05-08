#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory


def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('el')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg. hij.") == u"abc efg. hij."
    assert language.punctranslate(u"abc efg;") == u"abc efg·"
    assert language.punctranslate(u"abc efg? hij!") == u"abc efg; hij!"


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('el')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"Θέλετε να αποθηκεύσετε το παιχνίδι σας; (Θα σβησθούν οι Αυτόματες-Αποθηκεύσεις)")
    assert sentences == [u"Θέλετε να αποθηκεύσετε το παιχνίδι σας;", u"(Θα σβησθούν οι Αυτόματες-Αποθηκεύσεις)"]
    sentences = language.sentences(u"Πρώτη πρόταση. Δεύτερη πρόταση.")
    assert sentences == [u"Πρώτη πρόταση.", u"Δεύτερη πρόταση."]
    sentences = language.sentences(u"Πρώτη πρόταση. δεύτερη πρόταση.")
    assert sentences == [u"Πρώτη πρόταση. δεύτερη πρόταση."]
