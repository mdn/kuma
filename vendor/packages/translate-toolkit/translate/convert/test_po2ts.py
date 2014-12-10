#!/usr/bin/env python

from translate.convert import po2ts
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po

class TestPO2TS:
    def po2ts(self, posource):
        """helper that converts po source to ts source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2ts.po2ts()
        outputts = convertor.convertstore(inputpo)
        return outputts

    def singleelement(self, storage):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(storage.units) == 1
        return storage.units[0]

    def test_simpleunit(self):
        """checks that a simple po entry definition converts properly to a ts entry"""
        minipo = r'''#: term.cpp
msgid "Term"
msgstr "asdf"'''
        tsfile = self.po2ts(minipo)
        print tsfile
        assert "<name>term.cpp</name>" in tsfile
        assert "<source>Term</source>" in tsfile
        assert "<translation>asdf</translation>" in tsfile
        assert "<comment>" not in tsfile

    def test_fullunit(self):
        """check that an entry with various settings is converted correctly"""
        posource = '''# Translator comment
#. Automatic comment
#: location.cpp:100
msgid "Source"
msgstr "Target"
'''
        tsfile = self.po2ts(posource)
        print tsfile
        # The other section are a duplicate of test_simplentry
        # FIXME need to think about auto vs trans comments maybe in TS v1.1
        assert "<comment>Translator comment</comment>" in tsfile

    def test_fuzzyunit(self):
        """check that we handle fuzzy units correctly"""
        posource = '''#: term.cpp
#, fuzzy
msgid "Source"
msgstr "Target"'''
        tsfile = self.po2ts(posource)
        print tsfile
        assert '''<translation type="unfinished">Target</translation>''' in tsfile

    def test_obsolete(self):
        """test that we can take back obsolete messages"""
        posource = '''#. (obsolete)
#: term.cpp
msgid "Source"
msgstr "Target"'''
        tsfile = self.po2ts(posource)
        print tsfile
        assert '''<translation type="obsolete">Target</translation>''' in tsfile
        
    def test_duplicates(self):
        """test that we can handle duplicates in the same context block"""
        posource = '''#: @@@#1
msgid "English"
msgstr "a"

#: @@@#3
msgid "English"
msgstr "b"
'''
        tsfile = self.po2ts(posource)
        print tsfile
        assert tsfile.find("English") != tsfile.rfind("English")
        

class TestPO2TSCommand(test_convert.TestConvertCommand, TestPO2TS):
    """Tests running actual po2ts commands on files"""
    convertmodule = po2ts

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-c CONTEXT, --context=CONTEXT")
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE", last=True)
