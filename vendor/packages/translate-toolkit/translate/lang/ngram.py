#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006 Thomas Mangin
# Copyright (c) 2009 Zuza Software Foundation
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Orignal file from http://thomas.mangin.me.uk/data/source/ngram.py

import re

nb_ngrams = 400

class _NGram:
    def __init__(self, arg={}):
        if isinstance(arg, basestring):
            self.addText(arg)
            self.normalise()
        elif isinstance(arg, dict):
            self.ngrams = arg
            self.normalise()
        else:
            self.ngrams = dict()

    def addText(self, text):
        if isinstance(text, str):
            text = text.decode('utf-8')

        ngrams = dict()

        text = text.replace('\n', ' ')
        text = re.sub('\s+', ' ', text)
        words = text.split(' ')

        for word in words:
            word = '_'+word+'_'
            size = len(word)
            for i in xrange(size):
                for s in (1, 2, 3, 4):
                    sub = word[i:i+s]
                    if not ngrams.has_key(sub):
                        ngrams[sub] = 0
                    ngrams[sub] += 1

                    if i+s >= size:
                        break
        self.ngrams = ngrams
        return self

    def sorted(self):
        sorted = [(self.ngrams[k], k) for k in self.ngrams.keys()]
        sorted.sort()
        sorted.reverse()
        sorted = sorted[:nb_ngrams]
        return sorted

    def normalise(self):
        count = 0
        ngrams = {}
        for v, k in self.sorted():
            ngrams[k] = count
            count += 1

        self.ngrams = ngrams
        return self

    def addValues(self, key, value):
        self.ngrams[key] = value
        return self

    def compare(self, ngram):
        d = 0
        ngrams = ngram.ngrams
        for k in self.ngrams.keys():
            if ngrams.has_key(k):
                d += abs(ngrams[k] - self.ngrams[k])
            else:
                d += nb_ngrams
        return d


import os
import glob

class NGram:
    def __init__(self, folder, ext='.lm'):
        self.ngrams = dict()
        folder = os.path.join(folder, '*'+ext)
        size = len(ext)
        count = 0

        for fname in glob.glob(os.path.normcase(folder)):
            count += 1
            lang = os.path.split(fname)[-1][:-size]
            ngrams = {}
            lines = open(fname, 'r').readlines()

            try:
                i = len(lines)
                for line in lines:
                    line = line.decode('utf-8')
                    parts = line[:-1].split()
                    if len(parts) != 2:
                        try:
                            ngrams[parts[0]] = i
                        except IndexError:
                            pass # Line probably only contained spaces, if anything
                    else:
                        ngrams[parts[0]] = int(parts[1])
                    i -= 1
            except UnicodeDecodeError, e:
                continue

            if ngrams:
                self.ngrams[lang] = _NGram(ngrams)

        if not count:
            raise ValueError("no language files found")

    def classify(self, text):
        ngram = _NGram(text)
        r = 'guess'

        langs = self.ngrams.keys()
        r = langs.pop()
        min = self.ngrams[r].compare(ngram)

        for lang in langs:
            d = self.ngrams[lang].compare(ngram)
            if d < min:
                min = d
                r = lang

        if min > 0.8 * (nb_ngrams**2):
            r = ''
        return r

class Generate:
    def __init__(self, folder, ext='.txt'):
        self.ngrams = dict()
        folder = os.path.join(folder, '*'+ext)
        size = len(ext)

        for fname in glob.glob(os.path.normcase(folder)):
            lang = os.path.split(fname)[-1][:-size]
            n = _NGram()

            file = open(fname,'r')
            for line in file.readlines():
                n.addText(line)
            file.close()

            n.normalise()
            self.ngrams[lang] = n

    def save(self, folder, ext='.lm'):
        for lang in self.ngrams.keys():
            fname = os.path.join(folder, lang+ext)
            file = open(fname, 'w')
            for v, k in self.ngrams[lang].sorted():
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
    print l.classify(text)
