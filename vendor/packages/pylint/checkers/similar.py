# pylint: disable-msg=W0622
# Copyright (c) 2004-2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""a similarities / code duplication command line tool and pylint checker
"""
from __future__ import generators

__revision__ = '$Id: similar.py,v 1.14 2006-03-29 08:24:32 syt Exp $'

import sys

from logilab.common.compat import set, izip, sum, enumerate
from logilab.common.ureports import Table

from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker, table_lines_from_stats


class Similar:
    """finds copy-pasted lines of code in a project"""
    
    def __init__(self, min_lines=4, ignore_comments=False,
                 ignore_docstrings=False):
        self.min_lines = min_lines
        self.ignore_comments = ignore_comments
        self.ignore_docstrings = ignore_docstrings
        self.linesets = []

    def append_stream(self, streamid, stream):
        """append a file to search for similarities"""
        self.linesets.append(LineSet(streamid,
                                     stream.readlines(),
                                     self.ignore_comments,
                                     self.ignore_docstrings))
        
    def run(self):
        """start looking for similarities and display results on stdout"""
        self._display_sims(self._compute_sims())
        
    def _compute_sims(self):
        """compute similarities in appended files"""
        no_duplicates = {}
        for num, lineset1, idx1, lineset2, idx2 in self._iter_sims():
            duplicate = no_duplicates.setdefault(num, [])
            for couples in duplicate:
                if (lineset1, idx1) in couples or (lineset2, idx2) in couples:
                    couples.add( (lineset1, idx1) )
                    couples.add( (lineset2, idx2) )
                    break
            else:
                duplicate.append( set([(lineset1, idx1), (lineset2, idx2)]) )
        sims = []
        for num, ensembles in no_duplicates.iteritems():
            for couples in ensembles:
                sims.append( (num, couples) )
        sims.sort()
        sims.reverse()
        return sims
    
    def _display_sims(self, sims):
        """display computed similarities on stdout"""
        nb_lignes_dupliquees = 0
        for num, couples in sims:
            print 
            print num, "similar lines in", len(couples), "files"
            couples = list(couples)
            couples.sort()
            for lineset, idx in couples:
                print "==%s:%s" % (lineset.name, idx)
            # pylint: disable-msg=W0631
            for line in lineset._real_lines[idx:idx+num]:
                print "  ", line,
            nb_lignes_dupliquees += num * (len(couples)-1)
        nb_total_lignes = sum([len(lineset) for lineset in self.linesets])
        print "TOTAL lines=%s duplicates=%s percent=%s" \
            % (nb_total_lignes, nb_lignes_dupliquees,
               nb_lignes_dupliquees*1. / nb_total_lignes)

    def _find_common(self, lineset1, lineset2):
        """find similarities in the two given linesets"""
        lines1 = lineset1.enumerate_stripped
        lines2 = lineset2.enumerate_stripped
        find = lineset2.find
        index1 = 0
        min_lines = self.min_lines
        while index1 < len(lineset1):
            skip = 1
            num = 0
            for index2 in find( lineset1[index1] ):
                non_blank = 0
                for num, ((_, line1), (_, line2)) in enumerate(
                    izip(lines1(index1), lines2(index2))):
                    if line1 != line2:
                        if non_blank > min_lines:
                            yield num, lineset1, index1, lineset2, index2
                        skip = max(skip, num)
                        break
                    if line1:
                        non_blank += 1
                else:
                    # we may have reach the end
                    num += 1
                    if non_blank > min_lines:
                        yield num, lineset1, index1, lineset2, index2
                    skip = max(skip, num)
            index1 += skip
        
    def _iter_sims(self):
        """iterate on similarities among all files, by making a cartesian
        product
        """
        for idx, lineset in enumerate(self.linesets[:-1]):
            for lineset2 in self.linesets[idx+1:]:
                for sim in self._find_common(lineset, lineset2):
                    yield sim

def stripped_lines(lines, ignore_comments, ignore_docstrings):
    strippedlines = []
    docstring = None
    for line in lines:
        line = line.strip()
        if ignore_docstrings:
            if not docstring and \
                   (line.startswith('"""') or line.startswith("'''")):
                docstring = line[:3]
                line = line[3:]
            if docstring:
                if line.endswith(docstring):
                    docstring = None
                line = ''
        # XXX cut when a line begins with code but end with a comment
        if ignore_comments and line.startswith('#'):
            line = ''
        strippedlines.append(line)
    return strippedlines

class LineSet:
    """Holds and indexes all the lines of a single source file"""
    def __init__(self, name, lines, ignore_comments=False,
                 ignore_docstrings=False):
        self.name = name
        self._real_lines = lines
        self._stripped_lines = stripped_lines(lines, ignore_comments,
                                              ignore_docstrings)
        self._index = self._mk_index()
            
    def __str__(self):
        return '<Lineset for %s>' % self.name

    def __len__(self):
        return len(self._real_lines)

    def __getitem__(self, index):
        return self._stripped_lines[index]

    def __cmp__(self, other):
        return cmp(self.name, other.name)
    
    def __hash__(self):
        return id(self)
    
    def enumerate_stripped(self, start_at=0):
        """return an iterator on stripped lines, starting from a given index
        if specified, else 0
        """
        idx = start_at
        if start_at:
            lines = self._stripped_lines[start_at:]
        else:
            lines = self._stripped_lines
        for line in lines:
            #if line:
            yield idx, line
            idx += 1

    def find(self, stripped_line):
        """return positions of the given stripped line in this set"""
        return self._index.get(stripped_line, ())
    
    def _mk_index(self):
        """create the index for this set"""
        index = {}
        for line_no, line in enumerate(self._stripped_lines):
            if line:
                index.setdefault(line, []).append( line_no )
        return index


MSGS = {'R0801': ('Similar lines in %s files\n%s',
                  'Indicates that a set of similar lines has been detected \
                  among multiple file. This usually means that the code should \
                  be refactored to avoid this duplication.')}

def report_similarities(sect, stats, old_stats):
    """make a layout with some stats about duplication"""
    lines = ['', 'now', 'previous', 'difference']
    lines += table_lines_from_stats(stats, old_stats,
                                    ('nb_duplicated_lines',
                                     'percent_duplicated_lines'))
    sect.append(Table(children=lines, cols=4, rheaders=1, cheaders=1))


# wrapper to get a pylint checker from the similar class
class SimilarChecker(BaseChecker, Similar):
    """checks for similarities and duplicated code. This computation may be
    memory / CPU intensive, so you should disable it if you experiments some
    problems.
    """
    
    __implements__ = (IRawChecker,)
    # configuration section name
    name = 'similarities'
    # messages
    msgs = MSGS
    # configuration options
    # for available dict keys/values see the optik parser 'add_option' method
    options = (('min-similarity-lines',
                {'default' : 4, 'type' : "int", 'metavar' : '<int>',
                 'help' : 'Minimum lines number of a similarity.'}),
               ('ignore-comments',
                {'default' : True, 'type' : 'yn', 'metavar' : '<y or n>',
                 'help': 'Ignore comments when computing similarities.'}
                ),
               ('ignore-docstrings',
                {'default' : True, 'type' : 'yn', 'metavar' : '<y or n>',
                 'help': 'Ignore docstrings when computing similarities.'}
                ),
               )
    # reports
    reports = ( ('R0801', 'Duplication', report_similarities), )
    
    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)
        Similar.__init__(self, min_lines=4,
                         ignore_comments=True, ignore_docstrings=True)
        self.stats = None

    def set_option(self, opt_name, value, action=None, opt_dict=None):
        """method called to set an option (registered in the options list)

        overridden to report options setting to Similar
        """
        BaseChecker.set_option(self, opt_name, value, action, opt_dict)
        if opt_name == 'min-similarity-lines':
            self.min_lines = self.config.min_similarity_lines
        elif opt_name == 'ignore-comments':
            self.ignore_comments = self.config.ignore_comments
        elif opt_name == 'ignore-docstrings':
            self.ignore_docstrings = self.config.ignore_docstrings
        
    def open(self):
        """init the checkers: reset linesets and statistics information"""
        self.linesets = []
        self.stats = self.linter.add_stats(nb_duplicated_lines=0,
                                           percent_duplicated_lines=0)
        
    def process_module(self, stream):
        """process a module
        
        the module's content is accessible via the stream object
        
        stream must implements the readlines method
        """
        self.append_stream(self.linter.current_name, stream)

    def close(self):
        """compute and display similarities on closing (i.e. end of parsing)"""
        total = sum([len(lineset) for lineset in self.linesets])
        duplicated = 0
        stats = self.stats
        for num, couples in self._compute_sims():
            msg = []
            for lineset, idx in couples:
                msg.append("==%s:%s" % (lineset.name, idx))
            msg.sort()
            # pylint: disable-msg=W0631
            for line in lineset._real_lines[idx:idx+num]:
                msg.append(line.rstrip())
            self.add_message('R0801', args=(len(couples), '\n'.join(msg)))
            duplicated += num * (len(couples) - 1)
        stats['nb_duplicated_lines'] = duplicated
        stats['percent_duplicated_lines'] = total and duplicated * 100. / total
        

def register(linter):
    """required method to auto register this checker """
    linter.register_checker(SimilarChecker(linter))

def usage(status=0):
    """display command line usage information"""
    print "finds copy pasted blocks in a set of files"
    print
    print 'Usage: similar [-d|--duplicates min_duplicated_lines] \
[--ignore-comments] file1...'
    sys.exit(status)
    
def run(argv=None):
    """standalone command line access point"""
    if argv is None:
        argv = sys.argv[1:]
    from getopt import getopt
    s_opts = 'hd:'
    l_opts = ('help', 'duplicates=', 'ignore-comments')
    min_lines = 4
    ignore_comments = False
    opts, args = getopt(argv, s_opts, l_opts)
    for opt, val in opts:
        if opt in ('-d', '--duplicates'):
            min_lines = int(val)
        elif opt in ('-h', '--help'):
            usage()
        elif opt == '--ignore-comments':
            ignore_comments = True
    if not args:
        usage(1)
    sim = Similar(min_lines, ignore_comments)
    for filename in args:
        sim.append_stream(filename, open(filename))
    sim.run()

if __name__ == '__main__':
    run()
