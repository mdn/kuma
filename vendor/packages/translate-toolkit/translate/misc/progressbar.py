#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004, 2005 Zuza Software Foundation
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

"""progress bar utilities for reporting feedback on progress of application..."""

class DotsProgressBar:
    """an ultra-simple progress indicator that just writes a dot for each action"""
    def __init__(self):
        import sys
        self.stderr = sys.stderr
        self.amount = 0

    def show(self, verbosemessage):
        """show a dot for progress :-)"""
        self.stderr.write('.')
        self.stderr.flush()

    def close(self):
        self.stderr.write('\n')
        self.stderr.flush()

    def __del__(self):
        self.close()

class NoProgressBar:
    """an invisible indicator that does nothing..."""
    def __init__(self):
        self.amount = 0

    def show(self, verbosemessage):
        """show nothing for progress :-)"""
        pass

    def close(self):
        pass

class ProgressBar:
    """a plain progress bar that doesn't know very much about output..."""
    def __init__(self, minValue = 0, maxValue = 100, totalWidth=50):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.width = totalWidth
        self.amount = 0       # When amount == max, we are 100% done 

    def __str__(self):
        """produces the string representing the progress bar"""
        if self.amount < self.min: self.amount = self.min
        if self.amount > self.max: self.amount = self.max

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 7 
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[%s%s] %3d%%" % ('#'*numHashes, ' '*(allFull-numHashes), percentDone)
        return str(self.progBar)

    def show(self, verbosemessage):
        """displays the progress bar"""
        print self

class MessageProgressBar(ProgressBar):
    """a ProgressBar that just writes out the messages without any progress display"""
    def __init__(self, *args, **kwargs):
        import sys
        self.sys = sys
        ProgressBar.__init__(self, *args, **kwargs)

    def show(self, verbosemessage):
        self.sys.stderr.write(verbosemessage + '\n')
        self.sys.stderr.flush()

class HashProgressBar(ProgressBar):
    """a ProgressBar which knows how to go back to the beginning of the line..."""
    def __init__(self, *args, **kwargs):
        import sys
        self.sys = sys
        ProgressBar.__init__(self, *args, **kwargs)

    def show(self, verbosemessage):
        self.sys.stderr.write(str(self) + '\r')
        self.sys.stderr.flush()

    def close(self):
        self.sys.stderr.write('\n')
        self.sys.stderr.flush()

    def __del__(self):
        self.close()

class VerboseProgressBar(HashProgressBar):
    def __init__(self, *args, **kwargs):
        self.lastwidth = 0
        HashProgressBar.__init__(self, *args, **kwargs)

    def show(self, verbosemessage):
        output = str(self)
        self.sys.stderr.write('\r' + ' '*self.lastwidth)
        self.sys.stderr.write('\r' + verbosemessage + '\n')
        self.lastwidth = len(output)
        self.sys.stderr.write('\r' + output)
        self.sys.stderr.flush()

def test(progressbar):
    import time
    for n in range(progressbar.min, progressbar.max+1, 5):
        progressbar.amount = n
        progressbar.show("Some message")
        time.sleep(0.2)

if __name__ == '__main__':
    p = HashProgressBar(0,100,50)
    test(p)

