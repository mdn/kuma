# -*- coding: utf-8 -*-

from pytest import importorskip
importorskip("bs4")

from translate.storage import trados


def test_unescape():
    # NBSP
    assert trados.unescape(u"Ordre du jour\\~:") == u"Ordre du jour\u00a0:"
    assert trados.unescape(u"Association for Road Safety \\endash  Conference") == u"Association for Road Safety –  Conference"


def test_escape():
    # NBSP
    assert trados.escape(u"Ordre du jour\u00a0:") == u"Ordre du jour\\~:"
    assert trados.escape(u"Association for Road Safety –  Conference") == u"Association for Road Safety \\endash  Conference"

#@mark.xfail(reason="Lots to implement")
#class TestTradosTxtTmUnit(test_base.TestTranslationUnit):
#    UnitClass = trados.TradosUnit
#
#@mark.xfail(reason="Lots to implement")
#class TestTrodosTxtTmFile(test_base.TestTranslationStore):
#    StoreClass = trados.TradosTxtTmFile
