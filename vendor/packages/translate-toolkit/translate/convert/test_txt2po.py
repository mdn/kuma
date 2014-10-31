#!/usr/bin/env python

from translate.convert import txt2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import txt

class TestTxt2PO:
    def txt2po(self, txtsource, template=None):
        """helper that converts txt source to po source without requiring files"""
        inputfile = wStringIO.StringIO(txtsource)
        inputtxt = txt.TxtFile(inputfile)
        convertor = txt2po.txt2po()
        outputpo = convertor.convertstore(inputtxt)
        return outputpo

    def singleelement(self, storage):
        """checks that the pofile contains a single non-header element, and returns it"""
        print str(storage)
        assert len(storage.units) == 1
        return storage.units[0]

    def test_simple(self):
        """test the most basic txt conversion"""
        txtsource = "A simple string"
        poexpected = '''#: :1
msgid "A simple string"
msgstr ""
'''
        poresult = self.txt2po(txtsource)
        assert str(poresult.units[1]) == poexpected

    def test_miltiple_units(self):
        """test that we can handle txt with multiple units"""
        txtsource = """First unit
Still part of first unit

Second unit is a heading
------------------------

Third unit with blank after but no more units.

"""
        poresult = self.txt2po(txtsource)
        assert poresult.units[0].isheader()
        assert len(poresult.units) == 4

    def test_carriage_return(self):
        """Remove carriage returns from files in dos format."""
        txtsource = '''The rapid expansion of telecommunications infrastructure in recent years has\r
helped to bridge the digital divide to a limited extent.\r
'''

        txtexpected = '''The rapid expansion of telecommunications infrastructure in recent years has
helped to bridge the digital divide to a limited extent.'''

        poresult = self.txt2po(txtsource)
        pounit = poresult.units[1]
        assert str(pounit.getsource()) == txtexpected

class TestDoku2po:
    def doku2po(self, txtsource, template=None):
        """helper that converts dokuwiki source to po source without requiring files."""
        inputfile = wStringIO.StringIO(txtsource)
        inputtxt = txt.TxtFile(inputfile, flavour="dokuwiki")
        convertor = txt2po.txt2po()
        outputpo = convertor.convertstore(inputtxt)
        return outputpo

    def singleelement(self, storage):
        """checks that the pofile contains a single non-header element, and returns it"""
        print str(storage)
        assert len(storage.units) == 1
        return storage.units[0]

    def test_basic(self):
        """Tests that we can convert some basic things."""
        dokusource = """=====Heading=====

This is a wiki page.
"""
        poresult = self.doku2po(dokusource)
        assert poresult.units[0].isheader()
        assert len(poresult.units) == 3
        assert poresult.units[1].source == "Heading"
        assert poresult.units[2].source == "This is a wiki page."

    def test_bullets(self):
        """Tests that we can convert some basic things."""
        dokusource = """  * This is a fact. 
  * This is a fact. 
"""
        poresult = self.doku2po(dokusource)
        assert poresult.units[0].isheader()
        assert len(poresult.units) == 3
        assert poresult.units[1].source == "This is a fact."
        assert poresult.units[2].source == "This is a fact."

    def test_numbers(self):
        """Tests that we can convert some basic things."""
        dokusource = """  - This is an item. 
  - This is an item.
"""
        poresult = self.doku2po(dokusource)
        assert poresult.units[0].isheader()
        assert len(poresult.units) == 3
        assert poresult.units[1].source == "This is an item."
        assert poresult.units[2].source == "This is an item."
    
    def test_spacing(self):
        """Tests that we can convert some basic things."""
        dokusource = """ =====         Heading  ===== 
  * This is an item.
    * This is a subitem.
        * This is a tabbed item.
"""
        poresult = self.doku2po(dokusource)
        assert poresult.units[0].isheader()
        assert len(poresult.units) == 5
        assert poresult.units[1].source == "Heading"
        assert poresult.units[2].source == "This is an item."
        assert poresult.units[3].source == "This is a subitem."
        assert poresult.units[4].source == "This is a tabbed item."

class TestTxt2POCommand(test_convert.TestConvertCommand, TestTxt2PO):
    """Tests running actual txt2po commands on files"""
    convertmodule = txt2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "--duplicates")
        options = self.help_check(options, "--encoding")
        options = self.help_check(options, "--flavour", last=True)
