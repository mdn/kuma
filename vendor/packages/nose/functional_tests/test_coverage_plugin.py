"""Test the coverage plugin."""
import os
import sys
import unittest
import shutil

from nose.plugins import PluginTester
from nose.plugins.cover import Coverage

support = os.path.join(os.path.dirname(__file__), 'support')

try:
    import coverage

    # Python 3.3 may accidentally pick up our support area when running the unit
    # tests.  Look for the coverage attribute to make sure we've got the right
    # package.
    hasCoverage = hasattr(coverage, 'coverage')
except ImportError:
    hasCoverage = False


class TestCoveragePlugin(PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-html', '--cover-min-percentage', '25']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage')

    def setUp(self):
        if not hasCoverage:
            raise unittest.SkipTest('coverage not available; skipping')

        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        super(TestCoveragePlugin, self).setUp()

    def runTest(self):
        self.assertTrue("blah        4      3    25%   1" in self.output)
        self.assertTrue("Ran 1 test in" in self.output)
        # Assert coverage html report exists
        self.assertTrue(os.path.exists(os.path.join(self.cover_html_dir,
                        'index.html')))
        # Assert coverage data is saved
        self.assertTrue(os.path.exists(self.cover_file))


class TestCoverageMinPercentagePlugin(PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-min-percentage', '100']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage')

    def setUp(self):
        if not hasCoverage:
            raise unittest.SkipTest('coverage not available; skipping')

        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        self.assertRaises(SystemExit,
                          super(TestCoverageMinPercentagePlugin, self).setUp)

    def runTest(self):
        pass


class TestCoverageMinPercentageSinglePackagePlugin(
        PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-html',
            '--cover-min-percentage', '100']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage')

    def setUp(self):
        if not hasCoverage:
            raise unittest.SkipTest('coverage not available; skipping')

        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        self.assertRaises(SystemExit,
                          super(TestCoverageMinPercentageSinglePackagePlugin,
                              self).setUp)

    def runTest(self):
        pass


class TestCoverageMinPercentageSinglePackageWithBranchesPlugin(
        PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-branches',
            '--cover-html', '--cover-min-percentage', '100']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage')

    def setUp(self):
        if not hasCoverage:
            raise unittest.SkipTest('coverage not available; skipping')

        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        self.assertRaises(
                SystemExit,
                super(TestCoverageMinPercentageSinglePackageWithBranchesPlugin,
                    self).setUp)

    def runTest(self):
        pass


class TestCoverageMinPercentageTOTALPlugin(PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-package=moo',
            '--cover-min-percentage', '100']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage2')

    def setUp(self):
        if not hasCoverage:
            raise unittest.SkipTest('coverage not available; skipping')

        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        self.assertRaises(SystemExit,
                          super(TestCoverageMinPercentageTOTALPlugin, self).setUp)

    def runTest(self):
        pass


class TestCoverageMinPercentageWithBranchesTOTALPlugin(
        PluginTester, unittest.TestCase):
    activate = "--with-coverage"
    args = ['-v', '--cover-package=blah', '--cover-package=moo',
            '--cover-branches', '--cover-min-percentage', '100']
    plugins = [Coverage()]
    suitepath = os.path.join(support, 'coverage2')

    def setUp(self):
        if not hasCoverage:
            raise unittest.SkipTest('coverage not available; skipping')

        self.cover_file = os.path.join(os.getcwd(), '.coverage')
        self.cover_html_dir = os.path.join(os.getcwd(), 'cover')
        if os.path.exists(self.cover_file):
            os.unlink(self.cover_file)
        if os.path.exists(self.cover_html_dir):
            shutil.rmtree(self.cover_html_dir)
        self.assertRaises(
                SystemExit,
                super(TestCoverageMinPercentageWithBranchesTOTALPlugin, self).setUp)

    def runTest(self):
        pass

if __name__ == '__main__':
    unittest.main()
