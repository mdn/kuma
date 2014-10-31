import os

from test_multiprocessing import support, MPTestBase

class TestMPNameError(MPTestBase):
    processes = 2
    suitepath = os.path.join(os.path.dirname(__file__), 'support', 'nameerror.py')

    def runTest(self):
        print str(self.output)
        assert 'NameError' in self.output
        assert "'undefined_variable' is not defined" in self.output

