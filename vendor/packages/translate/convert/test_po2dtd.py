#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings

import pytest

from translate.convert import dtd2po, po2dtd, test_convert
from translate.misc import wStringIO
from translate.storage import dtd, po


class TestPO2DTD:

    def setup_method(self, method):
        warnings.resetwarnings()

    def teardown_method(self, method):
        warnings.resetwarnings()

    def po2dtd(self, posource, remove_untranslated=False):
        """helper that converts po source to dtd source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2dtd.po2dtd(remove_untranslated=remove_untranslated)
        outputdtd = convertor.convertstore(inputpo)
        return outputdtd

    def merge2dtd(self, dtdsource, posource):
        """helper that merges po translations to dtd source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(dtdsource)
        templatedtd = dtd.dtdfile(templatefile)
        convertor = po2dtd.redtd(templatedtd)
        outputdtd = convertor.convertstore(inputpo)
        return outputdtd

    def convertdtd(self, posource, dtdtemplate, remove_untranslated=False):
        """helper to exercise the command line function"""
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(dtdtemplate)
        assert po2dtd.convertdtd(inputfile, outputfile, templatefile,
                                 remove_untranslated=remove_untranslated)
        return outputfile.getvalue()

    def roundtripsource(self, dtdsource):
        """converts dtd source to po and back again, returning the resulting source"""
        dtdinputfile = wStringIO.StringIO(dtdsource)
        dtdinputfile2 = wStringIO.StringIO(dtdsource)
        pooutputfile = wStringIO.StringIO()
        dtd2po.convertdtd(dtdinputfile, pooutputfile, dtdinputfile2)
        posource = pooutputfile.getvalue()
        poinputfile = wStringIO.StringIO(posource)
        dtdtemplatefile = wStringIO.StringIO(dtdsource)
        dtdoutputfile = wStringIO.StringIO()
        po2dtd.convertdtd(poinputfile, dtdoutputfile, dtdtemplatefile)
        dtdresult = dtdoutputfile.getvalue()
        print_string = "Original DTD:\n%s\n\nPO version:\n%s\n\n"
        print_string = print_string + "Output DTD:\n%s\n################"
        print(print_string % (dtdsource, posource, dtdresult))
        return dtdresult

    def roundtripstring(self, entitystring):
        """Just takes the contents of a ENTITY definition (with quotes) and does a roundtrip on that"""
        dtdintro, dtdoutro = '<!ENTITY Test.RoundTrip ', '>\n'
        dtdsource = dtdintro + entitystring + dtdoutro
        dtdresult = self.roundtripsource(dtdsource)
        assert dtdresult.startswith(dtdintro) and dtdresult.endswith(dtdoutro)
        return dtdresult[len(dtdintro):-len(dtdoutro)]

    def check_roundtrip(self, dtdsource, dtdcompare=None):
        """Checks that the round-tripped string is the same as dtdcompare.

        If no dtdcompare string is provided then the round-tripped string is
        compared with the original string.

        The reason why sometimes another string is provided to compare with the
        resulting string from the roundtrip is that if the original string
        contains some characters, like " character, or escapes like &quot;,
        then when the roundtrip is performed those characters or escapes are
        escaped, rendering a round-tripped string which differs from the
        original one.
        """
        if not dtdcompare:
            dtdcompare = dtdsource
        assert self.roundtripstring(dtdsource) == dtdcompare

    def test_joinlines(self):
        """tests that po lines are joined seamlessly (bug 16)"""
        multilinepo = '''#: pref.menuPath\nmsgid ""\n"<span>Tools &gt; Options</"\n"span>"\nmsgstr ""\n'''
        dtdfile = self.po2dtd(multilinepo)
        dtdsource = str(dtdfile)
        assert "</span>" in dtdsource

    def test_escapedstr(self):
        """tests that \n in msgstr is escaped correctly in dtd"""
        multilinepo = '''#: pref.menuPath\nmsgid "Hello\\nEveryone"\nmsgstr "Good day\\nAll"\n'''
        dtdfile = self.po2dtd(multilinepo)
        dtdsource = str(dtdfile)
        assert "Good day\nAll" in dtdsource

    def test_missingaccesskey(self):
        """tests that proper warnings are given if access key is missing"""
        simplepo = '''#: simple.label
#: simple.accesskey
msgid "Simple &String"
msgstr "Dimpled Ring"
'''
        simpledtd = '''<!ENTITY simple.label "Simple String">
<!ENTITY simple.accesskey "S">'''
        warnings.simplefilter("error")
        assert pytest.raises(Warning, self.merge2dtd, simpledtd, simplepo)

    def test_accesskeycase(self):
        """tests that access keys come out with the same case as the original, regardless"""
        simplepo_template = '''#: simple.label\n#: simple.accesskey\nmsgid "%s"\nmsgstr "%s"\n'''
        simpledtd_template = '''<!ENTITY simple.label "Simple %s">\n<!ENTITY simple.accesskey "%s">'''
        possibilities = [
                #(en label, en akey, en po, af po, af label, expected af akey)
                ("Sis", "S", "&Sis", "&Sies", "Sies", "S"),
                ("Sis", "s", "Si&s", "&Sies", "Sies", "S"),
                ("Sis", "S", "&Sis", "Sie&s", "Sies", "s"),
                ("Sis", "s", "Si&s", "Sie&s", "Sies", "s"),
                # untranslated strings should have the casing of the source
                ("Sis", "S", "&Sis", "", "Sis", "S"),
                ("Sis", "s", "Si&s", "", "Sis", "s"),
                ("Suck", "S", "&Suck", "", "Suck", "S"),
                ("Suck", "s", "&Suck", "", "Suck", "s"),
                ]
        for (en_label, en_akey, po_source, po_target, target_label, target_akey) in possibilities:
            simplepo = simplepo_template % (po_source, po_target)
            simpledtd = simpledtd_template % (en_label, en_akey)
            dtdfile = self.merge2dtd(simpledtd, simplepo)
            dtdfile.makeindex()
            accel = dtd.unquotefromdtd(dtdfile.id_index["simple.accesskey"].definition)
            assert accel == target_akey

    def test_accesskey_types(self):
        """tests that we can detect the various styles of accesskey"""
        simplepo_template = '''#: simple.%s\n#: simple.%s\nmsgid "&File"\nmsgstr "F&aele"\n'''
        simpledtd_template = '''<!ENTITY simple.%s "File">\n<!ENTITY simple.%s "a">'''
        for label in ("label", "title"):
            for accesskey in ("accesskey", "accessKey", "akey"):
                simplepo = simplepo_template % (label, accesskey)
                simpledtd = simpledtd_template % (label, accesskey)
                dtdfile = self.merge2dtd(simpledtd, simplepo)
                dtdfile.makeindex()
                assert dtd.unquotefromdtd(dtdfile.id_index["simple.%s" % accesskey].definition) == "a"

    def test_ampersandfix(self):
        """tests that invalid ampersands are fixed in the dtd"""
        simplestring = '''#: simple.string\nmsgid "Simple String"\nmsgstr "Dimpled &Ring"\n'''
        dtdfile = self.po2dtd(simplestring)
        dtdsource = str(dtdfile)
        assert "Dimpled Ring" in dtdsource

        po_snippet = r'''#: searchIntegration.label
#: searchIntegration.accesskey
msgid "Allow &searchIntegration.engineName; to &search messages"
msgstr "&searchIntegration.engineName; &ileti aramasına izin ver"
'''
        dtd_snippet = r'''<!ENTITY searchIntegration.accesskey      "s">
<!ENTITY searchIntegration.label       "Allow &searchIntegration.engineName; to search messages">'''
        dtdfile = self.merge2dtd(dtd_snippet, po_snippet)
        dtdsource = str(dtdfile)
        print(dtdsource)
        assert '"&searchIntegration.engineName; ileti aramasına izin ver"' in dtdsource

    def test_accesskey_missing(self):
        """tests that missing ampersands use the source accesskey"""
        po_snippet = r'''#: key.label
#: key.accesskey
msgid "&Search"
msgstr "Ileti"
'''
        dtd_snippet = r'''<!ENTITY key.accesskey      "S">
<!ENTITY key.label       "Ileti">'''
        dtdfile = self.merge2dtd(dtd_snippet, po_snippet)
        dtdsource = str(dtdfile)
        print(dtdsource)
        assert '"Ileti"' in dtdsource
        assert '""' not in dtdsource
        assert '"S"' in dtdsource

    def test_accesskey_and_amp_case_no_accesskey(self):
        """tests that accesskey and &amp; can work together

        If missing we use the source accesskey"""
        po_snippet = r'''#: key.label
#: key.accesskey
msgid "Colour & &Light"
msgstr "Lig en Kleur"
'''
        dtd_snippet = r'''<!ENTITY key.accesskey      "L">
<!ENTITY key.label       "Colour &amp; Light">'''
        dtdfile = self.merge2dtd(dtd_snippet, po_snippet)
        dtdsource = str(dtdfile)
        print(dtdsource)
        assert '"Lig en Kleur"' in dtdsource
        assert '"L"' in dtdsource

    def test_accesskey_and_amp_case_no_amp(self):
        """tests that accesskey and &amp; can work together

        If present we use the target accesskey"""
        po_snippet = r'''#: key.label
#: key.accesskey
msgid "Colour & &Light"
msgstr "Lig en &Kleur"
'''
        dtd_snippet = r'''<!ENTITY key.accesskey      "L">
<!ENTITY key.label       "Colour &amp; Light">'''
        dtdfile = self.merge2dtd(dtd_snippet, po_snippet)
        dtdsource = str(dtdfile)
        print(dtdsource)
        assert '"Lig en Kleur"' in dtdsource
        assert '"K"' in dtdsource

    def test_accesskey_and_amp_case_both_amp_and_accesskey(self):
        """tests that accesskey and &amp; can work together

        If present both & (and) and a marker then we use the correct source
        accesskey"""
        po_snippet = r'''#: key.label
#: key.accesskey
msgid "Colour & &Light"
msgstr "Lig & &Kleur"
'''
        dtd_snippet = r'''<!ENTITY key.accesskey      "L">
<!ENTITY key.label       "Colour &amp; Light">'''
        dtdfile = self.merge2dtd(dtd_snippet, po_snippet)
        dtdsource = str(dtdfile)
        print(dtdsource)
        assert '"Lig &amp; Kleur"' in dtdsource
        assert '"K"' in dtdsource

    def test_entities_two(self):
        """test the error ouput when we find two entities"""
        simplestring = '''#: simple.string second.string\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        dtdfile = self.po2dtd(simplestring)
        dtdsource = str(dtdfile)
        assert "CONVERSION NOTE - multiple entities" in dtdsource

    def test_entities(self):
        """tests that entities are correctly idnetified in the dtd"""
        simplestring = '''#: simple.string\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        dtdfile = self.po2dtd(simplestring)
        dtdsource = str(dtdfile)
        assert dtdsource.startswith("<!ENTITY simple.string")

    def test_comments_translator(self):
        """tests for translator comments"""
        simplestring = '''# Comment1\n# Comment2\n#: simple.string\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        dtdfile = self.po2dtd(simplestring)
        dtdsource = str(dtdfile)
        assert dtdsource.startswith("<!-- Comment1 -->")

    def test_retains_hashprefix(self):
        """tests that hash prefixes in the dtd are retained"""
        hashpo = '''#: lang.version\nmsgid "__MOZILLA_LOCALE_VERSION__"\nmsgstr "__MOZILLA_LOCALE_VERSION__"\n'''
        hashdtd = '#expand <!ENTITY lang.version "__MOZILLA_LOCALE_VERSION__">\n'
        dtdfile = self.merge2dtd(hashdtd, hashpo)
        regendtd = str(dtdfile)
        assert regendtd == hashdtd

    def test_convertdtd(self):
        """checks that the convertdtd function is working"""
        posource = '''#: simple.label\n#: simple.accesskey\nmsgid "Simple &String"\nmsgstr "Dimpled &Ring"\n'''
        dtdtemplate = '''<!ENTITY simple.label "Simple String">\n<!ENTITY simple.accesskey "S">\n'''
        dtdexpected = '''<!ENTITY simple.label "Dimpled Ring">\n<!ENTITY simple.accesskey "R">\n'''
        newdtd = self.convertdtd(posource, dtdtemplate)
        print(newdtd)
        assert newdtd == dtdexpected

    def test_untranslated_with_template(self):
        """test removing of untranslated entries in redtd"""
        posource = '''#: simple.label
msgid "Simple string"
msgstr "Dimpled ring"

#: simple.label2
msgid "Simple string 2"
msgstr ""

#: simple.label3
msgid "Simple string 3"
msgstr "Simple string 3"

#: simple.label4
#, fuzzy
msgid "Simple string 4"
msgstr "simple string four"
'''
        dtdtemplate = '''<!ENTITY simple.label "Simple string">
<!ENTITY simple.label2 "Simple string 2">
<!ENTITY simple.label3 "Simple string 3">
<!ENTITY simple.label4 "Simple string 4">
'''
        dtdexpected = '''<!ENTITY simple.label "Dimpled ring">

<!ENTITY simple.label3 "Simple string 3">

'''
        newdtd = self.convertdtd(posource, dtdtemplate, remove_untranslated=True)
        print(newdtd)
        assert newdtd == dtdexpected

    def test_untranslated_without_template(self):
        """test removing of untranslated entries in po2dtd"""
        posource = '''#: simple.label
msgid "Simple string"
msgstr "Dimpled ring"

#: simple.label2
msgid "Simple string 2"
msgstr ""

#: simple.label3
msgid "Simple string 3"
msgstr "Simple string 3"

#: simple.label4
#, fuzzy
msgid "Simple string 4"
msgstr "simple string four"
'''
        dtdexpected = '''<!ENTITY simple.label "Dimpled ring">
<!ENTITY simple.label3 "Simple string 3">
'''
        newdtd = self.po2dtd(posource, remove_untranslated=True)
        print(newdtd)
        assert str(newdtd) == dtdexpected

    def test_blank_source(self):
        """test removing of untranslated entries where source is blank"""
        posource = '''#: simple.label
msgid "Simple string"
msgstr "Dimpled ring"

#: simple.label2
msgid ""
msgstr ""

#: simple.label3
msgid "Simple string 3"
msgstr "Simple string 3"
'''
        dtdtemplate = '''<!ENTITY simple.label "Simple string">
<!ENTITY simple.label2 "">
<!ENTITY simple.label3 "Simple string 3">
'''
        dtdexpected_with_template = '''<!ENTITY simple.label "Dimpled ring">
<!ENTITY simple.label2 "">
<!ENTITY simple.label3 "Simple string 3">
'''

        dtdexpected_no_template = '''<!ENTITY simple.label "Dimpled ring">
<!ENTITY simple.label3 "Simple string 3">
'''
        newdtd_with_template = self.convertdtd(posource, dtdtemplate, remove_untranslated=True)
        print(newdtd_with_template)
        assert newdtd_with_template == dtdexpected_with_template
        newdtd_no_template = self.po2dtd(posource, remove_untranslated=True)
        print(newdtd_no_template)
        assert str(newdtd_no_template) == dtdexpected_no_template

    def test_newlines_escapes(self):
        """check that we can handle a \n in the PO file"""
        posource = '''#: simple.label\n#: simple.accesskey\nmsgid "A hard coded newline.\\n"\nmsgstr "Hart gekoeerde nuwe lyne\\n"\n'''
        dtdtemplate = '<!ENTITY  simple.label "A hard coded newline.\n">\n'
        dtdexpected = '''<!ENTITY  simple.label "Hart gekoeerde nuwe lyne\n">\n'''
        dtdfile = self.merge2dtd(dtdtemplate, posource)
        print(dtdfile)
        assert str(dtdfile) == dtdexpected

    def test_roundtrip_simple(self):
        """checks that simple strings make it through a dtd->po->dtd roundtrip"""
        self.check_roundtrip('"Hello"')
        self.check_roundtrip('"Hello Everybody"')

    def test_roundtrip_escape(self):
        """checks that escapes in strings make it through a dtd->po->dtd roundtrip"""
        self.check_roundtrip(r'"Simple Escape \ \n \\ \: \t \r "')
        self.check_roundtrip(r'"End Line Escape \"')

    def test_roundtrip_quotes(self):
        """Checks that quotes make it through a DTD->PO->DTD roundtrip.

        Quotes may be escaped or not.
        """
        # NOTE: during the roundtrip, if " quote mark is present, then it is
        # converted to &quot; and the resulting string is always enclosed
        # between " characters independently of which quotation marks the
        # original string is enclosed between. Thus the string cannot be
        # compared with itself and therefore other string should be provided to
        # compare with the result.
        #
        # Thus the string cannot be compared with itself and therefore another
        # string should be provided to compare with the roundtrip result.
        self.check_roundtrip(r"""'Quote Escape "" '""",
                             r'''"Quote Escape &quot;&quot; "''')
        self.check_roundtrip(r'''"Double-Quote Escape &quot;&quot; "''')
        self.check_roundtrip(r'''"Single-Quote ' "''')
        self.check_roundtrip(r'''"Single-Quote Escape \' "''')
        # NOTE: during the roundtrip, if " quote mark is present, then ' is
        # converted to &apos; and " is converted to &quot; Also the resulting
        # string is always enclosed between " characters independently of which
        # quotation marks the original string is enclosed between. Thus the
        # string cannot be compared with itself and therefore another string
        # should be provided to compare with the result.
        #
        # Thus the string cannot be compared with itself and therefore another
        # string should be provided to compare with the roundtrip result.
        self.check_roundtrip(r"""'Both Quotes "" &apos;&apos; '""",
                             r'''"Both Quotes &quot;&quot; &apos;&apos; "''')
        self.check_roundtrip(r'''"Both Quotes &quot;&quot; &apos;&apos; "''')
        # NOTE: during the roundtrip, if &quot; is present, then ' is converted
        # to &apos; Also the resulting string is always enclosed between "
        # characters independently of which quotation marks the original string
        # is enclosed between.
        #
        # Thus the string cannot be compared with itself and therefore another
        # string should be provided to compare with the roundtrip result.
        self.check_roundtrip(r'''"Both Quotes &quot;&quot; '' "''',
                             r'''"Both Quotes &quot;&quot; &apos;&apos; "''')

    def test_roundtrip_amp(self):
        """Checks that quotes make it through a DTD->PO->DTD roundtrip.

        Quotes may be escaped or not.
        """
        self.check_roundtrip('"Colour &amp; Light"')

    def test_merging_entries_with_spaces_removed(self):
        """dtd2po removes pretty printed spaces, this tests that we can merge this back into the pretty printed dtd"""
        posource = '''#: simple.label\nmsgid "First line then "\n"next lines."\nmsgstr "Eerste lyne en dan volgende lyne."\n'''
        dtdtemplate = '<!ENTITY simple.label "First line then\n' + \
          '                                          next lines.">\n'
        dtdexpected = '<!ENTITY simple.label "Eerste lyne en dan volgende lyne.">\n'
        dtdfile = self.merge2dtd(dtdtemplate, posource)
        print(dtdfile)
        assert str(dtdfile) == dtdexpected

    def test_preserving_spaces(self):
        """ensure that we preseve spaces between entity and value. Bug 1662"""
        posource = '''#: simple.label\nmsgid "One"\nmsgstr "Een"\n'''
        dtdtemplate = '<!ENTITY     simple.label         "One">\n'
        dtdexpected = '<!ENTITY     simple.label         "Een">\n'
        dtdfile = self.merge2dtd(dtdtemplate, posource)
        print(dtdfile)
        assert str(dtdfile) == dtdexpected

    def test_preserving_spaces(self):
        """Preseve spaces after value. Bug 1662"""
        # Space between value and >
        posource = '''#: simple.label\nmsgid "One"\nmsgstr "Een"\n'''
        dtdtemplate = '<!ENTITY simple.label "One" >\n'
        dtdexpected = '<!ENTITY simple.label "Een" >\n'
        dtdfile = self.merge2dtd(dtdtemplate, posource)
        print(dtdfile)
        assert str(dtdfile) == dtdexpected
        # Space after >
        dtdtemplate = '<!ENTITY simple.label "One"> \n'
        dtdexpected = '<!ENTITY simple.label "Een"> \n'
        dtdfile = self.merge2dtd(dtdtemplate, posource)
        print(dtdfile)
        assert str(dtdfile) == dtdexpected

    def test_comments(self):
        """test that we preserve comments, bug 351"""
        posource = '''#: name\nmsgid "Text"\nmsgstr "Teks"'''
        dtdtemplate = '''<!ENTITY name "%s">\n<!-- \n\nexample -->\n'''
        dtdfile = self.merge2dtd(dtdtemplate % "Text", posource)
        print(dtdfile)
        assert str(dtdfile) == dtdtemplate % "Teks"

    def test_duplicates(self):
        """test that we convert duplicates back correctly to their respective entries."""
        posource = r'''#: bookmarksMenu.label bookmarksMenu.accesskey
msgctxt "bookmarksMenu.label bookmarksMenu.accesskey"
msgid "&Bookmarks"
msgstr "Dipu&kutshwayo1"

#: bookmarksItem.title
msgctxt "bookmarksItem.title
msgid "Bookmarks"
msgstr "Dipukutshwayo2"

#: bookmarksButton.label
msgctxt "bookmarksButton.label"
msgid "Bookmarks"
msgstr "Dipukutshwayo3"
'''
        dtdtemplate = r'''<!ENTITY bookmarksMenu.label "Bookmarks">
<!ENTITY bookmarksMenu.accesskey "B">
<!ENTITY bookmarksItem.title "Bookmarks">
<!ENTITY bookmarksButton.label "Bookmarks">
'''
        dtdexpected = r'''<!ENTITY bookmarksMenu.label "Dipukutshwayo1">
<!ENTITY bookmarksMenu.accesskey "k">
<!ENTITY bookmarksItem.title "Dipukutshwayo2">
<!ENTITY bookmarksButton.label "Dipukutshwayo3">
'''
        dtdfile = self.merge2dtd(dtdtemplate, posource)
        print(dtdfile)
        assert str(dtdfile) == dtdexpected


class TestPO2DTDCommand(test_convert.TestConvertCommand, TestPO2DTD):
    """Tests running actual po2dtd commands on files"""
    convertmodule = po2dtd
    defaultoptions = {"progress": "none"}
    # TODO: because of having 2 base classes, we need to call all their setup and teardown methods
    # (otherwise we won't reset the warnings etc)

    def setup_method(self, method):
        """call both base classes setup_methods"""
        test_convert.TestConvertCommand.setup_method(self, method)
        TestPO2DTD.setup_method(self, method)

    def teardown_method(self, method):
        """call both base classes teardown_methods"""
        test_convert.TestConvertCommand.teardown_method(self, method)
        TestPO2DTD.teardown_method(self, method)

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--threshold=PERCENT")
        options = self.help_check(options, "--removeuntranslated")
        options = self.help_check(options, "--nofuzzy", last=True)
