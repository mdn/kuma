#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import mark

from translate.lang import common


def test_characters():
    """Test the basic characters segmentation"""
    language = common.Common
    assert language.characters(u"") == []
    assert language.characters(u"Four") == [u"F", u"o", u"u", u"r"]
    assert language.characters(u"A B") == [u"A", u" ", u"B"]
    # Spaces are compacted, source has 2 returned has only one
    assert language.characters(u"A  B") == [u"A", u" ", u"B"]


def test_words():
    """Tests basic functionality of word segmentation."""
    language = common.Common
    words = language.words(u"")
    assert words == []

    words = language.words(u"test sentence.")
    assert words == [u"test", u"sentence"]

    words = language.words(u"This is a weird test .")
    assert words == [u"This", u"is", u"a", u"weird", u"test"]

    words = language.words(u"Don't send e-mail!")
    assert words == [u"Don't", u"send", u"e-mail"]

    words = language.words(u"Don’t send e-mail!")
    assert words == [u"Don’t", u"send", u"e-mail"]


@mark.xfail("sys.version_info >= (2, 6)",
            reason="ZWS "
                   "is not considered a space in Python 2.6+. Khmer should extend "
                   "words() to include \\u200b in addition to other word breakers.")
def test_word_khmer():
    language = common.Common
    # Let's test Khmer with zero width space (\u200b)
    words = language.words(u"ផ្ដល់​យោបល់")
    print(u"ផ្ដល់​យោបល់")
    print(language.words(u"ផ្ដល់<200b>យោបល់"))
    print([u"ផ្ដល់", u"យោបល់"])
    assert words == [u"ផ្ដល់", u"យោបល់"]


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = common.Common
    # Check that we correctly handle an empty string:
    sentences = language.sentences(u"")

    sentences = language.sentences(u"This is a sentence.")
    assert sentences == [u"This is a sentence."]
    sentences = language.sentences(u"This is a sentence")
    assert sentences == [u"This is a sentence"]
    sentences = language.sentences(u"This is a sentence. Another one.")
    assert sentences == [u"This is a sentence.", u"Another one."]
    sentences = language.sentences(u"This is a sentence. Another one. Bla.")
    assert sentences == [u"This is a sentence.", u"Another one.", u"Bla."]
    sentences = language.sentences(u"This is a sentence.Not another one.")
    assert sentences == [u"This is a sentence.Not another one."]
    sentences = language.sentences(u"Exclamation! Really? No...")
    assert sentences == [u"Exclamation!", u"Really?", u"No..."]
    sentences = language.sentences(u"Four i.e. 1+3. See?")
    assert sentences == [u"Four i.e. 1+3.", u"See?"]
    sentences = language.sentences(u"Apples, bananas, etc. are nice.")
    assert sentences == [u"Apples, bananas, etc. are nice."]
    sentences = language.sentences(u"Apples, bananas, etc.\nNext part")
    assert sentences == [u"Apples, bananas, etc.", u"Next part"]
    sentences = language.sentences(u"No font for displaying text in encoding '%s' found,\nbut an alternative encoding '%s' is available.\nDo you want to use this encoding (otherwise you will have to choose another one)?")
    assert sentences == [u"No font for displaying text in encoding '%s' found,\nbut an alternative encoding '%s' is available.", u"Do you want to use this encoding (otherwise you will have to choose another one)?"]
    # Test that a newline at the end won't confuse us
    sentences = language.sentences(u"The first sentence. The second sentence.\n")
    assert sentences == [u"The first sentence.", u"The second sentence."]
    sentences = language.sentences(u"P.O. box")
    assert sentences == [u"P.O. box"]
    sentences = language.sentences(u"Doen dit d.m.v. koeie.")
    assert sentences == [u"Doen dit d.m.v. koeie."]


def test_capsstart():
    """Tests for basic sane behaviour in startcaps()."""
    language = common.Common
    assert language.capsstart("Open cow file")
    assert language.capsstart("'Open' cow file")
    assert not language.capsstart("open cow file")
    assert not language.capsstart(":")
    assert not language.capsstart("")


def test_numstart():
    """Tests for basic sane behaviour in startcaps()."""
    language = common.Common
    assert language.numstart("360 degress")
    assert language.numstart("3D file")
    assert not language.numstart("Open 360 degrees")
    assert not language.numstart(":")
    assert not language.numstart("")


def test_punctranslate():
    """Test the basic punctranslate function"""
    language = common.Common
    assert not language.punctranslate(u"A...") == u"A…"
    language.puncdict = {u"...": u"…"}
    assert language.punctranslate(u"A...") == u"A…"


def test_length_difference():
    """Test the heuristics of the length difference function"""
    # Expansion with no code
    assert common.Common.length_difference(10) == 6
    assert common.Common.length_difference(100) == 15
    assert common.Common.length_difference(300) == 35


def test_alter_length():
    """Test that we create the correct length by adding or removing characters"""
    assert common.Common.alter_length("One two three") == "One twOne two three"
