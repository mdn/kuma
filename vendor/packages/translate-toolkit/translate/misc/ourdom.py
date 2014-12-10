#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2007 Zuza Software Foundation
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

"""module that provides modified DOM functionality for our needs

Note that users of ourdom should ensure that no code might still use classes 
directly from minidom, like minidom.Element, minidom.Document or methods such 
as minidom.parseString, since the functionality provided here will not be in 
those objects.
"""

from xml.dom import minidom
from xml.dom import expatbuilder

# helper functions we use to do xml the way we want, used by modified classes below

def writexml_helper(self, writer, indent="", addindent="", newl=""):
    """A replacement for writexml that formats it like typical XML files.
    Nodes are intendented but text nodes, where whitespace can be significant, are not indented."""
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        # We need to write text nodes without newline and indentation, so 
        # we handle them differently. Note that we here assume that "empty" 
        # text nodes can be done away with (see the strip()). Note also that 
        # nested tags in a text node (like ph tags in xliff) should also not 
        # have newlines and indentation or an extra newline, since that will 
        # alter the text node.
        haveText = False
        for childNode in self.childNodes:
            if childNode.nodeType == self.TEXT_NODE and childNode.data.strip():
                haveText = True
                break
        if haveText:
          writer.write(">")
          for node in self.childNodes:
              node.writexml(writer,"","","")
          writer.write("</%s>%s" % (self.tagName,newl))
        else:
          # This is the normal case that we do with pretty layout
          writer.write(">%s"%(newl))
          for node in self.childNodes:
              if node.nodeType != self.TEXT_NODE:
                  node.writexml(writer,indent+addindent,addindent,newl)
          writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))

def getElementsByTagName_helper(parent, name, dummy=None):
    """A reimplementation of getElementsByTagName as an iterator.

    Note that this is not compatible with getElementsByTagName that returns a 
    list, therefore, the class below exposes this through yieldElementsByTagName"""

    for node in parent.childNodes:
        if node.nodeType == minidom.Node.ELEMENT_NODE and \
            (name == "*" or node.tagName == name):
            yield node
        if node.hasChildNodes():
            for othernode in node.getElementsByTagName(name):
                yield othernode

def searchElementsByTagName_helper(parent, name, onlysearch):
    """limits the search to within tags occuring in onlysearch"""
    for node in parent.childNodes:
        if node.nodeType == minidom.Node.ELEMENT_NODE and \
            (name == "*" or node.tagName == name):
            yield node
        if node.nodeType == minidom.Node.ELEMENT_NODE and node.tagName in onlysearch:
            for node in node.searchElementsByTagName(name, onlysearch):
                yield node

def getFirstElementByTagName(node, name):
  results = node.yieldElementsByTagName(name)
#  if isinstance(results, list):
#    if len(results) == 0:
#      return None
#    else:
#      return results[0]
  try:
    result = results.next()
    return result
  except StopIteration:
    return None

def getnodetext(node):
  """returns the node's text by iterating through the child nodes"""
  if node is None: return ""
  return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

# various modifications to minidom classes to add functionality we like

class DOMImplementation(minidom.DOMImplementation):
  def _create_document(self):
    return Document()

class Element(minidom.Element):
  def yieldElementsByTagName(self, name):
    return getElementsByTagName_helper(self, name)
  def searchElementsByTagName(self, name, onlysearch):
    return searchElementsByTagName_helper(self, name, onlysearch)
  def writexml(self, writer, indent, addindent, newl):
    return writexml_helper(self, writer, indent, addindent, newl)

class Document(minidom.Document):
  implementation = DOMImplementation()
  def yieldElementsByTagName(self, name):
    return getElementsByTagName_helper(self, name)
  def searchElementsByTagName(self, name, onlysearch):
    return searchElementsByTagName_helper(self, name, onlysearch)
  def createElement(self, tagName):
    e = Element(tagName)
    e.ownerDocument = self
    return e
  def createElementNS(self, namespaceURI, qualifiedName):
    prefix, localName = _nssplit(qualifiedName)
    e = Element(qualifiedName, namespaceURI, prefix)
    e.ownerDocument = self
    return e

theDOMImplementation = DOMImplementation()

# an ExpatBuilder that allows us to use the above modifications

class ExpatBuilderNS(expatbuilder.ExpatBuilderNS):
  def reset(self):
    """Free all data structures used during DOM construction."""
    self.document = theDOMImplementation.createDocument(
      expatbuilder.EMPTY_NAMESPACE, None, None)
    self.curNode = self.document
    self._elem_info = self.document._elem_info
    self._cdata = False
    self._initNamespaces()

  def start_element_handler(self, name, attributes):
    # all we want to do is construct our own Element instead of minidom.Element
    # unfortunately the only way to do this is to copy this whole function from expatbuilder.py
    if ' ' in name:
      uri, localname, prefix, qname = expatbuilder._parse_ns_name(self, name)
    else:
      uri = expatbuilder.EMPTY_NAMESPACE
      qname = name
      localname = None
      prefix = expatbuilder.EMPTY_PREFIX
    node = Element(qname, uri, prefix, localname)
    node.ownerDocument = self.document
    expatbuilder._append_child(self.curNode, node)
    self.curNode = node

    if self._ns_ordered_prefixes:
      for prefix, uri in self._ns_ordered_prefixes:
        if prefix:
          a = minidom.Attr(expatbuilder._intern(self, 'xmlns:' + prefix),
                   expatbuilder.XMLNS_NAMESPACE, prefix, "xmlns")
        else:
          a = minidom.Attr("xmlns", expatbuilder.XMLNS_NAMESPACE,
                   "xmlns", expatbuilder.EMPTY_PREFIX)
        d = a.childNodes[0].__dict__
        d['data'] = d['nodeValue'] = uri
        d = a.__dict__
        d['value'] = d['nodeValue'] = uri
        d['ownerDocument'] = self.document
        expatbuilder._set_attribute_node(node, a)
      del self._ns_ordered_prefixes[:]

    if attributes:
      _attrs = node._attrs
      _attrsNS = node._attrsNS
      for i in range(0, len(attributes), 2):
        aname = attributes[i]
        value = attributes[i+1]
        if ' ' in aname:
          uri, localname, prefix, qname = expatbuilder._parse_ns_name(self, aname)
          a = minidom.Attr(qname, uri, localname, prefix)
          _attrs[qname] = a
          _attrsNS[(uri, localname)] = a
        else:
          a = minidom.Attr(aname, expatbuilder.EMPTY_NAMESPACE,
                   aname, expatbuilder.EMPTY_PREFIX)
          _attrs[aname] = a
          _attrsNS[(expatbuilder.EMPTY_NAMESPACE, aname)] = a
        d = a.childNodes[0].__dict__
        d['data'] = d['nodeValue'] = value
        d = a.__dict__
        d['ownerDocument'] = self.document
        d['value'] = d['nodeValue'] = value
        d['ownerElement'] = node

  if __debug__:
    # This only adds some asserts to the original
    # end_element_handler(), so we only define this when -O is not
    # used.  If changing one, be sure to check the other to see if
    # it needs to be changed as well.
    #
    def end_element_handler(self, name):
      curNode = self.curNode
      if ' ' in name:
        uri, localname, prefix, qname = expatbuilder._parse_ns_name(self, name)
        assert (curNode.namespaceURI == uri
            and curNode.localName == localname
            and curNode.prefix == prefix), \
            "element stack messed up! (namespace)"
      else:
        assert curNode.nodeName == name, \
             "element stack messed up - bad nodeName"
        assert curNode.namespaceURI == expatbuilder.EMPTY_NAMESPACE, \
             "element stack messed up - bad namespaceURI"
      self.curNode = curNode.parentNode
      self._finish_end_element(curNode)

# parser methods that use our modified xml classes

def parse(file, parser=None, bufsize=None):
  """Parse a file into a DOM by filename or file object."""
  builder = ExpatBuilderNS()
  if isinstance(file, basestring):
    fp = open(file, 'rb')
    try:
      result = builder.parseFile(fp)
    finally:
      fp.close()
  else:
    result = builder.parseFile(file)
  return result

def parseString(string, parser=None):
  """Parse a file into a DOM from a string."""
  builder = ExpatBuilderNS()
  return builder.parseString(string)

