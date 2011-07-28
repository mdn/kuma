import test_utils
from nose.plugins.skip import SkipTest

class SkippedTestCase(test_utils.TestCase):
    def setUp(self):
        raise SkipTest()
