#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""simple parser / string tokenizer
rather than returning a list of token types etc, we simple return a list
of tokens.  Each tokenizing function takes a string as input and returns
a list of tokens.
"""

# Copyright 2002, 2003 St James Software
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
# along with this program; if not, see <http://www.gnu.org/licenses/>.


def stringeval(text):
    """takes away repeated quotes (escapes) and returns the string
    represented by the text"""
    stringchar = text[0]
    if text[-1] != stringchar or stringchar not in ("'", '"'):
        # scratch your head
        raise ValueError("error parsing escaped string: %r" % text)
    return text[1:-1].replace((stringchar + stringchar), stringchar)


def stringquote(text):
    """escapes quotes as neccessary and returns a string representing
    the text"""
    if "'" in text:
        if '"' in text:
            return '"' + text.replace('"', '""') + '"'
        else:
            return '"' + text + '"'
    else:
        return "'" + text + "'"


class ParserError(ValueError):
    """Intelligent parser error"""

    def __init__(self, parser, message, tokennum):
        """takes a message and the number of the token that caused the error"""
        tokenpos = parser.findtokenpos(tokennum)
        line, charpos = parser.getlinepos(tokenpos)
        ValueError.__init__(self, "%s at line %d, char %d (token %r)" %
                                  (message, line, charpos, parser.tokens[tokennum]))
        self.parser = parser
        self.tokennum = tokennum


class SimpleParser:
    """this is a simple parser"""

    def __init__(self, defaulttokenlist=None, whitespacechars=" \t\r\n",
                 includewhitespacetokens=0):
        if defaulttokenlist is None:
            self.defaulttokenlist = ['<=', '>=', '==', '!=',
                                     '+=', '-=', '*=', '/=', '<>']
            self.defaulttokenlist.extend('(),[]:=+-')
        else:
            self.defaulttokenlist = defaulttokenlist
        self.whitespacechars = whitespacechars
        self.includewhitespacetokens = includewhitespacetokens
        self.standardtokenizers = [
            self.stringtokenize, self.removewhitespace, self.separatetokens
        ]
        self.quotechars = ('"', "'")
        self.endquotechars = {'"': '"', "'": "'"}
        self.stringescaping = 1

    def stringtokenize(self, text):
        """makes strings in text into tokens..."""
        tokens = []
        laststart = 0
        instring = 0
        endstringchar, escapechar = '', '\\'
        gotclose, gotescape = 0, 0
        for pos in range(len(text)):
            char = text[pos]
            if instring:
                if (self.stringescaping and
                    (gotescape or char == escapechar) and not gotclose):
                    gotescape = not gotescape
                elif char == endstringchar:
                    gotclose = not gotclose
                elif gotclose:
                    tokens.append(text[laststart:pos])
                    instring, laststart, endstringchar = 0, pos, ''
            if not instring:
                if char in self.quotechars:
                    if pos > laststart:
                        tokens.append(text[laststart:pos])
                    instring, laststart, endstringchar, gotclose = 1, pos, self.endquotechars[char], 0
        if laststart < len(text):
            tokens.append(text[laststart:])
        return tokens

    def keeptogether(self, text):
        """checks whether a token should be kept together"""
        return self.isstringtoken(text)

    def isstringtoken(self, text):
        """checks whether a token is a string token"""
        return text[:1] in self.quotechars

    def separatetokens(self, text, tokenlist=None):
        """this separates out tokens in tokenlist from whitespace etc"""
        if self.keeptogether(text):
            return [text]
        if tokenlist is None:
            tokenlist = self.defaulttokenlist
        # loop through and put tokens into a list
        tokens = []
        pos = 0
        laststart = 0
        lentext = len(text)
        while pos < lentext:
            foundtoken = 0
            for token in tokenlist:
                lentoken = len(token)
                if text[pos:pos+lentoken] == token:
                    if laststart < pos:
                        tokens.append(text[laststart:pos])
                    tokens.append(token)
                    pos += lentoken
                    foundtoken, laststart = 1, pos
                    break
            if not foundtoken:
                pos += 1
        if laststart < lentext:
            tokens.append(text[laststart:])
        return tokens

    def removewhitespace(self, text):
        """this removes whitespace but lets it separate things out into
        separate tokens"""
        if self.keeptogether(text):
            return [text]
        # loop through and put tokens into a list
        tokens = []
        pos = 0
        inwhitespace = 0
        laststart = 0
        for pos in range(len(text)):
            char = text[pos]
            if inwhitespace:
                if char not in self.whitespacechars:
                    if laststart < pos and self.includewhitespacetokens:
                        tokens.append(text[laststart:pos])
                    inwhitespace, laststart = 0, pos
            else:
                if char in self.whitespacechars:
                    if laststart < pos:
                        tokens.append(text[laststart:pos])
                    inwhitespace, laststart = 1, pos
        if (laststart < len(text) and
            (not inwhitespace or self.includewhitespacetokens)):
            tokens.append(text[laststart:])
        return tokens

    def applytokenizer(self, inputlist, tokenizer):
        """apply a tokenizer to a set of text, flattening the result"""
        tokenizedlists = [tokenizer(text) for text in inputlist]
        joined = []
        map(joined.extend, tokenizedlists)
        return joined

    def applytokenizers(self, inputlist, tokenizers):
        """apply a set of tokenizers to a set of text, flattening each time"""
        for tokenizer in tokenizers:
            inputlist = self.applytokenizer(inputlist, tokenizer)
        return inputlist

    def tokenize(self, source, tokenizers=None):
        """tokenize the text string with the standard tokenizers"""
        self.source = source
        if tokenizers is None:
            tokenizers = self.standardtokenizers
        self.tokens = self.applytokenizers([self.source], tokenizers)
        return self.tokens

    def findtokenpos(self, tokennum):
        """finds the position of the given token in the text"""
        currenttokenpos = 0
        for currenttokennum in range(tokennum + 1):
            currenttokenpos = self.source.find(self.tokens[currenttokennum],
                                               currenttokenpos)
        return currenttokenpos

    def getlinepos(self, tokenpos):
        """finds the line and character position of the given character"""
        sourcecut = self.source[:tokenpos]
        line = sourcecut.count("\n") + 1
        charpos = tokenpos - sourcecut.rfind("\n")
        return line, charpos

    def raiseerror(self, message, tokennum):
        """raises a ParserError"""
        raise ParserError(self, message, tokennum)
