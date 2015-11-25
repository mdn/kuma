#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from translate.storage import qm, test_base


class TestQtUnit(test_base.TestTranslationUnit):
    UnitClass = qm.qmunit


class TestQtFile(test_base.TestTranslationStore):
    StoreClass = qm.qmfile

    def test_parse(self):
        # self.reparse relies on __str__ to be output and then parsed
        # qm.py does not implement __str__ but returns u''
        pass

    def test_save(self):
        # QM does not implement saving
        assert pytest.raises(Exception, self.StoreClass.savefile,
                           self.StoreClass())

    def test_files(self):
        # QM does not implement saving
        assert pytest.raises(Exception, self.StoreClass.savefile,
                           self.StoreClass())

    def test_nonascii(self):
        # QM does not implement serialising
        assert pytest.raises(Exception, self.StoreClass.__str__,
                           self.StoreClass())

    def test_add(self):
        # QM does not implement serialising
        assert pytest.raises(Exception, self.StoreClass.__str__,
                           self.StoreClass())
