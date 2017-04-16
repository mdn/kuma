#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2005, 2006 Zuza Software Foundation
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

"""converts properties files back to funny mozilla files"""

from translate.storage import properties
from translate.convert import po2prop
from translate.convert import mozfunny2prop
from translate.misc.wStringIO import StringIO

def prop2inc(pf):
    """convert a properties file back to a .inc file with #defines in it"""
    # any leftover blanks will not be included at the end
    pendingblanks = []
    for unit in pf.units:
        for comment in unit.comments:
            if comment.startswith("# converted from") and "#defines" in comment:
                pass
            else:
                for blank in pendingblanks:
                    yield blank
                # TODO: could convert commented # x=y back to # #define x y
                yield comment
        if unit.isblank():
            pendingblanks.append("\n")
        else:
            definition = "#define %s %s\n" % (unit.name, unit.value.replace("\n", "\\n"))
            if isinstance(definition, unicode):
                definition = definition.encode("UTF-8")
            for blank in pendingblanks:
                yield blank
            yield definition

def prop2it(pf):
    """convert a properties file back to a pseudo-properties .it file"""
    for unit in pf.units:
        for comment in unit.comments:
            if comment.startswith("# converted from") and "pseudo-properties" in comment:
                pass
            elif comment.startswith("# section: "):
                yield comment.replace("# section: ", "", 1) + "\n"
            else:
                yield comment.replace("#", ";", 1) + "\n"
        if unit.isblank():
            yield ""
        else:
            definition = "%s=%s\n" % (unit.name, unit.value)
            if isinstance(definition, unicode):
                definition = definition.encode("UTF-8")
            yield definition

def prop2funny(src, itencoding="cp1252"):
    lines = src.split("\n")
    header = lines[0]
    if not header.startswith("# converted from "):
        waspseudoprops = len([line for line in lines if line.startswith("# section:")])
        wasdefines = len([line for line in lines if line.startswith("#filter") or line.startswith("#unfilter")])
    else:
        waspseudoprops = "pseudo-properties" in header
        wasdefines = "#defines" in header
        lines = lines[1:]
    if not (waspseudoprops ^ wasdefines):
        raise ValueError("could not determine file type as pseudo-properties or defines file")
    pf = properties.propfile(personality="mozilla")
    pf.parse("\n".join(lines))
    if wasdefines:
        for line in prop2inc(pf):
            yield line + "\n"
    elif waspseudoprops:
        for line in prop2it(pf):
            yield line.decode("utf-8").encode(itencoding) + "\n"

def po2inc(inputfile, outputfile, templatefile, encoding=None, includefuzzy=False):
    """wraps po2prop but converts outputfile to properties first"""
    outputpropfile = StringIO()
    if templatefile is not None:
        templatelines = templatefile.readlines()
        templateproplines = [line for line in mozfunny2prop.inc2prop(templatelines)]
        templatepropfile = StringIO("".join(templateproplines))
    else:
        templatepropfile = None
    result = po2prop.convertmozillaprop(inputfile, outputpropfile, templatepropfile, includefuzzy=includefuzzy)
    if result:
        outputpropfile.seek(0)
        pf = properties.propfile(outputpropfile, personality="mozilla")
        outputlines = prop2inc(pf)
        outputfile.writelines(outputlines)
    return result

def po2it(inputfile, outputfile, templatefile, encoding="cp1252", includefuzzy=False):
    """wraps po2prop but converts outputfile to properties first"""
    outputpropfile = StringIO()
    if templatefile is not None:
        templatelines = templatefile.readlines()
        templateproplines = [line for line in mozfunny2prop.it2prop(templatelines, encoding=encoding)]
        templatepropfile = StringIO("".join(templateproplines))
    else:
        templatepropfile = None
    result = po2prop.convertmozillaprop(inputfile, outputpropfile, templatepropfile, includefuzzy=includefuzzy)
    if result:
        outputpropfile.seek(0)
        pf = properties.propfile(outputpropfile, personality="mozilla")
        outputlines = prop2it(pf)
        for line in outputlines:
            line = line.decode("utf-8").encode(encoding)
            outputfile.write(line)
    return result

def po2ini(inputfile, outputfile, templatefile, encoding="UTF-8", includefuzzy=False):
    """wraps po2prop but converts outputfile to properties first using UTF-8 encoding"""
    return po2it(inputfile=inputfile, outputfile=outputfile, templatefile=templatefile, encoding=encoding, includefuzzy=includefuzzy)

def main(argv=None):
    import sys
    # TODO: get encoding from charset.mk, using parameter
    src = sys.stdin.read()
    for line in prop2funny(src):
        sys.stdout.write(line)

if __name__ == "__main__":
    main()

