#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2006 Zuza Software Foundation
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

"""factory methods to build real storage objects that conform to base.py"""

import os
from gzip import GzipFile
try:
    # bz2 is not available on python 2.3
    from bz2 import BZ2File
except ImportError:
    BZ2File = None
import sys

from translate.storage import base
from translate.storage import csvl10n
from translate.storage import mo
from translate.storage import omegat
from translate.storage import po
from translate.storage import qm
from translate.storage import wordfast
#Let's try to import the XML formats carefully. They might fail if the user
#doesn't have lxml installed. Let's try to continue gracefully, but print an 
#informative warning.
try:
    #Although poxliff is unused in this module, it is referenced in test_factory
    from translate.storage import poxliff
    from translate.storage import qph
    from translate.storage import tbx
    from translate.storage import tmx
    from translate.storage import ts2 as ts
    from translate.storage import xliff
    support_xml = True
except ImportError, e:
    print >> sys.stderr, str(e)
    support_xml = False


#TODO: Monolingual formats (with template?)

classes = {
           "csv": csvl10n.csvfile, 
           "tab": omegat.OmegaTFileTab, "utf8": omegat.OmegaTFile,
           "po": po.pofile, "pot": po.pofile, 
           "mo": mo.mofile, "gmo": mo.mofile, 
           "qm": qm.qmfile, 
           "_wftm": wordfast.WordfastTMFile,
          }
"""Dictionary of file extensions and their associated class.  

_ext is a pseudo extension, that is their is no real extension by that name."""

if support_xml:
    classes.update({
           "qph": qph.QphFile,
           "tbx": tbx.tbxfile,
           "tmx": tmx.tmxfile, 
           "ts": ts.tsfile,
           "xliff": xliff.xlifffile, "xlf": xliff.xlifffile,
    })

decompressclass = {
    'gz': GzipFile,
}
if BZ2File:
    decompressclass['bz2'] = BZ2File

def _examine_txt(storefile):
    """Determine the true filetype for a .txt file"""
    if isinstance(storefile, basestring) and os.path.exists(storefile):
        storefile = open(storefile)
    try:
        start = storefile.read(600).strip()
    except AttributeError:
        raise ValueError("Need to read object to determine type")
    # Some encoding magic for Wordfast
    if wordfast.TAB_UTF16 in start.split("\n")[0]:
        encoding = 'utf-16'
    else:
        encoding = 'iso-8859-1'
    start = start.decode(encoding).encode('utf-8')
    if '%Wordfast TM' in start:
        pseudo_extension = '_wftm'
    else:
        raise ValueError("Failed to guess file type.")
    storefile.seek(0)
    return pseudo_extension

hiddenclasses = {"txt": _examine_txt}

def _guessextention(storefile):
    """Guesses the type of a file object by looking at the first few characters.
    The return value is a file extention ."""
    start = storefile.read(300).strip()
    if '<xliff ' in start:
        extention = 'xlf'
    elif 'msgid "' in start:
        extention = 'po'
    elif '%Wordfast TM' in start:
        extention = 'txt'
    elif '<!DOCTYPE TS>' in start:
        extention = 'ts'
    else:
        raise ValueError("Failed to guess file type.")
    storefile.seek(0)
    return extention

def _getdummyname(storefile):
    """Provides a dummy name for a file object without a name attribute, by guessing the file type."""
    return 'dummy.' + _guessextention(storefile)

def _getname(storefile):
    """returns the filename"""
    if storefile is None:
        raise ValueError("This method cannot magically produce a filename when given None as input.")
    if not isinstance(storefile, basestring):
        if not hasattr(storefile, "name"):
            storefilename = _getdummyname(storefile)
        else:
            storefilename = storefile.name
    else:
        storefilename = storefile
    return storefilename

def getclass(storefile, ignore=None, classes=classes, hiddenclasses=hiddenclasses):
    """Factory that returns the applicable class for the type of file presented.
    Specify ignore to ignore some part at the back of the name (like .gz). """
    storefilename = _getname(storefile)
    if ignore and storefilename.endswith(ignore):
        storefilename = storefilename[:-len(ignore)]
    root, ext = os.path.splitext(storefilename)
    ext = ext[len(os.path.extsep):].lower()
    decomp = None
    if ext in decompressclass:
        decomp = ext
        root, ext = os.path.splitext(root)
        ext = ext[len(os.path.extsep):].lower()
    if ext in hiddenclasses:
        guesserfn = hiddenclasses[ext]
        if decomp:
            ext = guesserfn(decompressclass[decomp](storefile))
        else:
            ext = guesserfn(storefile)
    try:
        storeclass = classes[ext]
    except KeyError:
        raise ValueError("Unknown filetype (%s)" % storefilename)
    return storeclass

def getobject(storefile, ignore=None, classes=classes, hiddenclasses=hiddenclasses):
    """Factory that returns a usable object for the type of file presented.

    @type storefile: file or str
    @param storefile: File object or file name.

    Specify ignore to ignore some part at the back of the name (like .gz).
    """

    if isinstance(storefile, base.TranslationStore):
        return storefile
    if isinstance(storefile, basestring):
        if os.path.isdir(storefile) or storefile.endswith(os.path.sep):
            from translate.storage import directory
            return directory.Directory(storefile)
    storefilename = _getname(storefile)
    storeclass = getclass(storefile, ignore, classes=classes, hiddenclasses=hiddenclasses)
    if os.path.exists(storefilename) or not getattr(storefile, "closed", True):
        name, ext = os.path.splitext(storefilename)
        ext = ext[len(os.path.extsep):].lower()
        if ext in decompressclass:
            storefile = decompressclass[ext](storefilename)
        store = storeclass.parsefile(storefile)
    else:
        store = storeclass()
        store.filename = storefilename
    return store

def supported_files():
    """Returns data about all supported files

    @return: list of type that include (name, extensions, mimetypes)
    @rtype: list
    """

    supported = {}
    for supported_class in classes.itervalues():
        name = getattr(supported_class, "Name", None)
        if name is None:
            continue
        extensions = getattr(supported_class, "Extensions", None)
        mimetypes = getattr(supported_class, "Mimetypes", None)
        if not supported.has_key(name):
            supported[name] = (extensions, mimetypes)
        else:
            supported[name][0].extend(extensions)
            supported[name][1].extend(mimetypes)
    return [(name, ext_mime[0], ext_mime[1]) for name, ext_mime in supported.iteritems()]
