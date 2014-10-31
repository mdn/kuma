import os
import sys
import unittest

import multiprocessing
from test_multiprocessing import MPTestBase


is_pypy = '__pypy__' in sys.builtin_module_names


class TestConcurrentShared(MPTestBase):
    processes = 2
    suitepath = os.path.join(os.path.dirname(__file__), 'support',
                             'concurrent_shared')

    def setUp(self):
        if is_pypy:
            raise unittest.SkipTest('pypy warm-up is too slow; skipping')

        # Need to call the base's setUp() routine to get the necessary output
        # capturing.
        MPTestBase.setUp(self)

    def runTest(self):
        assert 'Ran 2 tests in 1.' in self.output, "make sure two tests use 1.x seconds (no more than 2 seconds)"
        assert str(self.output).strip().endswith('OK')


class TestConcurrentSharedWithAutomaticProcessesCount(TestConcurrentShared):
    """Make sure negative numbers are handled gracefully."""
    processes = -1

    def setUp(self):
        if multiprocessing.cpu_count() < 2:
            raise unittest.SkipTest(
                    "At least 2 cpus required for this test; skipping")

        TestConcurrentShared.setUp(self)
