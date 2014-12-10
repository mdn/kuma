#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008-2009 Zuza Software Foundation
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


"""Convert Gettext PO localization files to subtitle files"""

from translate.storage import factory

class resub:
    def __init__(self, templatefile):
        from translate.storage import subtitles
        self.templatefile = templatefile
        self.templatestore = subtitles.SubtitleFile(templatefile)
        self._inputdict = {}

    def convertstore(self, inputstore, includefuzzy=False):
        self._makestoredict(inputstore, includefuzzy)
        for unit in self.templatestore.units:
            for location in unit.getlocations():
                if location in self._inputdict:
                    unit.target = self._inputdict[location]
                else:
                    unit.target = unit.source
        return str(self.templatestore)

    def _makestoredict(self, store, includefuzzy=False):
        # make a dictionary of the translations
        for unit in store.units:
            if includefuzzy or not unit.isfuzzy():
                # there may be more than one entity due to msguniq merge
                for location in unit.getlocations():
                    substring = unit.target
                    if len(substring.strip()) == 0:
                        substring = unit.source
                    self._inputdict[location] = substring

def convertsub(inputfile, outputfile, templatefile, includefuzzy=False):
    inputstore = factory.getobject(inputfile)
    if templatefile is None:
        raise ValueError("must have template file for subtitle files")
    else:
        convertor = resub(templatefile)
    outputstring = convertor.convertstore(inputstore, includefuzzy)
    outputfile.write(outputstring)
    return 1

def main(argv=None):
    # handle command line options
    from translate.convert import convert
    formats = {("po", "srt"): ("srt", convertsub)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.add_fuzzy_option()
    parser.run(argv)

if __name__ == '__main__':
    main()

