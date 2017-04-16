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

"""Merges XLIFF and Gettext PO localization files

Snippet file produced by pogrep or updated by a translator can be merged into
existing files

See: http://translate.sourceforge.net/wiki/toolkit/pomerge for examples and 
usage instructions
"""

import sys
from translate.storage import factory
from translate.storage import po
from translate.storage import xliff 
from translate.storage.poheader import poheader

def mergestores(store1, store2, mergeblanks, mergecomments):
    """Take any new translations in store2 and write them into store1."""

    for unit2 in store2.units:
        if unit2.isheader():
            if isinstance(store1, poheader):
                store1.mergeheaders(store2)
            # Skip header units
            continue
        # there may be more than one entity due to msguniq merge
        entities = unit2.getlocations()
        if len(entities) == 0:
            source = unit2.source
            unit1 = store1.findunit(source)
            if unit1 is None:
                sys.stderr.write(str(unit2) + "\n")
            else:
                # finally set the new definition in unit1
                unit1.merge(unit2, overwrite=True)
        for entity in entities:
            unit1 = None
            if store1.locationindex.has_key(entity):
                # now we need to replace the definition of entity with msgstr
                unit1 = store1.locationindex[entity] # find the other po
            # check if this is a duplicate in store2...
            if store2.locationindex.has_key(entity):
                if store2.locationindex[entity] is None:
                    unit1 = None
            # if locationindex was not unique, use the source index
            if unit1 is None:
                source = unit2.source
                unit1 = store1.findunit(source)
            # check if we found a matching po element
            if unit1 is None:
                print >> sys.stderr, "# the following po element was not found"
                sys.stderr.write(str(unit2) + "\n")
            else:
                if not mergeblanks:
                    target = unit2.target
                    if len(target.strip()) == 0: continue
                # finally set the new definition in unit1
                unit1.merge(unit2, overwrite=True, comments=mergecomments)
    return store1

def str2bool(option):
    """Convert a string value to boolean

    @param option: yes, true, 1, no, false, 0
    @type option: String
    @rtype: Boolean

    """
    option = option.lower()
    if option in ("yes", "true", "1"):
        return True
    elif option in ("no", "false", "0"):
        return False
    else:
        raise ValueError("invalid boolean value: %r" % option)

def mergestore(inputfile, outputfile, templatefile, mergeblanks="no", mergecomments="yes"):
    try:
        mergecomments = str2bool(mergecomments)
    except ValueError:
        raise ValueError("invalid mergecomments value: %r" % mergecomments)
    try:
        mergeblanks = str2bool(mergeblanks)
    except ValueError:
        raise ValueError("invalid mergeblanks value: %r" % mergeblanks)
    inputstore = factory.getobject(inputfile)
    if templatefile is None:
        # just merge nothing
        templatestore = type(inputstore)()
    else:
        templatestore = factory.getobject(templatefile)
    templatestore.makeindex()
    inputstore.makeindex()
    outputstore = mergestores(templatestore, inputstore, mergeblanks, mergecomments)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main():
    from translate.convert import convert
    pooutput = ("po", mergestore)
    potoutput = ("pot", mergestore)
    xliffoutput = ("xlf", mergestore)
    formats = {("po", "po"): pooutput, ("po", "pot"): pooutput, ("pot", "po"): pooutput, ("pot", "pot"): potoutput,
                "po": pooutput, "pot": pooutput,
                ("xlf", "po"): pooutput, ("xlf", "pot"): pooutput,
                ("xlf", "xlf"): xliffoutput, ("po", "xlf"): xliffoutput}
    mergeblanksoption = convert.optparse.Option("", "--mergeblanks", dest="mergeblanks",
        action="store", default="yes", help="whether to overwrite existing translations with blank translations (yes/no). Default is yes.")
    mergecommentsoption = convert.optparse.Option("", "--mergecomments", dest="mergecomments",
        action="store", default="yes", help="whether to merge comments as well as translations (yes/no). Default is yes.")
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_option(mergeblanksoption)
    parser.passthrough.append("mergeblanks")
    parser.add_option(mergecommentsoption)
    parser.passthrough.append("mergecomments")
    parser.run()


if __name__ == '__main__':
    main()
