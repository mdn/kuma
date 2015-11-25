#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import factory


def test_punctranslate():
    """Tests that we can translate punctuation."""
    language = factory.getlanguage('ne')
    assert language.punctranslate(u"") == u""
    assert language.punctranslate(u"abc efg") == u"abc efg"
    assert language.punctranslate(u"abc efg.") == u"abc efg ।"
    assert language.punctranslate(u"(abc efg).") == u"(abc efg) ।"
    assert language.punctranslate(u"abc efg...") == u"abc efg..."
    assert language.punctranslate(u"abc efg?") == u"abc efg ?"


def test_sentences():
    """Tests basic functionality of sentence segmentation."""
    language = factory.getlanguage('ne')
    sentences = language.sentences(u"")
    assert sentences == []

    # Without spaces before the punctuation
    sentences = language.sentences(u"यसको भौगोलिक अक्षांश २६ डिग्री २२ मिनेट देखि ३० डिग्री २७ मिनेट उत्तर र ८० डिग्री ४ मिनेट देखि ८८ डिग्री १२ मिनेट पूर्वी देशान्तर सम्म फैलिएको छ। यसको कूल क्षेत्रफल १,४७,१८१ वर्ग कि.मि छ।\n")
    assert sentences == [u"यसको भौगोलिक अक्षांश २६ डिग्री २२ मिनेट देखि ३० डिग्री २७ मिनेट उत्तर र ८० डिग्री ४ मिनेट देखि ८८ डिग्री १२ मिनेट पूर्वी देशान्तर सम्म फैलिएको छ।", u"यसको कूल क्षेत्रफल १,४७,१८१ वर्ग कि.मि छ।"]
    # With spaces before the punctuation
    sentences = language.sentences(u"यसको भौगोलिक अक्षांश २६ डिग्री २२ मिनेट देखि ३० डिग्री २७ मिनेट उत्तर र ८० डिग्री ४ मिनेट देखि ८८ डिग्री १२ मिनेट पूर्वी देशान्तर सम्म फैलिएको छ । यसको कूल क्षेत्रफल १,४७,१८१ वर्ग कि.मि छ ।\n")
    assert sentences == [u"यसको भौगोलिक अक्षांश २६ डिग्री २२ मिनेट देखि ३० डिग्री २७ मिनेट उत्तर र ८० डिग्री ४ मिनेट देखि ८८ डिग्री १२ मिनेट पूर्वी देशान्तर सम्म फैलिएको छ ।", u"यसको कूल क्षेत्रफल १,४७,१८१ वर्ग कि.मि छ ।"]
