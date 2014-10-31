#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import php2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import php

class TestPhp2PO:
    def php2po(self, phpsource, phptemplate=None):
        """helper that converts .phperties source to po source without requiring files"""
        inputfile = wStringIO.StringIO(phpsource)
        inputphp = php.phpfile(inputfile)
        convertor = php2po.php2po()
        if phptemplate:
            templatefile = wStringIO.StringIO(phptemplate)
            templatephp = php.phpfile(templatefile)
            outputpo = convertor.mergestore(templatephp, inputphp)
        else:
            outputpo = convertor.convertstore(inputphp)
        return outputpo

    def convertphp(self, phpsource):
        """call the convertphp, return the outputfile"""
        inputfile = wStringIO.StringIO(phpsource)
        outputfile = wStringIO.StringIO()
        templatefile = None
        assert php2po.convertphp(inputfile, outputfile, templatefile)
        return outputfile.getvalue()

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.units) == 2
        assert pofile.units[0].isheader()
        print pofile
        return pofile.units[1]

    def countelements(self, pofile):
        """counts the number of non-header entries"""
        assert pofile.units[0].isheader()
        print pofile
        return len(pofile.units) - 1

    def test_simpleentry(self):
        """checks that a simple php entry converts properly to a po entry"""
        phpsource = """$_LANG['simple'] = 'entry';"""
        pofile = self.php2po(phpsource)
        pounit = self.singleelement(pofile)
        assert pounit.source == "entry"
        assert pounit.target == ""

    def test_convertphp(self):
        """checks that the convertphp function is working"""
        phpsource = """$_LANG['simple'] = 'entry';"""
        posource = self.convertphp(phpsource)
        pofile = po.pofile(wStringIO.StringIO(posource))
        pounit = self.singleelement(pofile)
        assert pounit.source == "entry"
        assert pounit.target == ""

    def test_unicode(self):
        """checks that unicode entries convert properly"""
        unistring = u'Norsk bokm\u00E5l'
        phpsource = """$lang['nb'] = '%s';""" % unistring
        pofile = self.php2po(phpsource)
        pounit = self.singleelement(pofile)
        print repr(pofile.units[0].target)
        print repr(pounit.source)
        assert pounit.source == u'Norsk bokm\u00E5l'

    def test_multiline(self):
        """checks that multiline enties can be parsed"""
        phpsource = r"""$lang['5093'] = 'Unable to connect to your IMAP server. You may have exceeded the maximum number 
of connections to this server. If so, use the Advanced IMAP Server Settings dialog to 
reduce the number of cached connections.';"""
        pofile = self.php2po(phpsource)
        print repr(pofile.units[1].target)
        assert self.countelements(pofile) == 1

    def test_comments_before(self):
        """test to ensure that we take comments from .php and place them in .po"""
        phpsource = '''/* Comment */
$lang['prefPanel-smime'] = 'Security';'''
        pofile = self.php2po(phpsource)
        pounit = self.singleelement(pofile)
        assert pounit.getnotes("developer") == "/* Comment"
        # TODO write test for inline comments and check for // comments that precede an entry

    def test_emptyentry(self):
        """checks that empty definitions survives into po file"""
        phpsource = '''/* comment */\n$lang['credit'] = '';'''
        pofile = self.php2po(phpsource)
        pounit = self.singleelement(pofile)
        assert pounit.getlocations() == ["$lang['credit']"]
        assert pounit.getcontext() == "$lang['credit']"
        assert "#. /* comment" in str(pofile)
        assert pounit.source == ""

    def test_hash_comment_with_equals(self):
        """Check that a # comment with = in it doesn't confuse us. Bug 1298."""
        phpsource = '''# inside alt= stuffies\n$variable = 'stringy';'''
        pofile = self.php2po(phpsource)
        pounit = self.singleelement(pofile)
        assert pounit.getlocations() == ["$variable"]
        assert "#. # inside alt= stuffies" in str(pofile)
        assert pounit.source == "stringy"

    def test_emptyentry_translated(self):
        """checks that if we translate an empty definition it makes it into the PO"""
        phptemplate = '''$lang['credit'] = '';'''
        phpsource = '''$lang['credit'] = 'Translators Names';'''
        pofile = self.php2po(phpsource, phptemplate)
        pounit = self.singleelement(pofile)
        assert pounit.getlocations() == ["$lang['credit']"]
        assert pounit.source == ""
        assert pounit.target == "Translators Names"

    def test_newlines_in_value(self):
        """check that we can carry newlines that appear in the entry value into the PO"""
        # Single quotes - \n is not a newline
        phpsource = r'''$lang['name'] = 'value1\nvalue2';'''
        pofile = self.php2po(phpsource)
        unit = self.singleelement(pofile)
        assert unit.source == r"value1\nvalue2"
        # Double quotes - \n is a newline
        phpsource = r'''$lang['name'] = "value1\nvalue2";'''
        pofile = self.php2po(phpsource)
        unit = self.singleelement(pofile)
        assert unit.source == "value1\nvalue2"

    def test_spaces_in_name(self):
        """checks that if we have spaces in the name we create a good PO with no spaces"""
        phptemplate = '''$lang[ 'credit' ] = 'Something';'''
        phpsource = '''$lang[ 'credit' ] = ''n Ding';'''
        pofile = self.php2po(phpsource, phptemplate)
        pounit = self.singleelement(pofile)
        assert pounit.getlocations() == ["$lang['credit']"]

class TestPhp2POCommand(test_convert.TestConvertCommand, TestPhp2PO):
    """Tests running actual php2po commands on files"""
    convertmodule = php2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--duplicates=DUPLICATESTYLE", last=True)

