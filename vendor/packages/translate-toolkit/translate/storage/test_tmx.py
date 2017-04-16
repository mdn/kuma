#!/usr/bin/env python

from translate.storage import tmx
from translate.storage import test_base
from translate.misc import wStringIO

class TestTMXUnit(test_base.TestTranslationUnit):
    UnitClass = tmx.tmxunit


class TestTMXUnitFromParsedString(TestTMXUnit):
    tmxsource = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE tmx
  SYSTEM 'tmx14.dtd'>
<tmx version="1.4">
        <header adminlang="en" creationtool="Translate Toolkit - po2tmx" creationtoolversion="1.0beta" datatype="PlainText" o-tmf="UTF-8" segtype="sentence" srclang="en"/>
        <body>
                <tu>
                        <tuv xml:lang="en">
                                <seg>Test String</seg>
                        </tuv>
                </tu>
        </body>
</tmx>'''

    def setup_method(self, method):
        store = tmx.tmxfile.parsestring(self.tmxsource)
        self.unit = store.units[0]

class TestTMXfile(test_base.TestTranslationStore):
    StoreClass = tmx.tmxfile

    def tmxparse(self, tmxsource):
        """helper that parses tmx source without requiring files"""
        dummyfile = wStringIO.StringIO(tmxsource)
        print tmxsource
        tmxfile = tmx.tmxfile(dummyfile)
        return tmxfile

    def test_translate(self):
        tmxfile = tmx.tmxfile()
        assert tmxfile.translate("Anything") is None
        tmxfile.addtranslation("A string of characters", "en", "'n String karakters", "af")
        assert tmxfile.translate("A string of characters") == "'n String karakters"

    def test_addtranslation(self):
        """tests that addtranslation() stores strings correctly"""
        tmxfile = tmx.tmxfile()
        tmxfile.addtranslation("A string of characters", "en", "'n String karakters", "af")
        newfile = self.tmxparse(str(tmxfile))
        print str(tmxfile)
        assert newfile.translate("A string of characters") == "'n String karakters"

    def test_withnewlines(self):
        """test addtranslation() with newlines"""
        tmxfile = tmx.tmxfile()
        tmxfile.addtranslation("First line\nSecond line", "en", "Eerste lyn\nTweede lyn", "af")
        newfile = self.tmxparse(str(tmxfile))
        print str(tmxfile)
        assert newfile.translate("First line\nSecond line") == "Eerste lyn\nTweede lyn"

    def test_xmlentities(self):
        """Test that the xml entities '&' and '<'  are escaped correctly"""
        tmxfile = tmx.tmxfile()
        tmxfile.addtranslation("Mail & News", "en", "Nuus & pos", "af")
        tmxfile.addtranslation("Five < ten", "en", "Vyf < tien", "af")
        xmltext = str(tmxfile)
        print "The generated xml:"
        print xmltext
        assert tmxfile.translate('Mail & News') == 'Nuus & pos'
        assert xmltext.index('Mail &amp; News')
        assert xmltext.find('Mail & News') == -1
        assert tmxfile.translate('Five < ten') == 'Vyf < tien'
        assert xmltext.index('Five &lt; ten')
        assert xmltext.find('Five < ten') == -1

