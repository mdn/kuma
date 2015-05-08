#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006 Thomas Mangin
# Copyright (c) 2009-2010 Zuza Software Foundation
#
# This program is distributed under Gnu General Public License
# (cf. the file COPYING in distribution). Alternatively, you can use
# the program under the conditions of the Artistic License (as Perl).
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

"""Ngram models for language guessing.

.. note:: Orignal code from http://thomas.mangin.me.uk/data/source/ngram.py
"""

import glob
import re
import sys
from os import path


nb_ngrams = 400
white_space_re = re.compile('\s+')


class _NGram:

    def __init__(self, arg=None):
        if isinstance(arg, basestring):
            self.addText(arg)
            self.normalise()
        elif isinstance(arg, dict):
            # This must already be normalised!
            self.ngrams = arg
        else:
            self.ngrams = dict()

    def addText(self, text):
        if isinstance(text, str):
            text = text.decode('utf-8')

        ngrams = dict()

        for word in white_space_re.split(text):
            word = '_%s_' % word
            size = len(word)
            for i in xrange(size - 1):
                for s in (1, 2, 3, 4):
                    end = i + s
                    if end >= size:
                        break
                    sub = word[i:end]

                    if not sub in ngrams:
                        ngrams[sub] = 0
                    ngrams[sub] += 1

        self.ngrams = ngrams
        return self

    def sorted_by_score(self):
        sorted = [(self.ngrams[k], k) for k in self.ngrams]
        sorted.sort()
        sorted.reverse()
        sorted = sorted[:nb_ngrams]
        return sorted

    def normalise(self):
        ngrams = {}
        for count, (v, k) in enumerate(self.sorted_by_score()):
            ngrams[k] = count

        self.ngrams = ngrams
        return self

    def addValues(self, key, value):
        self.ngrams[key] = value
        return self

    def compare(self, ngram):
        d = 0
        ngrams = ngram.ngrams
        for k in self.ngrams:
            if k in ngrams:
                d += abs(ngrams[k] - self.ngrams[k])
            else:
                d += nb_ngrams
        return d


class NGram:

    def __init__(self, folder, ext='.lm'):
        self.ngrams = dict()
        folder = path.join(folder, '*' + ext)
        size = len(ext)

        for fname in glob.glob(path.normcase(folder)):
            lang = path.split(fname)[-1][:-size]
            ngrams = {}
            try:
                f = open(fname, 'r')
                lines = f.read().decode('utf-8').splitlines()
                try:
                    for i, line in enumerate(lines):
                        ngram, _t, _f = line.partition(u'\t')
                        ngrams[ngram] = i
                except AttributeError as e:
                    # Python2.4 doesn't have unicode.partition()
                    for i, line in enumerate(lines):
                        ngram = line.split(u'\t')[0]
                        ngrams[ngram] = i
            except UnicodeDecodeError as e:
                continue

            if ngrams:
                self.ngrams[lang] = _NGram(ngrams)

        if not self.ngrams:
            raise ValueError("no language files found")

    def classify(self, text):
        ngram = _NGram(text)
        r = 'guess'

        min = sys.maxint

        for lang in self.ngrams:
            d = self.ngrams[lang].compare(ngram)
            if d < min:
                min = d
                r = lang

        if min > 0.8 * (nb_ngrams ** 2):
            r = ''
        return r


class Generate:

    def __init__(self, folder, ext='.txt'):
        self.ngrams = dict()
        folder = path.join(folder, '*' + ext)
        size = len(ext)

        for fname in glob.glob(path.normcase(folder)):
            lang = path.split(fname)[-1][:-size]
            n = _NGram()

            file = open(fname, 'r')
            for line in file.readlines():
                n.addText(line)
            file.close()

            n.normalise()
            self.ngrams[lang] = n

    def save(self, folder, ext='.lm'):
        for lang in self.ngrams.keys():
            fname = path.join(folder, lang + ext)
            file = open(fname, 'w')
            for v, k in self.ngrams[lang].sorted_by_score():
                file.write("%s\t %d\n" % (k, v))
            file.close()

if __name__ == '__main__':
    import sys

    # Should you want to generate your own .lm files
    #conf = Generate('/tmp')
    #conf.save('/tmp')

    text = sys.stdin.readline()
    from translate.misc.file_discovery import get_abs_data_filename
    l = NGram(get_abs_data_filename('langmodels'))
    print(l.classify(text))
