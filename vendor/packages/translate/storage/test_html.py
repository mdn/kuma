#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Tests for the HTML classes"""

from pytest import mark, raises

from translate.storage import base, html


def test_guess_encoding():
    """Read an encoding header to guess the encoding correctly"""
    h = html.htmlfile()
    assert h.guess_encoding('''<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=UTF-8">''') == "UTF-8"
    assert h.guess_encoding('''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd"><html><head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1"><!-- base href="http://home.online.no/~rut-aane/linux.html" --><link rel="shortcut icon" href="http://home.online.no/~rut-aane/peng16x16a.gif"><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><meta name="Description" content="Linux newbie stuff and a little about Watching TV under Linux"><meta name="MSSmartTagsPreventParsing" content="TRUE"><meta name="GENERATOR" content="Mozilla/4.7 [en] (X11; I; Linux 2.2.5-15 i586) [Netscape]"><title>Some Linux for beginners</title><style type="text/css">''') == "iso-8859-1"


def test_strip_html():
    assert html.strip_html("<a>Something</a>") == "Something"
    assert html.strip_html("You are <a>Something</a>") == "You are <a>Something</a>"
    assert html.strip_html("<b>You</b> are <a>Something</a>") == "<b>You</b> are <a>Something</a>"
    assert html.strip_html('<strong><font class="headingwhite">Projects</font></strong>') == "Projects"
    assert html.strip_html("<strong>Something</strong> else.") == "<strong>Something</strong> else."
    assert html.strip_html("<h1><strong>Something</strong> else.</h1>") == "<strong>Something</strong> else."
    assert html.strip_html('<h1 id="moral"><strong>We believe</strong> that the internet should be public, open and accessible.</h1>') == "<strong>We believe</strong> that the internet should be public, open and accessible."
    #assert html.strip_html('<h3><a href="http://www.firefox.com/" class="producttitle"><img src="../images/product-firefox-50.png" width="50" height="50" alt="" class="featured" style="display: block; margin-bottom: 30px;" /><strong>Firefox for Desktop</strong></a></h3>') == 'Firefox for Desktop'


def test_strip_html_with_pi():
    h = html.htmlfile()
    assert html.strip_html(h.pi_escape('<a href="<?$var?>">Something</a>')) == "Something"
    assert html.strip_html(h.pi_escape('<a href="<?=($a < $b ? $foo : ($b > c ? $bar : $cat))?>">Something</a>')) == "Something"


def test_normalize_html():
    assert html.normalize_html("<p>Simple  double  spaced</p>") == "<p>Simple double spaced</p>"


def test_pi_escaping():
    h = html.htmlfile()
    assert h.pi_escape('<a href="<?=($a < $b ? $foo : ($b > c ? $bar : $cat))?>">') == '<a href="<?=($a %lt; $b ? $foo : ($b %gt; c ? $bar : $cat))?>">'


class TestHTMLParsing:

    h = html.htmlfile

    def test_mismatched_tags(self):
        assert raises(base.ParseError, self.h.parsestring, "<h3><p>Some text<p></h3>")
        # First <tr> is not closed
        assert raises(base.ParseError, self.h.parsestring, "<html><head></head><body><table><tr><th>Heading One</th><th>Heading Two</th><tr><td>One</td><td>Two</td></tr></table></body></html>")
        # <tr> is not closed in <thead>
        assert raises(base.ParseError, self.h.parsestring, """<table summary="This is the summary"><caption>A caption</caption><thead><tr><th abbr="Head 1">Heading One</th><th>Heading Two</th></thead><tfoot><tr><td>Foot One</td><td>Foot Two</td></tr></tfoot><tbody><tr><td>One</td><td>Two</td></tr></tbody></table>""")

    def test_self_closing_tags(self):
        h = html.htmlfile()
        store = h.parsestring("<h3>Some text <img><br><img></h3>")
        assert len(store.units) == 1

    @mark.xfail(reason="Not implemented")
    def test_escaping_script_and_pre(self):
        """<script> and <pre> can contain < and > and these should not be
        interpretted as tags"""
        h = html.htmlfile()
        store = h.parsestring("<p>We are here</p><script>Some </tag>like data<script></p>")
        print(store.units[0].source)
        assert len(store.units) == 1


class TestHTMLExtraction(object):

    h = html.htmlfile

    def test_extraction_tag_figcaption(self):
        """Check that we can extract figcaption"""
        h = html.htmlfile()
        # Example form http://www.w3schools.com/tags/tag_figcaption.asp
        store = h.parsestring("""
               <figure>
                   <img src="img_pulpit.jpg" alt="The Pulpit Rock" width="304" height="228">
                   <figcaption>Fig1. - A view of the pulpit rock in Norway.</figcaption>
               </figure>""")
        print(store.units[0].source)
        assert len(store.units) == 2
        assert store.units[0].source == "The Pulpit Rock"
        assert store.units[1].source == "Fig1. - A view of the pulpit rock in Norway."

    def test_extraction_tag_caption_td_th(self):
        """Check that we can extract table related translatable: th, td and caption"""
        h = html.htmlfile()
        # Example form http://www.w3schools.com/tags/tag_caption.asp
        store = h.parsestring("""
            <table>
                <caption>Monthly savings</caption>
                <tr>
                    <th>Month</th>
                    <th>Savings</th>
                </tr>
                <tr>
                    <td>January</td>
                    <td>$100</td>
                </tr>
            </table>""")
        print(store.units[0].source)
        assert len(store.units) == 5
        assert store.units[0].source == "Monthly savings"
        assert store.units[1].source == "Month"
        assert store.units[2].source == "Savings"
        assert store.units[3].source == "January"
        assert store.units[4].source == "$100"

    def test_extraction_attr_alt(self):
        """Check that we can extract title attribute"""
        h = html.htmlfile()
        # Example from http://www.netmechanic.com/news/vol6/html_no1.htm
        store = h.parsestring("""
            <img src="cafeteria.jpg" height="200" width="200" alt="UAHC campers enjoy a meal in the camp cafeteria">
        """)
        assert len(store.units) == 1
        assert store.units[0].source == "UAHC campers enjoy a meal in the camp cafeteria"


    def test_extraction_attr_title(self):
        """Check that we can extract title attribute"""
        h = html.htmlfile()

        # Example form http://www.w3schools.com/tags/att_global_title.asp
        store = h.parsestring("""
            <p><abbr title="World Health Organization">WHO</abbr> was founded in 1948.</p>
            <p title="Free Web tutorials">W3Schools.com</p>""")
        print(store.units[0].source)
        assert len(store.units) == 4
        assert store.units[0].source == "World Health Organization"
        # FIXME this is not ideal we need to either drop title= as we've
        # extracted it already or not extract it earlier
        assert store.units[1].source == '<abbr title="World Health Organization">WHO</abbr> was founded in 1948.'
        assert store.units[2].source == "Free Web tutorials"
        assert store.units[3].source == "W3Schools.com"

        # Example from http://www.netmechanic.com/news/vol6/html_no1.htm
        store = h.parsestring("""
            <table width="100" border="2" title="Henry Jacobs Camp summer 2003 schedule">
        """)
        assert len(store.units) == 1
        assert store.units[0].source == "Henry Jacobs Camp summer 2003 schedule"
        # FIXME this doesn't extract as I'd have expected
        #store = h.parsestring("""
        #    <a href="page1.html" title="HS Jacobs - a UAHC camp in Utica, MS">Henry S. Jacobs Camp</a>
        #""")
        #assert len(store.units) == 2
        #assert store.units[0].source == "HS Jacobs - a UAHC camp in Utica, MS"
        #assert store.units[1].source == "Henry S. Jacobs Camp"
        store = h.parsestring("""
            <form name="application" title="Henry Jacobs camper application" method="  " action="  ">
        """)
        assert len(store.units) == 1
        assert store.units[0].source == "Henry Jacobs camper application"
