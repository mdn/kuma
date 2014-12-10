#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
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

import re

charset_re = re.compile('CHARACTER_SET[ ]+(?P<charset>.*)')
header_item_or_end_re = re.compile('(((?P<key>[^ ]+)(?P<space>[ ]*:[ ]*)(?P<value>.*))|(?P<end_comment>[*]/))')
header_item_re = re.compile('(?P<key>[^ ]+)(?P<space>[ ]*:[ ]*)(?P<value>.*)')
string_entry_re = re.compile('(?P<start>rls_string[ ]+)(?P<id>[^ ]+)(?P<space>[ ]+)(?P<str>.*)')

def identity(x):
    return x

class ParseState(object):
    def __init__(self, f, charset, read_hook=identity):
        self.f = f
        self.charset = charset
        self.current_line = u''
        self.read_hook = read_hook
        self.read_line()

    def read_line(self):
        current_line = self.current_line
        self.read_hook(current_line)
        self.current_line = self.f.next().decode(self.charset)
        return current_line

def read_while(ps, f, test):
    result = f(ps.current_line)
    while test(result):
        ps.read_line()
        result = f(ps.current_line)
    return result

def eat_whitespace(ps):
    read_while(ps, identity, lambda line: line.strip() == '')

def skip_no_translate(ps):
    if ps.current_line.startswith('// DO NOT TRANSLATE'):
        ps.read_line()
        read_while(ps, identity, lambda line: not line.startswith('// DO NOT TRANSLATE'))
        ps.read_line()
        eat_whitespace(ps)

def read_charset(lines):
    for line in lines:
        match = charset_re.match(line)
        if match is not None:
            return match.groupdict()['charset']
    return 'UTF-8'
