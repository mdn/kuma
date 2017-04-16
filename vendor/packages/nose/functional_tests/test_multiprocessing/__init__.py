import os
from unittest import TestCase

from nose.plugins import PluginTester
from nose.plugins.skip import SkipTest
from nose.plugins.multiprocess import MultiProcess

support = os.path.join(os.path.dirname(__file__), 'support')

def setup():
    try:
        import multiprocessing
        if 'active' in MultiProcess.status:
            raise SkipTest("Multiprocess plugin is active. Skipping tests of "
                           "plugin itself.")
    except ImportError:
        raise SkipTest("multiprocessing module not available")

class MPTestBase(PluginTester, TestCase):
    processes = 1
    activate = '--processes=1'
    plugins = [MultiProcess()]
    suitepath = os.path.join(support, 'timeout.py')

    def __init__(self, *args, **kwargs):
        self.activate = '--processes=%d' % self.processes
        PluginTester.__init__(self)
        TestCase.__init__(self, *args, **kwargs)
