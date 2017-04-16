#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory

def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('or')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"Document loaded") == u"Document loaded"
    assert language.punctranslate(u"Document loaded.") == u"Document loaded।"
    assert language.punctranslate(u"Document loaded.\n") == u"Document loaded।\n"
    assert language.punctranslate(u"Document loaded...") == u"Document loaded..."

def test_country_code():
    """Tests that we get the correct one even if a country code is attached to
    a special code being a reserved word in Python (like 'or')."""
    language = factory.getlanguage('or-IN')
    assert language.fullname == "Oriya"

def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('or')
    sentences = language.sentences(u"")
    assert sentences == []

    sentences = language.sentences(u"ଗୋଟିଏ ଚାବିକୁ ଆଲୋକପାତ କରିବା ପାଇଁ ମାଉସ ସୂଚକକୁ ତାହା ଉପରକୁ ଘୁଞ୍ଚାନ୍ତୁ। ଚୟନ କରିବା ପାଇଁ ଗୋଟିଏ ସୁଇଚକୁ ଦବାନ୍ତୁ।")
    assert sentences == [u"ଗୋଟିଏ ଚାବିକୁ ଆଲୋକପାତ କରିବା ପାଇଁ ମାଉସ ସୂଚକକୁ ତାହା ଉପରକୁ ଘୁଞ୍ଚାନ୍ତୁ।", u"ଚୟନ କରିବା ପାଇଁ ଗୋଟିଏ ସୁଇଚକୁ ଦବାନ୍ତୁ।"]

