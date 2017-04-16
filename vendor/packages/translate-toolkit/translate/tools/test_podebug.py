# -*- coding: utf-8 -*-

from translate.tools import podebug
from translate.storage import base, po, xliff

PO_DOC = """
msgid "This is a %s test, hooray."
msgstr ""
"""

XLIFF_DOC = """<?xml version='1.0' encoding='utf-8'?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.1" version="1.1">
  <file original="NoName" source-language="en" datatype="plaintext">
    <body>
      <trans-unit id="office:document-content[0]/office:body[0]/office:text[0]/text:p[0]">
        <source>This <g id="0">is a</g> test <x id="1" xid="office:document-content[0]/office:body[0]/office:text[0]/text:p[0]/text:note[0]"/>, hooray.</source>
      </trans-unit>
    </body>
  </file>
</xliff>
"""

class TestPODebug:
    debug = podebug.podebug()

    def setup_method(self, method):
        self.postore = po.pofile(PO_DOC)
        self.xliffstore = xliff.xlifffile(XLIFF_DOC)

    def test_ignore_gtk(self):
        """Test operation of GTK message ignoring"""
        unit = base.TranslationUnit("default:LTR")
        assert self.debug.ignore_gtk(unit) == True

    def test_rewrite_blank(self):
        """Test the blank rewrite function"""
        assert str(self.debug.rewrite_blank(u"Test")) == u""

    def test_rewrite_en(self):
        """Test the en rewrite function"""
        assert str(self.debug.rewrite_en(u"Test")) == u"Test"

    def test_rewrite_xxx(self):
        """Test the xxx rewrite function"""
        assert str(self.debug.rewrite_xxx(u"Test")) == u"xxxTestxxx"
        assert str(self.debug.rewrite_xxx(u"Newline\n")) == u"xxxNewlinexxx\n"

    def test_rewrite_bracket(self):
        """Test the bracket rewrite function"""
        assert str(self.debug.rewrite_bracket(u"Test")) == u"[Test]"
        assert str(self.debug.rewrite_bracket(u"Newline\n")) == u"[Newline]\n"

    def test_rewrite_unicode(self):
        """Test the unicode rewrite function"""
        assert unicode(self.debug.rewrite_unicode(u"Test")) == u"Ŧḗşŧ"

    def test_rewrite_flipped(self):
        """Test the unicode rewrite function"""
        assert unicode(self.debug.rewrite_flipped(u"Test")) == u"\u202e⊥ǝsʇ"
        #alternative with reversed string and no RTL override:
        #assert unicode(self.debug.rewrite_flipped("Test")) == u"ʇsǝ⊥"

    def test_rewrite_chef(self):
        """Test the chef rewrite function

        This is not realy critical to test but a simple tests ensures
        that it stays working.
        """
        assert str(self.debug.rewrite_chef(u"Mock Swedish test you muppet")) == u"Mock Swedish test yooo mooppet"

    def test_po_variables(self):
        debug = podebug.podebug(rewritestyle='unicode')
        po_out = debug.convertstore(self.postore)

        in_unit = self.postore.units[0]
        out_unit = po_out.units[0]

        assert in_unit.source == out_unit.source
        print out_unit.target
        print str(po_out)
        rewrite_func = self.debug.rewrite_unicode
        assert out_unit.target == u"%s%%s%s" % (rewrite_func(u'This is a '), rewrite_func(u' test, hooray.'))

    def test_xliff_rewrite(self):
        debug = podebug.podebug(rewritestyle='xxx')
        xliff_out = debug.convertstore(self.xliffstore)

        in_unit = self.xliffstore.units[0]
        out_unit = xliff_out.units[0]

        assert in_unit.source == out_unit.source
        print out_unit.target
        print str(xliff_out)
        assert out_unit.target == u'xxx%sxxx' % (in_unit.source)

    def test_hash(self):
        po_docs = ("""
msgid "Test msgid 1"
msgstr "Test msgstr 1"
""",
"""
msgctxt "test context"
msgid "Test msgid 2"
msgstr "Test msgstr 2"
""",
"""
# Test comment 3
msgctxt "test context 3"
msgid "Test msgid 3"
msgstr "Test msgstr 3"
""")
        debugs = (
            podebug.podebug(format="%h "),
            podebug.podebug(format="%6h."),
            podebug.podebug(format="zzz%7h.zzz"),
            podebug.podebug(format="%f %F %b %B %d %s "),
            podebug.podebug(format="%3f %4F %5b %6B %7d %8s "),
            podebug.podebug(format="%cf %cF %cb %cB %cd %cs "),
            podebug.podebug(format="%3cf %4cF %5cb %6cB %7cd %8cs ")
            )
        results = ["85a9 Test msgstr 1", "a15d Test msgstr 2", "6398 Test msgstr 3",
                   "85a917.Test msgstr 1", "a15d71.Test msgstr 2", "639898.Test msgstr 3",
                   "zzz85a9170.zzzTest msgstr 1", "zzza15d718.zzzTest msgstr 2", "zzz639898c.zzzTest msgstr 3",
                   "fullpath/to/fakefile fullpath/to/fakefile.po fakefile fakefile.po fullpath/to full-t-fake Test msgstr 1",
                   "fullpath/to/fakefile fullpath/to/fakefile.po fakefile fakefile.po fullpath/to full-t-fake Test msgstr 2",
                   "fullpath/to/fakefile fullpath/to/fakefile.po fakefile fakefile.po fullpath/to full-t-fake Test msgstr 3",
                   "ful full fakef fakefi fullpat full-t-f Test msgstr 1",
                   "ful full fakef fakefi fullpat full-t-f Test msgstr 2",
                   "ful full fakef fakefi fullpat full-t-f Test msgstr 3",
                   "fllpth/t/fkfl fllpth/t/fkfl.p fkfl fkfl.p fllpth/t fll-t-fk Test msgstr 1",
                   "fllpth/t/fkfl fllpth/t/fkfl.p fkfl fkfl.p fllpth/t fll-t-fk Test msgstr 2",
                   "fllpth/t/fkfl fllpth/t/fkfl.p fkfl fkfl.p fllpth/t fll-t-fk Test msgstr 3",
                   "fll fllp fkfl fkfl.p fllpth/ fll-t-fk Test msgstr 1",
                   "fll fllp fkfl fkfl.p fllpth/ fll-t-fk Test msgstr 2",
                   "fll fllp fkfl fkfl.p fllpth/ fll-t-fk Test msgstr 3"]

        for debug in debugs:
            for po_doc in po_docs:
                postore = po.pofile(po_doc)
                postore.filename = "fullpath/to/fakefile.po"
                po_out = debug.convertstore(postore)
                in_unit = postore.units[0]
                out_unit = po_out.units[0]
                assert in_unit.source == out_unit.source
                assert out_unit.target == results.pop(0)
