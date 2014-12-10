import unittest
import os
from nose import main
import sys
import re
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

support = os.path.join(os.path.dirname(__file__), 'support')

expected_output_pattern = """KeyError: '?fake'?\n-+ >> begin captured stdout << -+\nsomething\n"""

class TestIssue135(unittest.TestCase):
    def test_issue135(self):
        wd = os.path.join(support, 'issue135')
        stringio = StringIO()
        old_argv = sys.argv
        old_stderr = sys.stderr
        sys.stderr = stringio
        sys.argv = ["nosetests", wd]
        try:
            main(exit=False)
        finally:
            sys.argv = old_argv
            sys.stderr = old_stderr
        stringio.seek(0)
        output = stringio.read()
        self.assertTrue(re.search(expected_output_pattern, output) is not None)

if __name__ == '__main__':
    unittest.main()
