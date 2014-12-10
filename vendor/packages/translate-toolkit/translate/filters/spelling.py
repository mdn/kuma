#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
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

"""An API to provide spell checking for use in checks or elsewhere."""

import sys

available = False

try:
    # Enchant
    from enchant import checker, DictNotFoundError, Error as EnchantError
    available = True
    checkers = {}
    def check(text, lang):
        if not lang in checkers:
            try:
                checkers[lang] = checker.SpellChecker(lang)
                # some versions only report an error when checking something
                checkers[lang].check('')
            except EnchantError, e:
                # sometimes this is raised instead of DictNotFoundError
                print >> sys.stderr, str(e)
                checkers[lang] = None

        if not checkers[lang]:
            return
        spellchecker = checkers[lang]
        spellchecker.set_text(unicode(text))
        for err in spellchecker:
            yield err.word, err.wordpos, err.suggest()

except ImportError:
    def check(text, lang):
        return []

