#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang.team import guess_language


def test_simple():
    """test the regex, team snippet and language name snippets at a high
    level"""
    # standard regex guess
    assert guess_language(u"ab@li.org") == "ab"
    # We never suggest 'en', it's always a mistake
    assert guess_language(u"en@li.org") is None
    # We can't have a single char language code
    assert guess_language(u"C@li.org") is None
    # Testing regex postfilter
    assert guess_language(u"LL@li.org") is None

    # snippet guess based on contact info
    assert guess_language(u"assam@mm.assam-glug.org") == "as"
    # snippet guess based on a language name
    assert guess_language(u"Hawaiian") == "haw"

    # We found nothing
    assert guess_language(u"Bork bork") is None
