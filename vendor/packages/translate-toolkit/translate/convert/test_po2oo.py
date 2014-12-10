#!/usr/bin/env python

from translate.convert import po2oo
from translate.convert import oo2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
import warnings
import os

class TestPO2OO:
    def setup_method(self, method):
        warnings.resetwarnings()

    def teardown_method(self, method):
        warnings.resetwarnings()

    def convertoo(self, posource, ootemplate, language="en-US"):
        """helper to exercise the command line function"""
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(ootemplate)
        assert po2oo.convertoo(inputfile, outputfile, templatefile, targetlanguage=language, timestamp=0)
        return outputfile.getvalue()

    def roundtripstring(self, entitystring):
        oointro, oooutro = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	en-US	', '				2002-02-02 02:02:02' + '\r\n'
        oosource = oointro + entitystring + oooutro
        ooinputfile = wStringIO.StringIO(oosource)
        ooinputfile2 = wStringIO.StringIO(oosource)
        pooutputfile = wStringIO.StringIO()
        oo2po.convertoo(ooinputfile, pooutputfile, ooinputfile2, targetlanguage='en-US')
        posource = pooutputfile.getvalue()
        poinputfile = wStringIO.StringIO(posource)
        ootemplatefile = wStringIO.StringIO(oosource)
        oooutputfile = wStringIO.StringIO()
        po2oo.convertoo(poinputfile, oooutputfile, ootemplatefile, targetlanguage="en-US")
        ooresult = oooutputfile.getvalue()
        print "original oo:\n", oosource, "po version:\n", posource, "output oo:\n", ooresult
        assert ooresult.startswith(oointro) and ooresult.endswith(oooutro)
        return ooresult[len(oointro):-len(oooutro)]

    def check_roundtrip(self, oosource):
        """Checks that the round-tripped string is the same as the original"""
        assert self.roundtripstring(oosource) == oosource

    def test_convertoo(self):
        """checks that the convertoo function is working"""
        oobase = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	%s	%s				20050924 09:13:58' + '\r\n'
        posource = '''#: numpages.src#RID_SVXPAGE_NUM_OPTIONS.STR_BULLET.string.text\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        ootemplate = oobase % ('en-US', 'Simple String')
        ooexpected = oobase % ('zu', 'Dimpled Ring')
        newoo = self.convertoo(posource, ootemplate, language="zu")
        assert newoo == ootemplate + ooexpected

    def test_pofilter(self):
        """Tests integration with pofilter"""
        #Some bad po with a few errors:
        posource = '#: sourcefile.bla#ID_NUMBER.txet.gnirts\nmsgid "<tag cow=\\"3\\">Mistake."\nmsgstr "  <etiket koei=\\"3\\">(fout) "'
        filter = po2oo.filter
        pofile = po.pofile()
        pofile.parse(posource)
        assert not filter.validelement(pofile.units[0], "dummyname.po", "exclude-all")

    def test_roundtrip_simple(self):
        """checks that simple strings make it through a oo->po->oo roundtrip"""
        self.check_roundtrip('Hello')
        self.check_roundtrip('"Hello"')
        self.check_roundtrip('"Hello Everybody"')

    def test_roundtrip_escape(self):
        """checks that escapes in strings make it through a oo->po->oo roundtrip"""
        self.check_roundtrip(r'"Simple Escape \ \n \\ \: \t \r "')
        self.check_roundtrip(r'"More escapes \\n \\t \\r \\: "')
        self.check_roundtrip(r'"More escapes \\\n \\\t \\\r \\\: "')
        self.check_roundtrip(r'"More escapes \\\\n \\\\t \\\\r \\\\: "')
        self.check_roundtrip(r'"End Line Escape \"')
        self.check_roundtrip(r'"\\rangle \\langle')
        self.check_roundtrip(r'\\\\<')
        self.check_roundtrip(r'\\\<')
        self.check_roundtrip(r'\\<')
        self.check_roundtrip(r'\<')

    def test_roundtrip_quotes(self):
        """checks that (escaped) quotes in strings make it through a oo->po->oo roundtrip"""
        self.check_roundtrip(r"""'Quote Escape "" '""")
        self.check_roundtrip(r'''"Single-Quote ' "''')
        self.check_roundtrip(r'''"Single-Quote Escape \' "''')
        self.check_roundtrip(r"""'Both Quotes "" '' '""")

    def xtest_roundtrip_spaces(self):
        # FIXME: this test fails because the resultant PO file returns as po.isempty since .isblank returns true
        # which is caused by isblankmsgtr returning True.  Its a complete mess which would mean unravelling lots
        # of yuch in pypo.  Until we have time to do that unravelling we're diabling this test.  You can reenable 
        # once we've fixed that.
        """checks that (escaped) quotes in strings make it through a oo->po->oo roundtrip"""
        self.check_roundtrip(" ")
        self.check_roundtrip(u"\u00a0")

    def test_default_timestamp(self):
        """test to ensure that we revert to the default timestamp"""
        oointro, oooutro = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	en-US	Text				', '\r\n'
        posource = '''#: numpages.src#RID_SVXPAGE_NUM_OPTIONS.STR_BULLET.string.text\nmsgid "Text"\nmsgstr "Text"\n'''
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(oointro + '20050924 09:13:58' + oooutro)
        assert po2oo.convertoo(inputfile, outputfile, templatefile, targetlanguage="en-US")
        assert outputfile.getvalue() == oointro + '2002-02-02 02:02:02' + oooutro

    def test_escape_conversion(self):
        """test to ensure that we convert escapes correctly"""
        oosource = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	en-US	Column1\tColumn2\r\n				2002-02-02 02:02:02' + '\r\n'
        posource = '''#: numpages.src#RID_SVXPAGE_NUM_OPTIONS.STR_BULLET.string.text\nmsgid "Column1\\tColumn2\\r\\n"\nmsgstr "Kolom1\\tKolom2\\r\\n"\n'''
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(oosource)
        assert po2oo.convertoo(inputfile, outputfile, templatefile, targetlanguage="af-ZA")
        assert "\tKolom1\\tKolom2\\r\\n\t" in outputfile.getvalue()

    def test_helpcontent_escapes(self):
        """test to ensure that we convert helpcontent escapes correctly"""
        # Note how this test specifically uses incorrect spacing in the 
        # translation. The extra space before 'hid' and an extra space before
        # the closing tag should not confuse us.
        oosource = r'helpcontent2	source\text\shared\3dsettings_toolbar.xhp	0	help	par_idN1056A				0	en-US	\<ahelp hid=\".\"\>The 3D-Settings toolbar controls properties of selected 3D objects.\</ahelp\>				2002-02-02 02:02:02' + '\r\n'
        posource = r'''#: 3dsettings_toolbar.xhp#par_idN1056A.help.text
msgid ""
"<ahelp hid=\".\">The 3D-Settings toolbar controls properties of selected 3D "
"ob jects.</ahelp>"
msgstr ""
"<ahelp  hid=\".\" >Zeee 3DDDD-Settings toolbar controls properties of selected 3D "
"objects.</ahelp>"
'''
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(oosource)
        assert po2oo.convertoo(inputfile, outputfile, templatefile, targetlanguage="af-ZA")
        assert r"\<ahelp  hid=\".\" \>Zeee 3DDDD-Settings toolbar controls properties of selected 3D objects.\</ahelp\>" in outputfile.getvalue()

    def test_helpcontent_escapes2(self):
        """test to ensure that we convert helpcontent escapes correctly"""
        oosource = r'helpcontent2	source\text\scalc\05\empty_cells.xhp	0	help	par_id2629474				0	en-US	A1: <empty>				2002-02-02 02:02:02' + '\r\n'
        posource = r'''#: empty_cells.xhp#par_id2629474.help.text 
msgid "A1: <empty>"
msgstr "Aa1: <empty>"
'''
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(oosource)
        assert po2oo.convertoo(inputfile, outputfile, templatefile, targetlanguage="af-ZA")
        assert r"Aa1: <empty>" in outputfile.getvalue()

class TestPO2OOCommand(test_convert.TestConvertCommand, TestPO2OO):
    """Tests running actual po2oo commands on files"""
    convertmodule = po2oo

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "--source-language=LANG")
        options = self.help_check(options, "--language=LANG")
        options = self.help_check(options, "-T, --keeptimestamp")
        options = self.help_check(options, "--nonrecursiveoutput")
        options = self.help_check(options, "--nonrecursivetemplate")
        options = self.help_check(options, "--filteraction")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy")
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--multifile=MULTIFILESTYLE", last=True)

    def merge2oo(self, oosource, posource):
        """helper that merges po translations to oo source through files"""
        outputoo = convertor.convertstore(inputpo)
        return outputoo

    def convertoo(self, posource, ootemplate, language="en-US"):
        """helper to exercise the command line function"""
        self.create_testfile(os.path.join("input", "svx", "source", "dialog.po"), posource)
        self.create_testfile("input.oo", ootemplate)
        self.run_command("input", "output.oo", template="input.oo", language=language, keeptimestamp=True)
        return self.read_testfile("output.oo")

