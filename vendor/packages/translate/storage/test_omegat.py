#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import mark

from translate.storage import omegat as ot, test_base


class TestOtUnit(test_base.TestTranslationUnit):
    UnitClass = ot.OmegaTUnit


class TestOtFile(test_base.TestTranslationStore):
    StoreClass = ot.OmegaTFile

    @mark.xfail(reason="This doesn't work, due to two store classes handling different "
                       "extensions, but factory listing it as one supported file type")
    def test_extensions(self):
        assert False
