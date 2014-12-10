#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of translate.
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

"""
This module contains functions for identifying languages based on language
models.
"""

from os import extsep, path

from translate.misc.file_discovery import get_abs_data_filename
from translate.storage.base import TranslationStore

from ngram import NGram


class LanguageIdentifier(object):
    MODEL_DIR = get_abs_data_filename('langmodels')
    """The directory containing the ngram language model files."""
    CONF_FILE = 'fpdb.conf'
    """
    The name of the file that contains language name-code pairs
    (relative to C{MODEL_DIR}).
    """

    def __init__(self, model_dir=None, conf_file=None):
        if model_dir is None:
            model_dir = self.MODEL_DIR
        if not path.isdir(model_dir):
            raise ValueError('Directory does not exist: %s' % (model_dir))

        if conf_file is None:
            conf_file = self.CONF_FILE
        conf_file = path.abspath(path.join(model_dir, conf_file))
        if not path.isfile(conf_file):
            raise ValueError('File does not exist: %s' % (conf_file))

        self._load_config(conf_file)
        self.ngram = NGram(model_dir)

    def _load_config(self, conf_file):
        """Load the mapping of language names to language codes as given in the
            configuration file."""
        lines = open(conf_file).read().splitlines()
        self._lang_codes = {}
        for line in lines:
            parts = line.split()
            if not parts or line.startswith('#'):
                continue # Skip comment- and empty lines
            lname, lcode = parts[0], parts[1]

            lname = path.split(lname)[-1] # Make sure lname is not prefixed by directory names
            if extsep in lname:
                lname = lname[:lname.rindex(extsep)] # Remove extension if it has

            # Remove trailing '[_-]-utf8' from code
            if lcode.endswith('-utf8'):
                lcode = lcode[:-len('-utf8')]
            if lcode.endswith('-') or lcode.endswith('_'):
                lcode = lcode[:-1]

            self._lang_codes[lname] = lcode

    def identify_lang(self, text):
        """Identify the language of the text in the given string."""
        if not text:
            return None
        result = self.ngram.classify(text)
        if result in self._lang_codes:
            result = self._lang_codes[result]
        return result

    def identify_source_lang(self, instore):
        """Identify the source language of the given translation store or
            units.

            @type  instore: C{TranslationStore} or list or tuple of
                C{TranslationUnit}s.
            @param instore: The translation store to extract source text from.
            @returns: The identified language's code or C{None} if the language
                could not be identified."""
        if not isinstance(instore, (TranslationStore, list, tuple)):
            return None

        text = u' '.join(unit.source for unit in instore[:50] if unit.istranslatable() and unit.source)
        if not text:
            return None
        return self.identify_lang(text)

    def identify_target_lang(self, instore):
        """Identify the target language of the given translation store or
            units.

            @type  instore: C{TranslationStore} or list or tuple of
                C{TranslationUnit}s.
            @param instore: The translation store to extract target text from.
            @returns: The identified language's code or C{None} if the language
                could not be identified."""
        if not isinstance(instore, (TranslationStore, list, tuple)):
            return None

        text = u' '.join(unit.target for unit in instore[:200] if unit.istranslatable() and unit.target)
        if not text:
            return None
        return self.identify_lang(text)

if __name__ == "__main__":
    from sys import argv
    from os import path
    script_dir = path.abspath(path.dirname(argv[0]))
    identifier = LanguageIdentifier(path.join(script_dir, '..', 'share', 'langmodels'))
    import locale
    encoding = locale.getpreferredencoding()
    print "Language detected:", identifier.identify_lang(argv[1].decode(encoding))
