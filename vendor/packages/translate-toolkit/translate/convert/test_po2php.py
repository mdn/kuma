#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import po2php
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po

class TestPO2Php:
    def po2php(self, posource):
        """helper that converts po source to .php source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2php.po2php()
        outputphp = convertor.convertstore(inputpo)
        return outputphp

    def merge2php(self, phpsource, posource):
        """helper that merges po translations to .php source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(phpsource)
        #templatephp = php.phpfile(templatefile)
        convertor = po2php.rephp(templatefile)
        outputphp = convertor.convertstore(inputpo)
        print outputphp
        return outputphp

    def test_merging_simple(self):
        """check the simplest case of merging a translation"""
        posource = '''#: $lang['name']\nmsgid "value"\nmsgstr "waarde"\n'''
        phptemplate = '''$lang['name'] = 'value';\n'''
        phpexpected = '''$lang['name'] = 'waarde';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_space_preservation(self):
        """check that we preserve any spacing in php files when merging"""
        posource = '''#: $lang['name']\nmsgid "value"\nmsgstr "waarde"\n'''
        phptemplate = '''$lang['name']  =  'value';\n'''
        phpexpected = '''$lang['name']  =  'waarde';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_merging_blank_entries(self):
        """check that we can correctly merge entries that are blank in the template"""
        posource = r'''#: accesskey-accept
msgid ""
"_: accesskey-accept\n"
""
msgstr ""'''
        phptemplate = '''$lang['accesskey-accept'] = '';\n'''
        phpexpected = '''$lang['accesskey-accept'] = '';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_merging_fuzzy(self):
        """check merging a fuzzy translation"""
        posource = '''#: $lang['name']\n#, fuzzy\nmsgid "value"\nmsgstr "waarde"\n'''
        phptemplate = '''$lang['name']  =  'value';\n'''
        phpexpected = '''$lang['name']  =  'value';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_locations_with_spaces(self):
        """check that a location with spaces in php but spaces removed in PO is used correctly"""
        posource = '''#: $lang['name']\nmsgid "value"\nmsgstr "waarde"\n'''
        phptemplate = '''$lang[ 'name' ]  =  'value';\n'''
        phpexpected = '''$lang[ 'name' ]  =  'waarde';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_inline_comments(self):
        """check that we include inline comments from the template.  Bug 590"""
        posource = '''#: $lang['name']\nmsgid "value"\nmsgstr "waarde"\n'''
        phptemplate = '''$lang[ 'name' ]  =  'value'; //inline comment\n'''
        phpexpected = '''$lang[ 'name' ]  =  'waarde'; //inline comment\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_named_variables(self):
        """check that we convert correctly if using named variables."""
        posource = '''#: $dictYear
msgid "Year"
msgstr "Jaar"
'''
        phptemplate = '''$dictYear = 'Year';\n'''
        phpexpected = '''$dictYear = 'Jaar';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert phpfile == [phpexpected]

    def test_multiline(self):
        """Check that we convert multiline strings correctly.

        Bug 1296."""
        posource = r'''#: $string['upgradesure']
msgid ""
"Your Moodle files have been changed, and you are\n"
"about to automatically upgrade your server to this version:\n"
"<p><b>$a</b></p>\n"
"<p>Once you do this you can not go back again.</p>\n"
"<p>Are you sure you want to upgrade this server to this version?</p>"
msgstr ""
'''
        phptemplate = '''$string['upgradesure'] = 'Your Moodle files have been changed, and you are
about to automatically upgrade your server to this version:
<p><b>$a</b></p>
<p>Once you do this you can not go back again.</p>
<p>Are you sure you want to upgrade this server to this version?</p>';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile[0]
        assert phpfile[0] == phptemplate

    def test_hash_comment(self):
        """check that we convert # comments correctly."""
        posource = '''#: $variable
msgid "stringy"
msgstr "stringetjie"
'''
        phptemplate = '''# inside alt= stuffies\n$variable = 'stringy';\n'''
        phpexpected = '''# inside alt= stuffies\n$variable = 'stringetjie';\n'''
        phpfile = self.merge2php(phptemplate, posource)
        print phpfile
        assert "".join(phpfile) == phpexpected

#    def test_merging_propertyless_template(self):
#        """check that when merging with a template with no property values that we copy the template"""
#        posource = ""
#        proptemplate = "# A comment\n"
#        propexpected = proptemplate
#        propfile = self.merge2prop(proptemplate, posource)
#        print propfile
#        assert propfile == [propexpected]

class TestPO2PhpCommand(test_convert.TestConvertCommand, TestPO2Php):
    """Tests running actual po2php commands on files"""
    convertmodule = po2php
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy", last=True)

