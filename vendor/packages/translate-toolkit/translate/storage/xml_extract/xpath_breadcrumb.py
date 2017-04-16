#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from translate.misc.typecheck import accepts, Self, IsCallable, IsOneOf, Any

class XPathBreadcrumb(object):
    """A class which is used to build XPath-like paths as a DOM tree is
    walked. It keeps track of the number of times which it has seen
    a certain tag, so that it will correctly create indices for tags.
    
    Initially, the path is empty. Thus
    >>> xb = XPathBreadcrumb()
    >>> xb.xpath
    ""
    
    Suppose we walk down a DOM node for the tag <foo> and we want to
    record this, we simply do
    >>> xb.start_tag('foo')
    
    Now, the path is no longer empty. Thus
    >>> xb.xpath
    foo[0]
    
    Now suppose there are two <bar> tags under the tag <foo> (that is
    <foo><bar></bar><bar></bar><foo>), then the breadcrumb will keep
    track of the number of times it sees <bar>. Thus
    
    >>> xb.start_tag('bar')
    >>> xb.xpath
    foo[0]/bar[0]
    >>> xb.end_tag()
    >>> xb.xpath
    foo[0]
    >>> xb.start_tag('bar')
    >>> xb.xpath
    foo[0]/bar[1]
    """

    def __init__(self):
        self._xpath = []
        self._tagtally = [{}]
        
    @accepts(Self(), unicode)
    def start_tag(self, tag):
        tally_dict = self._tagtally[-1]
        tally = tally_dict.get(tag, -1) + 1
        tally_dict[tag] = tally
        self._xpath.append((tag, tally))
        self._tagtally.append({})
      
    def end_tag(self):
        self._xpath.pop()
        self._tagtally.pop()

    def _get_xpath(self):
        def str_component(component):
            tag, pos = component
            return u"%s[%d]" % (tag, pos)
        return u"/".join(str_component(component) for component in self._xpath)
    
    xpath = property(_get_xpath)
