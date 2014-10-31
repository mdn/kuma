#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import php
from translate.storage import test_monolingual
from translate.misc import wStringIO

def test_php_escaping_single_quote():
    """Test the helper escaping funtions for 'single quotes'

    The tests are built mostly from examples from the PHP
    U{string type definition<http://www.php.net/manual/en/language.types.string.php#language.types.string.syntax.single>}.
    """
    # Decoding - PHP -> Python
    assert php.phpdecode(r"\'") == r"'"     # To specify a literal single quote, escape it with a backslash (\).
    assert php.phpdecode(r'"') == r'"'  
    assert php.phpdecode(r"\\'") == r"\'"   # To specify a literal backslash before a single quote, or at the end of the string, double it (\\)
    assert php.phpdecode(r"\x") == r"\x"    # Note that attempting to escape any other character will print the backslash too.
    assert php.phpdecode(r'\t') == r'\t'  
    assert php.phpdecode(r'\n') == r'\n'  
    assert php.phpdecode(r"this is a simple string") == r"this is a simple string"
    assert php.phpdecode("""You can also have embedded newlines in 
strings this way as it is
okay to do""") == """You can also have embedded newlines in 
strings this way as it is
okay to do"""
    assert php.phpdecode(r"This will not expand: \n a newline") == r"This will not expand: \n a newline"
    assert php.phpdecode(r'Arnold once said: "I\'ll be back"') == r'''Arnold once said: "I'll be back"'''
    assert php.phpdecode(r'You deleted C:\\*.*?') == r"You deleted C:\*.*?"
    assert php.phpdecode(r'You deleted C:\*.*?') == r"You deleted C:\*.*?"
    assert php.phpdecode(r'\117\143\164\141\154') == r'\117\143\164\141\154'       # We don't handle Octal like " does
    assert php.phpdecode(r'\x48\x65\x78') == r'\x48\x65\x78'                       # Don't handle Hex either
    # Should implement for false interpretation of double quoted data.
    # Encoding - Python -> PHP
    assert php.phpencode(r"'") == r"\'"     # To specify a literal single quote, escape it with a backslash (\).
    assert php.phpencode(r"\'") == r"\\'"   # To specify a literal backslash before a single quote, or at the end of the string, double it (\\)
    assert php.phpencode(r'"') == r'"'
    assert php.phpencode(r"\x") == r"\x"    # Note that attempting to escape any other character will print the backslash too. 
    assert php.phpencode(r"\t") == r"\t"
    assert php.phpencode(r"\n") == r"\n"
    assert php.phpencode(r"""String with
newline""") == r"""String with
newline"""
    assert php.phpencode(r"This will not expand: \n a newline") == r"This will not expand: \n a newline"
    assert php.phpencode(r'''Arnold once said: "I'll be back"''') == r'''Arnold once said: "I\'ll be back"'''
    assert php.phpencode(r'You deleted C:\*.*?') == r"You deleted C:\*.*?"

def test_php_escaping_double_quote():
    """Test the helper escaping funtions for 'double quotes'"""
    # Decoding - PHP -> Python
    assert php.phpdecode("'", quotechar='"') == "'"         # we do nothing with single quotes
    assert php.phpdecode(r"\n", quotechar='"') == "\n"      # See table of escaped characters
    assert php.phpdecode(r"\r", quotechar='"') == "\r"      # See table of escaped characters
    assert php.phpdecode(r"\t", quotechar='"') == "\t"      # See table of escaped characters
    assert php.phpdecode(r"\v", quotechar='"') == "\v"      # See table of escaped characters
    assert php.phpdecode(r"\f", quotechar='"') == "\f"      # See table of escaped characters
    assert php.phpdecode(r"\\", quotechar='"') == "\\"      # See table of escaped characters
    #assert php.phpdecode(r"\$", quotechar='"') == "$"      # See table of escaped characters - this may cause confusion with actual variables in roundtripping
    assert php.phpdecode(r"\$", quotechar='"') == "\\$"     # Just to check that we don't unescape this
    assert php.phpdecode(r'\"', quotechar='"') == '"'       # See table of escaped characters
    assert php.phpdecode(r'\117\143\164\141\154', quotechar='"') == 'Octal'       # Octal: \[0-7]{1,3}
    assert php.phpdecode(r'\x48\x65\x78', quotechar='"') == 'Hex'                 # Hex: \x[0-9A-Fa-f]{1,2}
    assert php.phpdecode(r'\117\\c\164\141\154', quotechar='"') == 'O\ctal'  # Mixed
    # Decoding - special examples
    assert php.phpdecode(r"Don't escape me here\'s", quotechar='"') == r"Don't escape me here\'s"  # See bug #589
    assert php.phpdecode("Line1\nLine2") == "Line1\nLine2"      # Preserve newlines in multiline messages
    assert php.phpdecode("Line1\r\nLine2") == "Line1\r\nLine2"  # DOS PHP files
    # Encoding - Python -> PHP
    assert php.phpencode("'", quotechar='"') == "'"
    assert php.phpencode("\n", quotechar='"') == "\n"       # See table of escaped characters - we leave newlines unescaped so that we can try best to preserve pretty printing. See bug 588
    assert php.phpencode("\r", quotechar='"') == r"\r"      # See table of escaped characters
    assert php.phpencode("\t", quotechar='"') == r"\t"      # See table of escaped characters
    assert php.phpencode("\v", quotechar='"') == r"\v"      # See table of escaped characters
    assert php.phpencode("\f", quotechar='"') == r"\f"      # See table of escaped characters
    assert php.phpencode(r"\\", quotechar='"') == r"\\"      # See table of escaped characters
    #assert php.phpencode("\$", quotechar='"') == "$"      # See table of escaped characters - this may cause confusion with actual variables in roundtripping
    assert php.phpencode("\$", quotechar='"') == r"\$"     # Just to check that we don't unescape this
    assert php.phpencode('"', quotechar='"') == r'\"'
    assert php.phpencode(r"Don't escape me here\'s", quotechar='"') == r"Don't escape me here\'s"  # See bug #589

class TestPhpUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = php.phpunit

    def test_difficult_escapes(self):
        pass

class TestPhpFile(test_monolingual.TestMonolingualStore):
    StoreClass = php.phpfile
    
    def phpparse(self, phpsource):
        """helper that parses php source without requiring files"""
        dummyfile = wStringIO.StringIO(phpsource)
        phpfile = php.phpfile(dummyfile)
        return phpfile

    def phpregen(self, phpsource):
        """helper that converts php source to phpfile object and back"""
        return str(self.phpparse(phpsource))

    def test_simpledefinition(self):
        """checks that a simple php definition is parsed correctly"""
        phpsource = """$lang['mediaselect'] = 'Bestand selectie';"""
        phpfile = self.phpparse(phpsource)
        assert len(phpfile.units) == 1
        phpunit = phpfile.units[0]
        assert phpunit.name == "$lang['mediaselect']"
        assert phpunit.source == "Bestand selectie"

    def test_simpledefinition_source(self):
        """checks that a simple php definition can be regenerated as source"""
        phpsource = """$lang['mediaselect']='Bestand selectie';"""
        phpregen = self.phpregen(phpsource)
        assert phpsource + '\n' == phpregen

    def test_spaces_in_name(self):
        """check that spaces in the array name doesn't throw us off"""
        phpsource =  """$lang[ 'mediaselect' ] = 'Bestand selectie';"""
        phpfile = self.phpparse(phpsource)
        assert len(phpfile.units) == 1
        phpunit = phpfile.units[0]
        assert phpunit.name == "$lang['mediaselect']"
        assert phpunit.source == "Bestand selectie"

    def test_comment_blocks(self):
        """check that we don't process name value pairs in comment blocks"""
        phpsource = """/*
 * $lang[0] = "Blah";
 * $lang[1] = "Bluh";
 */
$lang[2] = "Yeah";
"""
        phpfile = self.phpparse(phpsource)
        assert len(phpfile.units) == 1
        phpunit = phpfile.units[0]
        assert phpunit.name == "$lang[2]"
        assert phpunit.source == "Yeah"

    def test_multiline(self):
        """check that we preserve newlines in a multiline message"""
        phpsource = """$lang['multiline'] = "Line1%sLine2";"""
        # Try DOS and Unix and make sure the output has the same
        for lineending in ("\n", "\r\n"):
            phpfile = self.phpparse(phpsource % lineending)
            assert len(phpfile.units) == 1
            phpunit = phpfile.units[0]
            assert phpunit.name == "$lang['multiline']"
            assert phpunit.source == "Line1%sLine2" % lineending
