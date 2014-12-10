#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004, 2005 Zuza Software Foundation
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

"""simpler wrapper to the elementtree XML parser"""

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
# this is needed to prevent expat-version conflicts with wx >= 2.5.2.2
from xml.parsers import expat

basicfixtag = ElementTree.fixtag

def makefixtagproc(namespacemap):
    """this constructs an alternative fixtag procedure that will use appropriate names for namespaces..."""
    def fixtag(tag, namespaces):
        """given a decorated tag (of the form {uri}tag), return prefixed tag and namespace declaration, if any"""
        if isinstance(tag, ElementTree.QName):
            tag = tag.text
        namespace_uri, tag = tag[1:].split("}", 1)
        prefix = namespaces.get(namespace_uri)
        if prefix is None:
            if namespace_uri in namespacemap:
                prefix = namespacemap[namespace_uri]
            else:
                prefix = "ns%d" % len(namespaces)
            namespaces[namespace_uri] = prefix
            xmlns = ("xmlns:%s" % prefix, namespace_uri)
        else:
            xmlns = None
        return "%s:%s" % (prefix, tag), xmlns
    return fixtag

def splitnamespace(fulltag):
    if '{' in fulltag:
        namespace = fulltag[fulltag.find('{'):fulltag.find('}')+1]
    else:
        namespace = ""
    tag = fulltag.replace(namespace, "", 1)
    return namespace, tag

class XMLWrapper:
    """simple wrapper for xml objects"""
    def __init__(self,obj):
        """construct object from the elementtree item"""
        self.obj = obj
        self.namespace, self.tag = splitnamespace(self.obj.tag)
        self.attrib = {}
        for fullkey, value in self.obj.attrib.iteritems():
            namespace, key = splitnamespace(fullkey)
            self.attrib[key] = value
    def getchild(self, searchtag, tagclass=None):
        """get a child with the given tag name"""
        if tagclass is None: tagclass = XMLWrapper
        for childobj in self.obj.getiterator():
            # getiterator() includes self...
            if childobj == self.obj: continue
            childns, childtag = splitnamespace(childobj.tag)
            if childtag == searchtag:
                child = tagclass(childobj)
                return child
        raise KeyError("could not find child with tag %r" % searchtag)
    def getchildren(self, searchtag, tagclass=None, excludetags=[]):
        """get all children with the given tag name"""
        if tagclass is None: tagclass = XMLWrapper
        childobjects = []
        for childobj in self.obj.getiterator():
            # getiterator() includes self...
            if childobj == self.obj: continue
            childns, childtag = splitnamespace(childobj.tag)
            if childtag == searchtag:
                childobjects.append(childobj)
        children = [tagclass(childobj) for childobj in childobjects]
        return children
    def gettext(self, searchtag):
        """get some contained text"""
        return self.getchild(searchtag).obj.text
    def getxml(self, encoding=None):
        return ElementTree.tostring(self.obj, encoding)
    def getplaintext(self, excludetags=[]):
        text = ""
        if self.obj.text != None: text += self.obj.text
        for child in self.obj._children:
            simplechild = XMLWrapper(child)
            if simplechild.tag not in excludetags:
                text += simplechild.getplaintext(excludetags)
        if self.obj.tail != None: text += self.obj.tail
        return text
    def getvalues(self, searchtag):
        """get some contained values..."""
        values = [child.obj.text for child in self.getchildren(searchtag)]
        return values
    def __repr__(self):
        """return a representation of the object"""
        return self.tag+':'+repr(self.__dict__)
    def getattr(self, attrname):
        """gets an attribute of the tag"""
        return self.attrib[attrname]
    def write(self, file, encoding="UTF-8"):
        """writes the object as XML to a file..."""
        e = ElementTree.ElementTree(self.obj)
        e.write(file, encoding)

def BuildTree(xmlstring):
    parser = ElementTree.XMLTreeBuilder()
    parser.feed(xmlstring)
    return parser.close()

def MakeElement(tag, attrib={}, **extraargs):
    return ElementTree.Element(tag, attrib, **extraargs)

