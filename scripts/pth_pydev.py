#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import os
from shutil import copyfile

from xml.etree.ElementTree import Element, ElementTree, tostring

pth_file = sys.argv[1]
pydevproject_file = sys.argv[2]
prefix = sys.argv[3]

copyfile(pydevproject_file, pydevproject_file+'.bak')

tree = ElementTree()
tree.parse(pydevproject_file)
pydev_pathproperty = tree.find("pydev_pathproperty")
paths = pydev_pathproperty.getiterator('path')

with open(pth_file) as f:
    for line in f:
        pydev_entry = prefix + line.rstrip()
        if pydev_entry in paths:
            pass
        else:
            pydev_element = Element('path')
            pydev_element.text = pydev_entry
            pydev_pathproperty.append(pydev_element)

paths = pydev_pathproperty.getiterator('path')
print tostring(pydev_pathproperty)
tree.write(pydevproject_file)