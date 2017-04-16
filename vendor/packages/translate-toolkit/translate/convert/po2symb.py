#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

"""convert Gettext PO localization files to Symbian translation files."""

import sys
from translate.storage import factory
from translate.storage.pypo import po_escape_map
from translate.storage.symbian import *

def escape(text):
    for key, val in po_escape_map.iteritems():
        text = text.replace(key, val)
    return '"%s"' % text

def replace_header_items(ps, replacments):
    match = read_while(ps, header_item_or_end_re.match, lambda match: match is None)
    while not ps.current_line.startswith('*/'):
        match = header_item_re.match(ps.current_line)
        if match is not None:
            key = match.groupdict()['key']
            if key in replacments:
                ps.current_line = match.expand('\g<key>\g<space>%s\n' % replacments[key])
        ps.read_line()

def parse(ps, header_replacements, body_replacements):
    replace_header_items(ps, header_replacements)
    try:
        while True:
            eat_whitespace(ps)
            skip_no_translate(ps)
            match = string_entry_re.match(ps.current_line)
            if match is not None:
                key = match.groupdict()['id']
                if key in body_replacements:
                    value = body_replacements[key].target or body_replacements[key].source
                    ps.current_line = match.expand(u'\g<start>\g<id>\g<space>%s\n' % escape(value))
            ps.read_line()
    except StopIteration:
        pass

def line_saver(charset):
    result = []
    def save_line(line):
        result.append(line.encode(charset))
    return result, save_line

def write_symbian(f, header_replacements, body_replacements):
    lines = list(f)
    charset = read_charset(lines)
    result, save_line = line_saver(charset)
    parse(ParseState(iter(lines), charset, save_line), header_replacements, body_replacements)
    return result

def build_location_index(store):
    po_header = store.parseheader()
    index = {}
    for unit in store.units:
        for location in unit.getlocations():
            index[location] = unit
    index['r_string_languagegroup_name'] = store.UnitClass(po_header['Language-Team'])
    return index

def build_header_index(store):
    po_header = store.parseheader()
    return {'Author': po_header['Last-Translator']}

def convert_symbian(input_file, output_file, template_file, pot=False, duplicatestyle="msgctxt"):
    store = factory.getobject(input_file)
    location_index = build_location_index(store)
    header_index = build_header_index(store)
    output = write_symbian(template_file, header_index, location_index)
    for line in output:
        output_file.write(line)
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"po": ("r0", convert_symbian)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, usepots=True, description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)

if __name__ == '__main__':
    main()

