# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""unit tests for logilab.common.fileutils"""

import sys, os, tempfile, shutil
from os.path import join

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.fileutils import *


DATA_DIR = 'data'
NEWLINES_TXT = join(DATA_DIR,'newlines.txt')

class FirstleveldirectoryTC(TestCase):

    def test_known_values_first_level_directory(self):
        """return the first level directory of a path"""
        self.assertEqual(first_level_directory('truc/bidule/chouette'), 'truc', None)
        self.assertEqual(first_level_directory('/truc/bidule/chouette'), '/', None)

class IsBinaryTC(TestCase):
    def test(self):
        self.assertEqual(is_binary('toto.txt'), 0)
        #self.assertEqual(is_binary('toto.xml'), 0)
        self.assertEqual(is_binary('toto.bin'), 1)
        self.assertEqual(is_binary('toto.sxi'), 1)
        self.assertEqual(is_binary('toto.whatever'), 1)

class GetModeTC(TestCase):
    def test(self):
        self.assertEqual(write_open_mode('toto.txt'), 'w')
        #self.assertEqual(write_open_mode('toto.xml'), 'w')
        self.assertEqual(write_open_mode('toto.bin'), 'wb')
        self.assertEqual(write_open_mode('toto.sxi'), 'wb')

class NormReadTC(TestCase):
    def test_known_values_norm_read(self):
        data = norm_read(NEWLINES_TXT)
        self.assertEqual(data.strip(), '\n'.join(['# mixed new lines', '1', '2', '3']))


class LinesTC(TestCase):
    def test_known_values_lines(self):
        self.assertEqual(lines(NEWLINES_TXT),
                         ['# mixed new lines', '1', '2', '3'])

    def test_known_values_lines_comment(self):
        self.assertEqual(lines(NEWLINES_TXT, comments='#'),
                         ['1', '2', '3'])

class ExportTC(TestCase):
    def setUp(self):
        self.tempdir = tempfile.mktemp()
        os.mkdir(self.tempdir)

    def test(self):
        export('data', self.tempdir, verbose=0)
        self.assert_(exists(join(self.tempdir, '__init__.py')))
        self.assert_(exists(join(self.tempdir, 'sub')))
        self.assert_(not exists(join(self.tempdir, '__init__.pyc')))
        self.assert_(not exists(join(self.tempdir, 'CVS')))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

class ProtectedFileTC(TestCase):
    def setUp(self):
        self.rpath = 'data/write_protected_file.txt'
        self.rwpath = 'data/normal_file.txt'
        # Make sure rpath is not writable !
        os.chmod(self.rpath, 33060)
        # Make sure rwpath is writable !
        os.chmod(self.rwpath, 33188)

    def test_mode_change(self):
        """tests that mode is changed when needed"""
        # test on non-writable file
        self.assert_(not os.access(self.rpath, os.W_OK))
        wp_file = ProtectedFile(self.rpath, 'w')
        self.assert_(os.access(self.rpath, os.W_OK))
        # test on writable-file
        self.assert_(os.access(self.rwpath, os.W_OK))
        wp_file = ProtectedFile(self.rwpath, 'w')
        self.assert_(os.access(self.rwpath, os.W_OK))

    def test_restore_on_close(self):
        """tests original mode is restored on close"""
        # test on non-writable file
        self.assert_(not os.access(self.rpath, os.W_OK))
        ProtectedFile(self.rpath, 'w').close()
        self.assert_(not os.access(self.rpath, os.W_OK))
        # test on writable-file
        self.assert_(os.access(self.rwpath, os.W_OK))
        ProtectedFile(self.rwpath, 'w').close()
        self.assert_(os.access(self.rwpath, os.W_OK))

    def test_mode_change_on_append(self):
        """tests that mode is changed when file is opened in 'a' mode"""
        self.assert_(not os.access(self.rpath, os.W_OK))
        wp_file = ProtectedFile(self.rpath, 'a')
        self.assert_(os.access(self.rpath, os.W_OK))
        wp_file.close()
        self.assert_(not os.access(self.rpath, os.W_OK))


from logilab.common.testlib import DocTest
class ModuleDocTest(DocTest):
    """relative_path embed tests in docstring"""
    from logilab.common import fileutils as module
    skipped = ('abspath_listdir',)


del DocTest # necessary if we don't want it to be executed (we don't...)

if __name__ == '__main__':
    unittest_main()
