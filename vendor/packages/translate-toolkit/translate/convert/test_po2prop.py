#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import po2prop
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po

class TestPO2Prop:
    def po2prop(self, posource):
        """helper that converts po source to .properties source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2prop.po2prop()
        outputprop = convertor.convertstore(inputpo)
        return outputprop

    def merge2prop(self, propsource, posource, personality="java"):
        """helper that merges po translations to .properties source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(propsource)
        #templateprop = properties.propfile(templatefile)
        convertor = po2prop.reprop(templatefile)
        outputprop = convertor.convertstore(inputpo, personality=personality)
        print outputprop
        return outputprop

    def test_merging_simple(self):
        """check the simplest case of merging a translation"""
        posource = '''#: prop\nmsgid "value"\nmsgstr "waarde"\n'''
        proptemplate = '''prop=value\n'''
        propexpected = '''prop=waarde\n'''
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpected]

    def test_hard_newlines_preserved(self):
        """check that we preserver hard coded newlines at the start and end of sentence"""
        posource = '''#: prop\nmsgid "\\nvalue\\n\\n"\nmsgstr "\\nwaarde\\n\\n"\n'''
        proptemplate = '''prop=\\nvalue\\n\\n\n'''
        propexpected = '''prop=\\nwaarde\\n\\n\n'''
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpected]

    def test_space_preservation(self):
        """check that we preserve any spacing in properties files when merging"""
        posource = '''#: prop\nmsgid "value"\nmsgstr "waarde"\n'''
        proptemplate = '''prop  =  value\n'''
        propexpected = '''prop  =  waarde\n'''
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpected]

    def test_merging_blank_entries(self):
        """check that we can correctly merge entries that are blank in the template"""
        posource = r'''#: accesskey-accept
msgid ""
"_: accesskey-accept\n"
""
msgstr ""'''
        proptemplate = 'accesskey-accept=\n'
        propexpected = 'accesskey-accept=\n'
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpected]

    def test_merging_fuzzy(self):
        """check merging a fuzzy translation"""
        posource = '''#: prop\n#, fuzzy\nmsgid "value"\nmsgstr "waarde"\n'''
        proptemplate = '''prop=value\n'''
        propexpected = '''prop=value\n'''
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpected]

    def test_merging_propertyless_template(self):
        """check that when merging with a template with no property values that we copy the template"""
        posource = ""
        proptemplate = "# A comment\n"
        propexpected = proptemplate
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpected]

    def test_personalities(self):
        """test that we output correctly for Java and Mozilla style property files.  Mozilla uses Unicode, while Java uses escaped Unicode"""
        posource = '''#: prop\nmsgid "value"\nmsgstr "ṽḁḽṻḝ"\n'''
        proptemplate = '''prop  =  value\n'''
        propexpectedjava = '''prop  =  \\u1E7D\\u1E01\\u1E3D\\u1E7B\\u1E1D\n'''
        propfile = self.merge2prop(proptemplate, posource)
        print propfile
        assert propfile == [propexpectedjava]
        propexpectedmozilla = '''prop  =  ṽḁḽṻḝ\n'''
        propfile = self.merge2prop(proptemplate, posource, personality="mozilla")
        print propfile
        assert propfile == [propexpectedmozilla]
        propexpectedskype = '''prop  =  ṽḁḽṻḝ\n'''
        propfile = self.merge2prop(proptemplate, posource, personality="skype")
        print propfile
        assert propfile == [propexpectedskype]

class TestPO2PropCommand(test_convert.TestConvertCommand, TestPO2Prop):
    """Tests running actual po2prop commands on files"""
    convertmodule = po2prop
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--personality=TYPE")
        options = self.help_check(options, "--nofuzzy", last=True)

