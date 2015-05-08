#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.lang import data


def test_languagematch():
    """test language comparison"""
    # Simple comparison
    assert data.languagematch("af", "af")
    assert not data.languagematch("af", "en")

    # Handle variants
    assert data.languagematch("pt", "pt_PT")
    # FIXME don't think this one is correct
    #assert not data.languagematch("sr", "sr@Latn")

    # No first language code, we just check that the other code is valid
    assert data.languagematch(None, "en")
    assert data.languagematch(None, "en_GB")
    assert data.languagematch(None, "en_GB@Latn")
    assert not data.languagematch(None, "not-a-lang-code")


def test_normalise_code():
    """test the normalisation of language codes"""
    assert data.normalize_code("af_ZA") == "af-za"
    assert data.normalize_code("xx@Latin") == "xx-latin"


def test_simplify_to_common():
    """test language code simplification"""
    assert data.simplify_to_common("af_ZA") == "af"
    assert data.simplify_to_common("pt_PT") == "pt"
    assert data.simplify_to_common("pt_BR") == "pt_BR"


def test_language_names():
    _ = data.tr_lang('en_US')
    assert _(u"Bokmål, Norwegian; Norwegian Bokmål") == u"Norwegian Bokmål"
    assert _(u"Spanish; Castillian") == u"Spanish"
    assert _(u"Mapudungun; Mapuche") == u"Mapudungun"
    assert _(u"Interlingua (International Auxiliary Language Association)") == u"Interlingua"
