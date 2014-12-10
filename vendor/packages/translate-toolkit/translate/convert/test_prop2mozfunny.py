#!/usr/bin/env python

from translate.convert import prop2mozfunny
from translate.misc import wStringIO

class TestPO2Prop:
    def merge2inc(self, incsource, posource):
        """helper that merges po translations to .inc source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        templatefile = wStringIO.StringIO(incsource)
        outputfile = wStringIO.StringIO()
        result = prop2mozfunny.po2inc(inputfile, outputfile, templatefile)
        outputinc = outputfile.getvalue()
        print outputinc
        assert result
        return outputinc

    def test_no_endlines_added(self):
        """check that we don't add newlines at the end of file"""
        posource = '''# converted from #defines file\n#: MOZ_LANG_TITLE\nmsgid "English (US)"\nmsgstr "Deutsch (DE)"\n\n'''
        inctemplate = '''#define MOZ_LANG_TITLE Deutsch (DE)\n'''
        incexpected = inctemplate
        incfile = self.merge2inc(inctemplate, posource)
        print incfile
        assert incfile == incexpected

    def test_uncomment_contributors(self):
        """check that we handle uncommenting contributors properly"""
        posource = '''# converted from #defines file
#: MOZ_LANGPACK_CONTRIBUTORS
msgid "<em:contributor>Joe Solon</em:contributor>"
msgstr "<em:contributor>Mr Fury</em:contributor>"
'''
        inctemplate = '''# #define MOZ_LANGPACK_CONTRIBUTORS <em:contributor>Joe Solon</em:contributor>\n'''
        incexpected = '''#define MOZ_LANGPACK_CONTRIBUTORS <em:contributor>Mr Fury</em:contributor>\n'''
        incfile = self.merge2inc(inctemplate, posource)
        print incfile
        assert incfile == incexpected

