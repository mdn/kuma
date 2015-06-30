#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2014 Zuza Software Foundation
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

"""Convert IDML files to PO localization files."""

from cStringIO import StringIO

from translate.convert import convert
from translate.storage import factory
from translate.storage.idml import (INLINE_ELEMENTS, NO_TRANSLATE_ELEMENTS,
                                    open_idml)
from translate.storage.xml_extract.extract import (IdMaker, ParseState,
                                                   build_idml_store,
                                                   make_postore_adder)


def convert_idml(inputfile, outputfile, template):
    """Convert an IDML package to PO."""
    # Since the convertoptionsparser will give us an open file, we risk that
    # it could have been opened in non-binary mode on Windows, and then we'll
    # have problems, so let's make sure we have what we want.
    inputfile.close()
    inputfile = file(inputfile.name, mode='rb')

    store = factory.getobject(outputfile)

    contents = open_idml(inputfile)

    id_maker = IdMaker()  # Create it here to avoid having repeated ids.

    for filename, translatable_file in contents.iteritems():
        parse_state = ParseState(NO_TRANSLATE_ELEMENTS, INLINE_ELEMENTS)
        po_store_adder = make_postore_adder(store, id_maker, filename)
        build_idml_store(StringIO(translatable_file), store, parse_state,
                         store_adder=po_store_adder)

    store.save()
    return True


def main(argv=None):
    formats = {
        "idml": ("po", convert_idml),
    }
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
