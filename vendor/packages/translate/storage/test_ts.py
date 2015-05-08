#!/usr/bin/env python

from translate.storage import ts


class TestTS:

    def test_construct(self):
        tsfile = ts.QtTsParser()
        tsfile.addtranslation("ryan", "Bread", "Brood", "Wit", createifmissing=True)
