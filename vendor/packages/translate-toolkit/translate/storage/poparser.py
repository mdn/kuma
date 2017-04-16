#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2007 Zuza Software Foundation
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

"""
From the GNU gettext manual:
     WHITE-SPACE
     #  TRANSLATOR-COMMENTS
     #. AUTOMATIC-COMMENTS
     #| PREVIOUS MSGID                 (Gettext 0.16 - check if this is the correct position - not yet implemented)
     #: REFERENCE...
     #, FLAG...
     msgctxt CONTEXT                   (Gettext 0.15)
     msgid UNTRANSLATED-STRING
     msgstr TRANSLATED-STRING
"""

isspace = str.isspace
find = str.find
rfind = str.rfind
startswith = str.startswith
append = list.append
decode = str.decode

class ParseState(object):
    def __init__(self, input_iterator, UnitClass, encoding = None):
        self._input_iterator = input_iterator
        self.next_line = ''
        self.eof = False
        self.encoding = encoding
        self.read_line()
        self.UnitClass = UnitClass

    def decode(self, string):
        if self.encoding is not None:
            return decode(string, self.encoding)
        else:
            return string

    def read_line(self):
        current = self.next_line
        if self.eof:
            return current
        try:
            self.next_line = self._input_iterator.next()
            while not self.eof and isspace(self.next_line):
                self.next_line = self._input_iterator.next()
        except StopIteration:
            self.next_line = ''
            self.eof = True
        return current

    def new_input(self, _input):
        return ParseState(_input, self.UnitClass, self.encoding)

def read_prevmsgid_lines(parse_state):
    """Read all the lines belonging starting with #|. These lines contain
    the previous msgid and msgctxt info. We strip away the leading '#| '
    and read until we stop seeing #|."""
    prevmsgid_lines = []
    next_line = parse_state.next_line
    while startswith(next_line, '#| '):
        append(prevmsgid_lines, parse_state.read_line()[3:])
        next_line = parse_state.next_line
    return prevmsgid_lines

def parse_prev_msgctxt(parse_state, unit):
    parse_message(parse_state, 'msgctxt', 7, unit.prev_msgctxt)
    return len(unit.prev_msgctxt) > 0

def parse_prev_msgid(parse_state, unit):
    parse_message(parse_state, 'msgid', 5, unit.prev_msgid)
    return len(unit.prev_msgid) > 0

def parse_prev_msgid_plural(parse_state, unit):
    parse_message(parse_state, 'msgid_plural', 12, unit.prev_msgid_plural)
    return len(unit.prev_msgid_plural) > 0

def parse_comment(parse_state, unit):
    next_line = parse_state.next_line
    if len(next_line) > 0 and next_line[0] == '#':
        next_char = next_line[1] 
        if next_char == '.':
            append(unit.automaticcomments, parse_state.decode(next_line))
        elif next_char == '|':
            # Read all the lines starting with #|
            prevmsgid_lines = read_prevmsgid_lines(parse_state)
            # Create a parse state object that holds these lines
            ps = parse_state.new_input(iter(prevmsgid_lines))
            # Parse the msgctxt if any
            parse_prev_msgctxt(ps, unit)
            # Parse the msgid if any
            parse_prev_msgid(ps, unit)
            # Parse the msgid_plural if any
            parse_prev_msgid_plural(ps, unit)
            return parse_state.next_line
        elif next_char == ':':
            append(unit.sourcecomments, parse_state.decode(next_line))
        elif next_char == ',':
            append(unit.typecomments, parse_state.decode(next_line))
        elif next_char == '~': 
            # Special case: we refuse to parse obsoletes: they are done
            # elsewhere to ensure we reuse the normal unit parsing code
            return None
        else:
            append(unit.othercomments, parse_state.decode(next_line))
        return parse_state.read_line()
    else:
        return None

def parse_comments(parse_state, unit):
    if not parse_comment(parse_state, unit):
        return None
    else:
        while parse_comment(parse_state, unit):
            pass
        return True

def read_obsolete_lines(parse_state):
    """Read all the lines belonging to the current unit if obsolete."""
    obsolete_lines = []
    if startswith(parse_state.next_line, '#~ '):
        append(obsolete_lines, parse_state.read_line()[3:])
    else:
        return obsolete_lines
    # Be extra careful that we don't start reading into a new unit. We detect
    # that with #~ msgid followed by a space (to ensure msgid_plural works)
    next_line = parse_state.next_line
    if startswith(next_line, '#~ msgid ') and obsolete_lines[-1].startswith('msgctxt'):
        append(obsolete_lines, parse_state.read_line()[3:])
        next_line = parse_state.next_line
    while startswith(next_line, '#~ ') and not (startswith(next_line, '#~ msgid ') or startswith(next_line, '#~ msgctxt')):
        append(obsolete_lines, parse_state.read_line()[3:])
        next_line = parse_state.next_line
    return obsolete_lines

def parse_obsolete(parse_state, unit):
    obsolete_lines = read_obsolete_lines(parse_state)
    if obsolete_lines == []:
        return None
    unit = parse_unit(parse_state.new_input(iter(obsolete_lines)), unit)
    if unit is not None:
        unit.makeobsolete()
    return unit

def parse_quoted(parse_state, start_pos = 0):
    line = parse_state.next_line
    left = find(line, '"', start_pos)
    if left == start_pos or isspace(line[start_pos:left]):
        right = rfind(line, '"')
        if left != right:
            return parse_state.read_line()[left:right+1]
        else:
            # There is no terminating quote, so we append an extra quote, but
            # we also ignore the newline at the end (therefore the -1)
            return parse_state.read_line()[left:-1] + '"'
    return None

def parse_msg_comment(parse_state, msg_comment_list, string):
    while string is not None:
        append(msg_comment_list, parse_state.decode(string))
        if find(string, '\\n') > -1:
            return parse_quoted(parse_state)
        string = parse_quoted(parse_state)
    return None

def parse_multiple_quoted(parse_state, msg_list, msg_comment_list, first_start_pos=0):
    string = parse_quoted(parse_state, first_start_pos)
    while string is not None:
        if not startswith(string, '"_:'):
            append(msg_list, parse_state.decode(string))
            string = parse_quoted(parse_state) 
        else:
            string = parse_msg_comment(parse_state, msg_comment_list, string)

def parse_message(parse_state, start_of_string, start_of_string_len, msg_list, msg_comment_list=None):
    if msg_comment_list is None:
        msg_comment_list = []
    if startswith(parse_state.next_line, start_of_string):
        return parse_multiple_quoted(parse_state, msg_list, msg_comment_list, start_of_string_len)

def parse_msgctxt(parse_state, unit):
    parse_message(parse_state, 'msgctxt', 7, unit.msgctxt)
    return len(unit.msgctxt) > 0

def parse_msgid(parse_state, unit):
    parse_message(parse_state, 'msgid', 5, unit.msgid, unit.msgidcomments)
    return len(unit.msgid) > 0 or len(unit.msgidcomments) > 0

def parse_msgstr(parse_state, unit):
    parse_message(parse_state, 'msgstr', 6, unit.msgstr)
    return len(unit.msgstr) > 0

def parse_msgid_plural(parse_state, unit):
    parse_message(parse_state, 'msgid_plural', 12, unit.msgid_plural, unit.msgid_pluralcomments)
    return len(unit.msgid_plural) > 0 or len(unit.msgid_pluralcomments) > 0

MSGSTR_ARRAY_ENTRY_LEN = len('msgstr[')

def add_to_dict(msgstr_dict, line, right_bracket_pos, entry):
    index = int(line[MSGSTR_ARRAY_ENTRY_LEN:right_bracket_pos])
    if index not in msgstr_dict:
        msgstr_dict[index] = []
    msgstr_dict[index].extend(entry)

def get_entry(parse_state, right_bracket_pos):
    entry = []
    parse_message(parse_state, 'msgstr[', right_bracket_pos + 1, entry)
    return entry

def parse_msgstr_array_entry(parse_state, msgstr_dict):
    line = parse_state.next_line
    right_bracket_pos = find(line, ']', MSGSTR_ARRAY_ENTRY_LEN)
    if right_bracket_pos >= 0:
        entry = get_entry(parse_state, right_bracket_pos)
        if len(entry) > 0:
            add_to_dict(msgstr_dict, line, right_bracket_pos, entry)
            return True
        else:
            return False
    else:
        return False

def parse_msgstr_array(parse_state, unit):
    msgstr_dict = {}
    result = parse_msgstr_array_entry(parse_state, msgstr_dict)
    if not result: # We require at least one result
        return False
    while parse_msgstr_array_entry(parse_state, msgstr_dict):
        pass
    unit.msgstr = msgstr_dict
    return True

def parse_plural(parse_state, unit):
    if parse_msgid_plural(parse_state, unit) and \
       (parse_msgstr_array(parse_state, unit) or parse_msgstr(parse_state, unit)):
        return True
    else:
        return False

def parse_msg_entries(parse_state, unit):
    parse_msgctxt(parse_state, unit)
    if parse_msgid(parse_state, unit) and \
       (parse_msgstr(parse_state, unit) or parse_plural(parse_state, unit)):
        return True
    else:
        return False

def parse_unit(parse_state, unit=None):
    unit = unit or parse_state.UnitClass()
    parsed_comments = parse_comments(parse_state, unit)
    obsolete_unit = parse_obsolete(parse_state, unit)
    if obsolete_unit is not None:
        return obsolete_unit
    parsed_msg_entries = parse_msg_entries(parse_state, unit)
    if parsed_comments or parsed_msg_entries:
        return unit
    else:
        return None

def set_encoding(parse_state, store, unit):
    charset = None
    if isinstance(unit.msgstr, list) and len(unit.msgstr) > 0 and isinstance(unit.msgstr[0], str):
        charset = re.search("charset=([^\\s\\\\n]+)", "".join(unit.msgstr))
    if charset:
        encoding = charset.group(1)
        if encoding != 'CHARSET':
            store._encoding = encoding
        else:
            store._encoding = 'utf-8'
    else:
        store._encoding = 'utf-8'
    parse_state.encoding = store._encoding

def decode_list(lst, decode):
    return [decode(item) for item in lst]

def decode_header(unit, decode):
    for attr in ('msgctxt', 'msgid', 'msgid_pluralcomments',
                 'msgid_plural', 'msgstr', 'obsoletemsgctxt',
                 'obsoletemsgid', 'obsoletemsgid_pluralcomments',
                 'obsoletemsgid_plural', 'obsoletemsgstr',
                 'othercomments', 'automaticcomments', 'sourcecomments',
                 'typecomments', 'msgidcomments', 'obsoletemsgidcomments'):
        element = getattr(unit, attr)
        if isinstance(element, list):
            setattr(unit, attr, decode_list(element, decode))
        else:
            setattr(unit, attr, dict([(key, decode_list(value, decode)) for key, value in element.items()]))

def parse_header(parse_state, store):
    first_unit = parse_unit(parse_state)
    if first_unit is None:
        return None
    set_encoding(parse_state, store, first_unit)
    decode_header(first_unit, parse_state.decode)
    return first_unit

def parse_units(parse_state, store):
    unit = parse_header(parse_state, store)
    while unit:
        store.addunit(unit)
        unit = parse_unit(parse_state)
    return parse_state.eof
