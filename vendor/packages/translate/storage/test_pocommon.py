#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import pocommon


def test_roundtrip_quote_plus():
    "Test that what we put in is what we get out"""
    def roundtrip_quote_plus(text, quoted):
        quote = pocommon.quote_plus(text)
        assert quote == quoted
        unquote = pocommon.unquote_plus(quoted)
        assert unquote == text
    roundtrip_quote_plus(u"abc", u"abc")
    roundtrip_quote_plus(u"key space", u"key+space")
    roundtrip_quote_plus(u"key ḓey", u"key+%E1%B8%93ey")
