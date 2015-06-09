#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2010 Zuza Software Foundation
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

"""factory methods to build real storage objects that conform to base.py"""

import os


#TODO: Monolingual formats (with template?)

decompressclass = {
    'gz': ("gzip", "GzipFile"),
    'bz2': ("bz2", "BZ2File"),
}


classes_str = {
           "csv": ("csvl10n", "csvfile"),
           "tab": ("omegat", "OmegaTFileTab"), "utf8": ("omegat", "OmegaTFile"),
           "po": ("po", "pofile"), "pot": ("po", "pofile"),
           "mo": ("mo", "mofile"), "gmo": ("mo", "mofile"),
           "qm": ("qm", "qmfile"),
           "lang": ("mozilla_lang", "LangStore"),
           "utx": ("utx", "UtxFile"),
           "_wftm": ("wordfast", "WordfastTMFile"),
           "_trados_txt_tm": ("trados", "TradosTxtTmFile"),
           "catkeys": ("catkeys", "CatkeysFile"),

           "qph": ("qph", "QphFile"),
           "tbx": ("tbx", "tbxfile"),
           "tmx": ("tmx", "tmxfile"),
           "ts": ("ts2", "tsfile"),
           "xliff": ("xliff", "xlifffile"), "xlf": ("xliff", "xlifffile"),
           "sdlxliff": ("xliff", "xlifffile"),
}
###  XXX:  if you add anything here, you must also add it to translate.storage.

"""Dictionary of file extensions and the names of their associated class.

Used for dynamic lazy loading of modules.
_ext is a pseudo extension, that is their is no real extension by that name.
"""


def _examine_txt(storefile):
    """Determine the true filetype for a .txt file"""
    if isinstance(storefile, basestring) and os.path.exists(storefile):
        storefile = open(storefile)
    try:
        start = storefile.read(600).strip()
    except AttributeError:
        raise ValueError("Need to read object to determine type")
    # Some encoding magic for Wordfast
    from translate.storage import wordfast
    if wordfast.TAB_UTF16 in start.split("\n")[0]:
        encoding = 'utf-16'
    else:
        encoding = 'iso-8859-1'
    start = start.decode(encoding).encode('utf-8')
    if '%Wordfast TM' in start:
        pseudo_extension = '_wftm'
    elif '<RTF Preamble>' in start:
        pseudo_extension = '_trados_txt_tm'
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
    elif '<tmx ' in start:
        extention = 'tmx'
    elif '#UTX' in start:
        extention = 'utx'
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


def getclass(storefile, ignore=None, classes=None, classes_str=classes_str, hiddenclasses=hiddenclasses):
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
            _module, _class = decompressclass[decomp]
            module = __import__(_module, globals(), {}, [])
            _file = getattr(module, _class)
            ext = guesserfn(_file(storefile))
        else:
            ext = guesserfn(storefile)
    try:
        # we prefer classes (if given) since that is the older API that Pootle uses
        if classes:
            storeclass = classes[ext]
        else:
            _module, _class = classes_str[ext]
            module = __import__("translate.storage.%s" % _module, globals(), {}, _module)
            storeclass = getattr(module, _class)
    except KeyError:
        raise ValueError("Unknown filetype (%s)" % storefilename)
    return storeclass


def getobject(storefile, ignore=None, classes=None, classes_str=classes_str, hiddenclasses=hiddenclasses):
    """Factory that returns a usable object for the type of file presented.

    :type storefile: file or str
    :param storefile: File object or file name.

    Specify ignore to ignore some part at the back of the name (like .gz).
    """

    if isinstance(storefile, basestring):
        if os.path.isdir(storefile) or storefile.endswith(os.path.sep):
            from translate.storage import directory
            return directory.Directory(storefile)
    storefilename = _getname(storefile)
    storeclass = getclass(storefile, ignore, classes=classes, classes_str=classes_str, hiddenclasses=hiddenclasses)
    if os.path.exists(storefilename) or not getattr(storefile, "closed", True):
        name, ext = os.path.splitext(storefilename)
        ext = ext[len(os.path.extsep):].lower()
        if ext in decompressclass:
            _module, _class = decompressclass[ext]
            module = __import__(_module, globals(), {}, [])
            _file = getattr(module, _class)
            storefile = _file(storefilename)
        store = storeclass.parsefile(storefile)
    else:
        store = storeclass()
        store.filename = storefilename
    return store


supported = [
        ('Gettext PO file', ['po', 'pot'], ["text/x-gettext-catalog", "text/x-gettext-translation", "text/x-po", "text/x-pot"]),
        ('XLIFF Translation File', ['xlf', 'xliff', 'sdlxliff'], ["application/x-xliff", "application/x-xliff+xml"]),
        ('Gettext MO file', ['mo', 'gmo'], ["application/x-gettext-catalog", "application/x-mo"]),
        ('Qt .qm file', ['qm'], ["application/x-qm"]),
        ('TBX Glossary', ['tbx'], ['application/x-tbx']),
        ('TMX Translation Memory', ['tmx'], ["application/x-tmx"]),
        ('Qt Linguist Translation File', ['ts'], ["application/x-linguist"]),
        ('Qt Phrase Book', ['qph'], ["application/x-qph"]),
        ('OmegaT Glossary', ['utf8', 'tab'], ["application/x-omegat-glossary"]),
        ('UTX Dictionary', ['utx'], ["text/x-utx"]),
        ('Haiku catkeys file', ['catkeys'], ["application/x-catkeys"]),
]


def supported_files():
    """Returns data about all supported files

    :return: list of type that include (name, extensions, mimetypes)
    :rtype: list
    """
    return supported[:]
