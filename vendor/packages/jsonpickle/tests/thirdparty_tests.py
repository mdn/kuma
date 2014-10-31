# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Paulett (john -at- paulett.org)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

import jsonpickle

RSS_DOC = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:base="http://example.org/" xml:lang="en">
  <title type="text">Sample Feed</title>
  <subtitle type="html">For documentation &lt;em&gt;only&lt;/em&gt;</subtitle>
  <link rel="alternate" type="html" href="/"/>
  <link rel="self" type="application/atom+xml" href="http://www.example.org/atom10.xml"/>
  <rights type="html">&lt;p>Copyright 2005, Mark Pilgrim&lt;/p>&lt;</rights>

  <generator uri="http://example.org/generator/" version="4.0">Sample Toolkit</generator>
  <id>tag:feedparser.org,2005-11-09:/docs/examples/atom10.xml</id>
  <updated>2005-11-09T11:56:34Z</updated>
  <entry>
    <title>First entry title</title>
    <link rel="alternate" href="/entry/3"/>
    <link rel="related" type="text/html" href="http://search.example.com/"/>

    <link rel="via" type="text/html" href="http://toby.example.com/examples/atom10"/>
    <link rel="enclosure" type="video/mpeg4" href="http://www.example.com/movie.mp4" length="42301"/>
    <id>tag:feedparser.org,2005-11-09:/docs/examples/atom10.xml:3</id>
    <published>2005-11-09T00:23:47Z</published>
    <updated>2005-11-09T11:56:34Z</updated>
    <author>
      <name>Mark Pilgrim</name>

      <uri>http://diveintomark.org/</uri>
      <email>mark@example.org</email>
    </author>
    <contributor>
      <name>Joe</name>
      <uri>http://example.org/joe/</uri>
      <email>joe@example.org</email>

    </contributor>
    <contributor>
      <name>Sam</name>
      <uri>http://example.org/sam/</uri>
      <email>sam@example.org</email>
    </contributor>
    <summary type="text">Watch out for nasty tricks</summary>

    <content type="xhtml" xml:base="http://example.org/entry/3" xml:lang="en-US">
      <div xmlns="http://www.w3.org/1999/xhtml">Watch out for <span style="background: url(javascript:window.location='http://example.org/')"> nasty tricks</span></div>
    </content>
  </entry>
</feed>"""

class FeedParserTest(unittest.TestCase):
    def setUp(self):
        try:
            import feedparser
        except ImportError, e:
            self.fail("feedparser module not available, please install")
        self.doc = feedparser.parse(RSS_DOC)

    def test(self):
        pickled = jsonpickle.encode(self.doc)
        unpickled = jsonpickle.decode(pickled)
        self.assertEquals(self.doc['feed']['title'], unpickled['feed']['title'])

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FeedParserTest, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
