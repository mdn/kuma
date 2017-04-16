#!/usr/bin/env python

from translate.convert import html2po
from translate.convert import po2html
from translate.convert import test_convert
from translate.misc import wStringIO

class TestHTML2PO:
    def html2po(self, markup, includeuntagged=False, duplicatestyle="msgctxt", keepcomments=False):
        """Helper to convert html to po without a file."""
        inputfile = wStringIO.StringIO(markup)
        convertor = html2po.html2po()
        outputpo = convertor.convertfile(inputfile, "test", False, includeuntagged, duplicatestyle, keepcomments)
        return outputpo

    def po2html(self, posource, htmltemplate):
        """Helper to convert po to html without a file."""
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(htmltemplate)
        assert po2html.converthtml(inputfile, outputfile, templatefile)
        return outputfile.getvalue()

    def countunits(self, pofile, expected):
        """helper to check that we got the expected number of messages"""
        actual = len(pofile.units)
        if actual > 0:
            if pofile.units[0].isheader():
                actual = actual - 1
        print pofile
        assert actual == expected

    def compareunit(self, pofile, unitnumber, expected):
        """helper to validate a PO message"""
        if not pofile.units[0].isheader():
            unitnumber = unitnumber - 1
        print 'unit source: ' + pofile.units[unitnumber].source.encode('utf-8') + '|'
        print 'expected: ' + expected.encode('utf-8') + '|'
        assert unicode(pofile.units[unitnumber].source) == unicode(expected)

    def check_single(self, markup, itemtext):
        """checks that converting this markup produces a single element with value itemtext"""
        pofile = self.html2po(markup)
        self.countunits(pofile, 1)
        self.compareunit(pofile, 1, itemtext)

    def check_null(self, markup):
        """checks that converting this markup produces no elements"""
        pofile = self.html2po(markup)
        self.countunits(pofile, 0)

    def check_phpsnippet(self, php):
        """Given a snippet of php, put it into an HTML shell and see
        if the results are as expected"""
        self.check_single('<html><head></head><body><p><a href="'+php+'/site.html">Body text</a></p></body></html>', "Body text")
        self.check_single('<html><head></head><body><p>More things in <a href="'+php+'/site.html">Body text</a></p></body></html>', 'More things in <a href="'+php+'/site.html">Body text</a>')
        self.check_null('<html><head></head><body><p>'+php+'</p></body></html>')

    def test_htmllang(self):
        """test to ensure that we no longer use the lang attribure"""
        markup = '''<html lang="en"><head><title>My title</title></head><body></body></html>'''
        pofile = self.html2po(markup)
        self.countunits(pofile, 1)
        # Check that the first item is the <title> not <head>
        self.compareunit(pofile, 1, "My title")

    def test_title(self):
        """test that we can extract the <title> tag"""
        self.check_single("<html><head><title>My title</title></head><body></body></html>", "My title")

    def test_title_with_linebreak(self):
        """Test a linebreak in the <title> tag"""
        htmltext = '''<html>
<head>
  <title>My
title</title>
</head>
<body>
</body>
</html>
'''
        self.check_single(htmltext, "My title")

    def test_meta(self):
        """Test that we can extract certain <meta> info from <head>."""
        self.check_single('''<html><head><meta name="keywords" content="these are keywords"></head><body></body></html>''', "these are keywords")

    def test_tag_p(self):
        """test that we can extract the <p> tag"""
        self.check_single("<html><head></head><body><p>A paragraph.</p></body></html>", "A paragraph.")
        markup = "<p>First line.<br>Second line.</p>"
        pofile = self.html2po(markup)
        self.compareunit(pofile, 1, "First line.<br>Second line.")

    def test_tag_p_with_linebreak(self):
        """Test newlines within the <p> tag."""
        htmltext = '''<html>
<head>
</head>
<body>
<p>
A paragraph is a section in a piece of writing, usually highlighting a
particular point or topic. It always begins on a new line and usually
with indentation, and it consists of at least one sentence.
</p>
</body>
</html>
'''
        self.check_single(htmltext, "A paragraph is a section in a piece of writing, usually highlighting a particular point or topic. It always begins on a new line and usually with indentation, and it consists of at least one sentence.")
        markup = "<p>First\nline.<br>Second\nline.</p>"
        pofile = self.html2po(markup)
        self.compareunit(pofile, 1, "First line.<br>Second line.")

    def test_tag_div(self):
        """test that we can extract the <div> tag"""
        self.check_single("<html><head></head><body><div>A paragraph.</div></body></html>", "A paragraph.")
        markup = "<div>First line.<br>Second line.</div>"
        pofile = self.html2po(markup)
        self.compareunit(pofile, 1, "First line.<br>Second line.")

    def test_tag_div_with_linebreaks(self):
        """Test linebreaks within a <div> tag."""
        htmltext = '''<html>
<head>
</head>
<body>
<div>
A paragraph is a section in a piece of writing, usually highlighting a
particular point or topic. It always begins on a new line and usually
with indentation, and it consists of at least one sentence.
</div>
</body>
</html>
'''
        self.check_single(htmltext, "A paragraph is a section in a piece of writing, usually highlighting a particular point or topic. It always begins on a new line and usually with indentation, and it consists of at least one sentence.")
        markup = "<div>First\nline.<br>Second\nline.</div>"
        pofile = self.html2po(markup)
        self.compareunit(pofile, 1, "First line.<br>Second line.")

    def test_tag_a(self):
        """test that we can extract the <a> tag"""
        self.check_single('<html><head></head><body><p>A paragraph with <a href="http://translate.org.za/">hyperlink</a>.</p></body></html>', 'A paragraph with <a href="http://translate.org.za/">hyperlink</a>.')

    def test_tag_a_with_linebreak(self):
        """Test that we can extract the <a> tag with newlines in it."""
        htmltext = '''<html>
<head>
</head>
<body>
<p>A
paragraph
with <a
href="http://translate.org.za/">hyperlink</a>
and
newlines.</p></body></html>
'''
        self.check_single(htmltext, 'A paragraph with <a href="http://translate.org.za/">hyperlink</a> and newlines.')

    def test_tag_img(self):
        """Test that we can extract the alt attribute from the <img> tag."""
        self.check_single('''<html><head></head><body><img src="picture.png" alt="A picture"></body></html>''', "A picture")

    def test_img_empty(self):
        """Test that we can extract the alt attribute from the <img> tag."""
        htmlsource = '''<html><head></head><body><img src="images/topbar.jpg" width="750" height="80"></body></html>'''
        self.check_null(htmlsource)

    def test_tag_table_summary(self):
        """Test that we can extract the summary attribute."""
        self.check_single('''<html><head></head><body><table summary="Table summary"></table></body></html>''', "Table summary")

    def test_table_simple(self):
        """Test that we can fully extract a simple table."""
        markup = '''<html><head></head><body><table><tr><th>Heading One</th><th>Heading Two</th><tr><td>One</td><td>Two</td></tr></table></body></html>'''
        pofile = self.html2po(markup)
        self.countunits(pofile, 4)
        self.compareunit(pofile, 1, "Heading One")
        self.compareunit(pofile, 2, "Heading Two")
        self.compareunit(pofile, 3, "One")
        self.compareunit(pofile, 4, "Two")

    def test_table_complex(self):
        markup = '''<table summary="This is the summary"><caption>A caption</caption><thead><tr><th abbr="Head 1">Heading One</th><th>Heading Two</th></thead><tfoot><tr><td>Foot One</td><td>Foot Two</td></tr></tfoot><tbody><tr><td>One</td><td>Two</td></tr></tbody></table>'''
        pofile = self.html2po(markup)
        self.countunits(pofile, 9)
        self.compareunit(pofile, 1, "This is the summary")
        self.compareunit(pofile, 2, "A caption")
        self.compareunit(pofile, 3, "Head 1")
        self.compareunit(pofile, 4, "Heading One")
        self.compareunit(pofile, 5, "Heading Two")
        self.compareunit(pofile, 6, "Foot One")
        self.compareunit(pofile, 7, "Foot Two")
        self.compareunit(pofile, 8, "One")
        self.compareunit(pofile, 9, "Two")

    def test_table_empty(self):
        """Test that we ignore tables that are empty.
        
        A table is deemed empty if it has no translatable content.
        """

        self.check_null('''<html><head></head><body><table><tr><td><img src="bob.png"></td></tr></table></body></html>''')
        self.check_null('''<html><head></head><body><table><tr><td>&nbsp;</td></tr></table></body></html>''')
        self.check_null('''<html><head></head><body><table><tr><td><strong></strong></td></tr></table></body></html>''')

    def test_address(self):
        """Test to see if the address element is extracted"""
        self.check_single("<body><address>My address</address></body>", "My address")

    def test_headings(self):
        """Test to see if the h* elements are extracted"""
        markup = "<html><head></head><body><h1>Heading One</h1><h2>Heading Two</h2><h3>Heading Three</h3><h4>Heading Four</h4><h5>Heading Five</h5><h6>Heading Six</h6></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 6)
        self.compareunit(pofile, 1, "Heading One")
        self.compareunit(pofile, 2, "Heading Two")
        self.compareunit(pofile, 3, "Heading Three")
        self.compareunit(pofile, 4, "Heading Four")
        self.compareunit(pofile, 5, "Heading Five")
        self.compareunit(pofile, 6, "Heading Six")

    def test_headings_with_linebreaks(self):
        """Test to see if h* elements with newlines can be extracted"""
        markup = "<html><head></head><body><h1>Heading\nOne</h1><h2>Heading\nTwo</h2><h3>Heading\nThree</h3><h4>Heading\nFour</h4><h5>Heading\nFive</h5><h6>Heading\nSix</h6></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 6)
        self.compareunit(pofile, 1, "Heading One")
        self.compareunit(pofile, 2, "Heading Two")
        self.compareunit(pofile, 3, "Heading Three")
        self.compareunit(pofile, 4, "Heading Four")
        self.compareunit(pofile, 5, "Heading Five")
        self.compareunit(pofile, 6, "Heading Six")

    def test_dt(self):
        """Test to see if the definition list title (dt) element is extracted"""
        self.check_single("<html><head></head><body><dl><dt>Definition List Item Title</dt></dl></body></html>", "Definition List Item Title")

    def test_dd(self):
        """Test to see if the definition list description (dd) element is extracted"""
        self.check_single("<html><head></head><body><dl><dd>Definition List Item Description</dd></dl></body></html>", "Definition List Item Description")

    def test_span(self):
        """test to check that we don't double extract a span item"""
        self.check_single("<html><head></head><body><p>You are a <span>Spanish</span> sentence.</p></body></html>", "You are a <span>Spanish</span> sentence.")

    def test_ul(self):
        """Test to see if the list item <li> is exracted"""
        markup = "<html><head></head><body><ul><li>Unordered One</li><li>Unordered Two</li></ul><ol><li>Ordered One</li><li>Ordered Two</li></ol></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 4)
        self.compareunit(pofile, 1, "Unordered One")
        self.compareunit(pofile, 2, "Unordered Two")
        self.compareunit(pofile, 3, "Ordered One")
        self.compareunit(pofile, 4, "Ordered Two")

    def test_duplicates(self):
        """check that we use the default style of msgctxt to disambiguate duplicate messages"""
        markup = "<html><head></head><body><p>Duplicate</p><p>Duplicate</p></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 2)
        # FIXME change this so that we check that the msgctxt is correctly added
        self.compareunit(pofile, 1, "Duplicate")
        self.compareunit(pofile, 2, "Duplicate")

    def wtest_multiline_reflow(self):
        """check that we reflow multiline content to make it more readable for translators"""
        self.check_single('''<td valign="middle" width="96%"><font class="headingwhite">South
                  Africa</font></td>''', '''<font class="headingwhite">South Africa</font>''')

    def wtest_nested_tags(self):
        """check that we can extract items within nested tags"""
        markup = "<div><p>Extract this</p>And this</div>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 2)
        self.compareunit(pofile, 1, "Extract this")
        self.compareunit(pofile, 2, "And this")

    def test_carriage_return(self):
        """Remove carriage returns from files in dos format."""
        htmlsource = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\r
<html><!-- InstanceBegin template="/Templates/masterpage.dwt" codeOutsideHTMLIsLocked="false" -->\r
<head>\r
<!-- InstanceBeginEditable name="doctitle" -->\r
<link href="fmfi.css" rel="stylesheet" type="text/css">\r
</head>\r
\r
<body>\r
<p>The rapid expansion of telecommunications infrastructure in recent\r
years has helped to bridge the digital divide to a limited extent.</p> \r
</body>\r
<!-- InstanceEnd --></html>\r
'''

        self.check_single(htmlsource, 'The rapid expansion of telecommunications infrastructure in recent years has helped to bridge the digital divide to a limited extent.')

    def test_encoding_latin1(self):
        """Convert HTML input in iso-8859-1 correctly to unicode."""
        htmlsource = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html><!-- InstanceBegin template="/Templates/masterpage.dwt" codeOutsideHTMLIsLocked="false" -->
<head>
<!-- InstanceBeginEditable name="doctitle" -->
<title>FMFI - South Africa - CSIR Openphone - Overview</title>
<!-- InstanceEndEditable -->
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<meta name="keywords" content="fmfi, first mile, first inch, wireless, rural development, access devices, mobile devices, wifi, connectivity, rural connectivty, ict, low cost, cheap, digital divide, csir, idrc, community">

<!-- InstanceBeginEditable name="head" -->
<!-- InstanceEndEditable -->
<link href="../../../fmfi.css" rel="stylesheet" type="text/css">
</head>

<body>
<p>We aim to please \x96 will you aim too, please?</p>
<p>South Africa\x92s language diversity can be challenging.</p>
</body>
</html>
'''
        pofile = self.html2po(htmlsource)

        self.countunits(pofile, 4)
        self.compareunit(pofile, 3, u'We aim to please \x96 will you aim too, please?')
        self.compareunit(pofile, 4, u'South Africa\x92s language diversity can be challenging.')

    def test_strip_html(self):
        """Ensure that unnecessary html is stripped from the resulting unit."""

        htmlsource = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>FMFI - Contact</title>
</head>
<body>
<table width="100%"  border="0" cellpadding="0" cellspacing="0">
  <tr align="left" valign="top">
    <td width="150" height="556"> 
      <table width="157" height="100%" border="0" cellspacing="0" id="leftmenubg-color">
      <tr>
          <td align="left" valign="top" height="555"> 
            <table width="100%" border="0" cellspacing="0" cellpadding="2">
              <tr align="left" valign="top" bgcolor="#660000"> 
                <td width="4%"><strong></strong></td>
                <td width="96%"><strong><font class="headingwhite">Projects</font></strong></td>
              </tr>
              <tr align="left" valign="top"> 
                <td valign="middle" width="4%"><img src="images/arrow.gif" width="8" height="8"></td>
                <td width="96%"><a href="index.html">Home Page</a></td>
              </tr>
            </table>
          </td>
      </tr>
    </table></td>
</table>
</body>
</html>
'''
        pofile = self.html2po(htmlsource)
        self.countunits(pofile, 3)
        self.compareunit(pofile, 2, u'Projects')
        self.compareunit(pofile, 3, u'Home Page')

        # Translate and convert back:
        pofile.units[2].target = 'Projekte'
        pofile.units[3].target = 'Tuisblad'
        htmlresult = self.po2html(str(pofile), htmlsource).replace('\n', ' ').replace('= "', '="').replace('> <', '><')
        snippet = '<td width="96%"><strong><font class="headingwhite">Projekte</font></strong></td>'
        assert snippet in htmlresult
        snippet = '<td width="96%"><a href="index.html">Tuisblad</a></td>'
        assert snippet in htmlresult

    def test_php(self):
        """Test that PHP snippets don't interfere"""

        # A simple string 
        self.check_phpsnippet('''<?=$phpvariable?>''')

        # Contains HTML tag charcters (< and >)
        self.check_phpsnippet('''<?=($a < $b ? $foo : ($b > c ? $bar : $cat))?>''')

        # Make sure basically any symbol can be handled
        self.check_phpsnippet(''' <? asdfghjkl qwertyuiop 1234567890!@#$%^&*()-=_+[]\{}|;':",./<>? ?> ''')

    def test_multiple_php(self):
        """Test multiple PHP snippets in a string to make sure they get restored properly"""
        php1 = '''<?=$phpvariable?>''' 
        php2 = '''<?=($a < $b ? $foo : ($b > c ? $bar : $cat))?>'''
        php3 = '''<? asdfghjklqwertyuiop1234567890!@#$%^&*()-=_+[]\{}|;':",./<>? ?>'''

        # Put 3 different strings into an html string
        innertext = '<a href="'+php1+'/site.html">Body text</a> and some '+php2+' more text '+php2+php3
        htmlsource = '<html><head></head><body><p>'+innertext+'</p></body></html>'
        self.check_single(htmlsource, innertext)

    def test_php_multiline(self):

        # A multi-line php string to test
        php1 = '''<? abc
def
ghi ?>'''

        # Scatter the php strings throughout the file, and show what the translation should be
        innertext = '<a href="'+php1+'/site.html">Body text</a> and some '+php1+' more text '+php1+php1
        innertrans = '<a href="'+php1+'/site.html">Texte de corps</a> et encore de '+php1+' plus de texte '+php1+php1

        htmlsource = '<html><head></head><body><p>'+innertext+'</p></body></html>' # Current html file
        transsource = '<html><head></head><body><p>'+innertrans+'</p></body></html>' # Expected translation

        pofile = self.html2po(htmlsource)
        pofile.units[1].target = innertrans # Register the translation in the PO file
        htmlresult = self.po2html(pofile, htmlsource)
        assert htmlresult == transsource

    def test_comments(self):
        """Test that HTML comments are converted to translator notes in output"""
        pofile = self.html2po('<!-- comment outside block --><p><!-- a comment -->A paragraph<!-- with another comment -->.</p>', keepcomments=True)
        self.compareunit(pofile, 1, 'A paragraph.')
        notes = pofile.getunits()[0].getnotes()
        assert unicode(notes) == ' a comment \n with another comment '

class TestHTML2POCommand(test_convert.TestConvertCommand, TestHTML2PO):
    """Tests running actual html2po commands on files"""
    convertmodule = html2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "--duplicates=DUPLICATESTYLE")
        options = self.help_check(options, "--keepcomments")
        options = self.help_check(options, "-u, --untagged", last=True)
