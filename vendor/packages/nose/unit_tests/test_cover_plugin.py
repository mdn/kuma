import sys
from optparse import OptionParser
from nose.config import Config
from nose.plugins.cover import Coverage
from nose.tools import eq_
import unittest

class TestCoveragePlugin(object):

    def test_cover_packages_option(self):
        parser = OptionParser()
        c = Coverage()
        c.addOptions(parser)
        options, args = parser.parse_args(['test_can_be_disabled',
                                           '--cover-package=pkg1,pkg2,pkg3'])
        c.configure(options, Config())
        eq_(['pkg1', 'pkg2', 'pkg3'], c.coverPackages)

        env = {'NOSE_COVER_PACKAGE': 'pkg1,pkg2,pkg3'}
        c = Coverage()
        parser = OptionParser()
        c.addOptions(parser, env)
        options, args = parser.parse_args(['test_can_be_disabled'])
        c.configure(options, Config())
        eq_(['pkg1', 'pkg2', 'pkg3'], c.coverPackages)
