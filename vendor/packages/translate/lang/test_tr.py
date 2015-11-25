#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('tr')
    sentences = language.sentences(u"Normal case. Nothing interesting.")
    assert sentences == [u"Normal case.", u"Nothing interesting."]
    sentences = language.sentences(u"1. sayı, 2. sayı.")
    assert sentences == [u"1. sayı, 2. sayı."]
