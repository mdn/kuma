# encoding: utf-8
"""
Test the output capture at the OS level, using file descriptors.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Tell nose to skip this module
__test__ = {}

from cStringIO import StringIO
import os

from twisted.trial import unittest

from IPython.testing import decorators_trial as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


class TestRedirector(unittest.TestCase):

    @dec.skip_win32
    def test_redirector(self):
        """Checks that the redirector can be used to do synchronous capture.
        """
        from IPython.kernel.core.fd_redirector import FDRedirector
        r = FDRedirector()
        out = StringIO()
        try:
            r.start()
            for i in range(10):
                os.system('echo %ic' % i)
                print >>out, r.getvalue(),
                print >>out, i
        except:
            r.stop()
            raise
        r.stop()
        result1 = out.getvalue()
        result2 = "".join("%ic\n%i\n" %(i, i) for i in range(10))
        self.assertEquals(result1, result2)

    @dec.skip_win32
    def test_redirector_output_trap(self):
        """Check the greedy trapping behavior of the traps.
        
        This test check not only that the redirector_output_trap does
        trap the output, but also that it does it in a gready way, that
        is by calling the callback ASAP.
        """
        from IPython.kernel.core.redirector_output_trap import RedirectorOutputTrap
        out = StringIO()
        trap = RedirectorOutputTrap(out.write, out.write)
        try:
            trap.set()
            for i in range(10):
                os.system('echo %ic' % i)
                print "%ip" % i
                print >>out, i
        except:
            trap.unset()
            raise
        trap.unset()
        result1 = out.getvalue()
        result2 = "".join("%ic\n%ip\n%i\n" %(i, i, i) for i in range(10))
        self.assertEquals(result1, result2)

