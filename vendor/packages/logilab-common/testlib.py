# -*- coding: utf-8 -*-
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
"""Run tests.

This will find all modules whose name match a given prefix in the test
directory, and run them. Various command line options provide
additional facilities.

Command line options:

 -v  verbose -- run tests in verbose mode with output to stdout
 -q  quiet   -- don't print anything except if a test fails
 -t  testdir -- directory where the tests will be found
 -x  exclude -- add a test to exclude
 -p  profile -- profiled execution
 -c  capture -- capture standard out/err during tests
 -d  dbc     -- enable design-by-contract
 -m  match   -- only run test matching the tag pattern which follow

If no non-option arguments are present, prefixes used are 'test',
'regrtest', 'smoketest' and 'unittest'.

"""
__docformat__ = "restructuredtext en"
# modified copy of some functions from test/regrtest.py from PyXml
# disable camel case warning
# pylint: disable-msg=C0103

import sys
import os, os.path as osp
import re
import time
import getopt
import traceback
import inspect
import unittest
import difflib
import types
import tempfile
import math
from shutil import rmtree
from operator import itemgetter
import warnings
from compiler.consts import CO_GENERATOR
from ConfigParser import ConfigParser
from itertools import dropwhile
from functools import wraps

try:
    from test import test_support
except ImportError:
    # not always available
    class TestSupport:
        def unload(self, test):
            pass
    test_support = TestSupport()

# pylint: disable-msg=W0622
from logilab.common.compat import set, enumerate, any, sorted
# pylint: enable-msg=W0622
from logilab.common.modutils import load_module_from_name
from logilab.common.debugger import Debugger, colorize_source
from logilab.common.decorators import cached, classproperty
from logilab.common import textutils


__all__ = ['main', 'unittest_main', 'find_tests', 'run_test', 'spawn']

DEFAULT_PREFIXES = ('test', 'regrtest', 'smoketest', 'unittest',
                    'func', 'validation')

ENABLE_DBC = False

FILE_RESTART = ".pytest.restart"

# used by unittest to count the number of relevant levels in the traceback
__unittest = 1


def with_tempdir(callable):
    """A decorator ensuring no temporary file left when the function return
    Work only for temporary file create with the tempfile module"""
    @wraps(callable)
    def proxy(*args, **kargs):

        old_tmpdir = tempfile.gettempdir()
        new_tmpdir = tempfile.mkdtemp(prefix="temp-lgc-")
        tempfile.tempdir = new_tmpdir
        try:
            return callable(*args, **kargs)
        finally:
            try:
                rmtree(new_tmpdir, ignore_errors=True)
            finally:
                tempfile.tempdir = old_tmpdir
    return proxy

def in_tempdir(callable):
    """A decorator moving the enclosed function inside the tempfile.tempfdir
    """
    @wraps(callable)
    def proxy(*args, **kargs):

        old_cwd = os.getcwd()
        os.chdir(tempfile.tempdir)
        try:
            return callable(*args, **kargs)
        finally:
            os.chdir(old_cwd)
    return proxy

def within_tempdir(callable):
    """A decorator run the enclosed function inside a tmpdir removed after execution
    """
    proxy = with_tempdir(in_tempdir(callable))
    proxy.__name__ = callable.__name__
    return proxy

def run_tests(tests, quiet, verbose, runner=None, capture=0):
    """Execute a list of tests.

    :rtype: tuple
    :return: tuple (list of passed tests, list of failed tests, list of skipped tests)
    """
    good = []
    bad = []
    skipped = []
    all_result = None
    for test in tests:
        if not quiet:
            print
            print '-'*80
            print "Executing", test
        result = run_test(test, verbose, runner, capture)
        if type(result) is type(''):
            # an unexpected error occurred
            skipped.append( (test, result))
        else:
            if all_result is None:
                all_result = result
            else:
                all_result.testsRun += result.testsRun
                all_result.failures += result.failures
                all_result.errors += result.errors
                all_result.skipped += result.skipped
            if result.errors or result.failures:
                bad.append(test)
                if verbose:
                    print "test", test, \
                          "failed -- %s errors, %s failures" % (
                        len(result.errors), len(result.failures))
            else:
                good.append(test)

    return good, bad, skipped, all_result

def find_tests(testdir,
               prefixes=DEFAULT_PREFIXES, suffix=".py",
               excludes=(),
               remove_suffix=True):
    """
    Return a list of all applicable test modules.
    """
    tests = []
    for name in os.listdir(testdir):
        if not suffix or name.endswith(suffix):
            for prefix in prefixes:
                if name.startswith(prefix):
                    if remove_suffix and name.endswith(suffix):
                        name = name[:-len(suffix)]
                    if name not in excludes:
                        tests.append(name)
    tests.sort()
    return tests


def run_test(test, verbose, runner=None, capture=0):
    """
    Run a single test.

    test -- the name of the test
    verbose -- if true, print more messages
    """
    test_support.unload(test)
    try:
        m = load_module_from_name(test, path=sys.path)
#        m = __import__(test, globals(), locals(), sys.path)
        try:
            suite = m.suite
            if callable(suite):
                suite = suite()
        except AttributeError:
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(m)
        if runner is None:
            runner = SkipAwareTextTestRunner(capture=capture) # verbosity=0)
        return runner.run(suite)
    except KeyboardInterrupt, v:
        raise KeyboardInterrupt, v, sys.exc_info()[2]
    except:
        # raise
        type, value = sys.exc_info()[:2]
        msg = "test %s crashed -- %s : %s" % (test, type, value)
        if verbose:
            traceback.print_exc()
        return msg

def _count(n, word):
    """format word according to n"""
    if n == 1:
        return "%d %s" % (n, word)
    else:
        return "%d %ss" % (n, word)




## PostMortem Debug facilities #####
def start_interactive_mode(result):
    """starts an interactive shell so that the user can inspect errors
    """
    debuggers = result.debuggers
    descrs = result.error_descrs + result.fail_descrs
    if len(debuggers) == 1:
        # don't ask for test name if there's only one failure
        debuggers[0].start()
    else:
        while True:
            testindex = 0
            print "Choose a test to debug:"
            # order debuggers in the same way than errors were printed
            print "\n".join(['\t%s : %s' % (i, descr) for i, (_, descr)
                in enumerate(descrs)])
            print "Type 'exit' (or ^D) to quit"
            print
            try:
                todebug = raw_input('Enter a test name: ')
                if todebug.strip().lower() == 'exit':
                    print
                    break
                else:
                    try:
                        testindex = int(todebug)
                        debugger = debuggers[descrs[testindex][0]]
                    except (ValueError, IndexError):
                        print "ERROR: invalid test number %r" % (todebug, )
                    else:
                        debugger.start()
            except (EOFError, KeyboardInterrupt):
                print
                break


# test utils ##################################################################
from cStringIO import StringIO

class SkipAwareTestResult(unittest._TextTestResult):

    def __init__(self, stream, descriptions, verbosity,
                 exitfirst=False, capture=0, printonly=None,
                 pdbmode=False, cvg=None, colorize=False):
        super(SkipAwareTestResult, self).__init__(stream,
                                                  descriptions, verbosity)
        self.skipped = []
        self.debuggers = []
        self.fail_descrs = []
        self.error_descrs = []
        self.exitfirst = exitfirst
        self.capture = capture
        self.printonly = printonly
        self.pdbmode = pdbmode
        self.cvg = cvg
        self.colorize = colorize
        self.pdbclass = Debugger
        self.verbose = verbosity > 1

    def descrs_for(self, flavour):
        return getattr(self, '%s_descrs' % flavour.lower())

    def _create_pdb(self, test_descr, flavour):
        self.descrs_for(flavour).append( (len(self.debuggers), test_descr) )
        if self.pdbmode:
            self.debuggers.append(self.pdbclass(sys.exc_info()[2]))


    def _iter_valid_frames(self, frames):
        """only consider non-testlib frames when formatting  traceback"""
        lgc_testlib = osp.abspath(__file__)
        std_testlib = osp.abspath(unittest.__file__)
        invalid = lambda fi: osp.abspath(fi[1]) in (lgc_testlib, std_testlib)
        for frameinfo in dropwhile(invalid, frames):
            yield frameinfo

    def _exc_info_to_string(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string.

        This method is overridden here because we want to colorize
        lines if --color is passed, and display local variables if
        --verbose is passed
        """
        exctype, exc, tb = err
        output = ['Traceback (most recent call last)']
        frames = inspect.getinnerframes(tb)
        colorize = self.colorize
        frames = enumerate(self._iter_valid_frames(frames))
        for index, (frame, filename, lineno, funcname, ctx, ctxindex) in frames:
            filename = osp.abspath(filename)
            if ctx is None: # pyc files or C extensions for instance
                source = '<no source available>'
            else:
                source = ''.join(ctx)
            if colorize:
                filename = textutils.colorize_ansi(filename, 'magenta')
                source = colorize_source(source)
            output.append('  File "%s", line %s, in %s' % (filename, lineno, funcname))
            output.append('    %s' % source.strip())
            if self.verbose:
                output.append('%r == %r' % (dir(frame), test.__module__))
                output.append('')
                output.append('    ' + ' local variables '.center(66, '-'))
                for varname, value in sorted(frame.f_locals.items()):
                    output.append('    %s: %r' % (varname, value))
                    if varname == 'self': # special handy processing for self
                        for varname, value in sorted(vars(value).items()):
                            output.append('      self.%s: %r' % (varname, value))
                output.append('    ' + '-' * 66)
                output.append('')
        output.append(''.join(traceback.format_exception_only(exctype, exc)))
        return '\n'.join(output)

    def addError(self, test, err):
        """err ==  (exc_type, exc, tcbk)"""
        exc_type, exc, _ = err #
        if exc_type == TestSkipped:
            self.addSkipped(test, exc)
        else:
            if self.exitfirst:
                self.shouldStop = True
            descr = self.getDescription(test)
            super(SkipAwareTestResult, self).addError(test, err)
            self._create_pdb(descr, 'error')

    def addFailure(self, test, err):
        if self.exitfirst:
            self.shouldStop = True
        descr = self.getDescription(test)
        super(SkipAwareTestResult, self).addFailure(test, err)
        self._create_pdb(descr, 'fail')

    def addSkipped(self, test, reason):
        self.skipped.append((test, self.getDescription(test), reason))
        if self.showAll:
            self.stream.writeln("SKIPPED")
        elif self.dots:
            self.stream.write('S')

    def printErrors(self):
        super(SkipAwareTestResult, self).printErrors()
        self.printSkippedList()

    def printSkippedList(self):
        for _, descr, err in self.skipped: # test, descr, err
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % ('SKIPPED', descr))
            self.stream.writeln("\t%s" % err)

    def printErrorList(self, flavour, errors):
        for (_, descr), (test, err) in zip(self.descrs_for(flavour), errors):
            self.stream.writeln(self.separator1)
            if self.colorize:
                self.stream.writeln("%s: %s" % (
                    textutils.colorize_ansi(flavour, color='red'), descr))
            else:
                self.stream.writeln("%s: %s" % (flavour, descr))

            self.stream.writeln(self.separator2)
            self.stream.writeln(err)
            try:
                output, errput = test.captured_output()
            except AttributeError:
                pass # original unittest
            else:
                if output:
                    self.stream.writeln(self.separator2)
                    self.stream.writeln("captured stdout".center(
                        len(self.separator2)))
                    self.stream.writeln(self.separator2)
                    self.stream.writeln(output)
                else:
                    self.stream.writeln('no stdout'.center(
                        len(self.separator2)))
                if errput:
                    self.stream.writeln(self.separator2)
                    self.stream.writeln("captured stderr".center(
                        len(self.separator2)))
                    self.stream.writeln(self.separator2)
                    self.stream.writeln(errput)
                else:
                    self.stream.writeln('no stderr'.center(
                        len(self.separator2)))


def run(self, result, runcondition=None, options=None):
    for test in self._tests:
        if result.shouldStop:
            break
        try:
            test(result, runcondition, options)
        except TypeError:
            # this might happen if a raw unittest.TestCase is defined
            # and used with python (and not pytest)
            warnings.warn("%s should extend lgc.testlib.TestCase instead of unittest.TestCase"
                 % test)
            test(result)
    return result
unittest.TestSuite.run = run

# backward compatibility: TestSuite might be imported from lgc.testlib
TestSuite = unittest.TestSuite

# python2.3 compat
def __call__(self, *args, **kwds):
    return self.run(*args, **kwds)
unittest.TestSuite.__call__ = __call__


class SkipAwareTextTestRunner(unittest.TextTestRunner):

    def __init__(self, stream=sys.stderr, verbosity=1,
                 exitfirst=False, capture=False, printonly=None,
                 pdbmode=False, cvg=None, test_pattern=None,
                 skipped_patterns=(), colorize=False, batchmode=False,
                 options=None):
        super(SkipAwareTextTestRunner, self).__init__(stream=stream,
                                                      verbosity=verbosity)
        self.exitfirst = exitfirst
        self.capture = capture
        self.printonly = printonly
        self.pdbmode = pdbmode
        self.cvg = cvg
        self.test_pattern = test_pattern
        self.skipped_patterns = skipped_patterns
        self.colorize = colorize
        self.batchmode = batchmode
        self.options = options

    def _this_is_skipped(self, testedname):
        return any([(pat in testedname) for pat in self.skipped_patterns])

    def _runcondition(self, test, skipgenerator=True):
        if isinstance(test, InnerTest):
            testname = test.name
        else:
            if isinstance(test, TestCase):
                meth = test._get_test_method()
                func = meth.im_func
                testname = '%s.%s' % (meth.im_class.__name__, func.__name__)
            elif isinstance(test, types.FunctionType):
                func = test
                testname = func.__name__
            elif isinstance(test, types.MethodType):
                func = test.im_func
                testname = '%s.%s' % (test.im_class.__name__, func.__name__)
            else:
                return True # Not sure when this happens

            if is_generator(func) and skipgenerator:
                return self.does_match_tags(func) # Let inner tests decide at run time

        # print 'testname', testname, self.test_pattern
        if self._this_is_skipped(testname):
            return False # this was explicitly skipped
        if self.test_pattern is not None:
            try:
                classpattern, testpattern = self.test_pattern.split('.')
                klass, name = testname.split('.')
                if classpattern not in klass or testpattern not in name:
                    return False
            except ValueError:
                if self.test_pattern not in testname:
                    return False

        return self.does_match_tags(test)

    def does_match_tags(self, test):
        if self.options is not None:
            tags_pattern = getattr(self.options, 'tags_pattern', None)
            if tags_pattern is not None:
                tags = getattr(test, 'tags', None)
                if tags is not None:
                    return tags.match(tags_pattern)
                if isinstance(test, types.MethodType):
                    tags = getattr(test.im_class, 'tags', Tags())
                    return tags.match(tags_pattern)
                return False
        return True # no pattern

    def _makeResult(self):
        return SkipAwareTestResult(self.stream, self.descriptions,
                                   self.verbosity, self.exitfirst, self.capture,
                                   self.printonly, self.pdbmode, self.cvg,
                                   self.colorize)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        startTime = time.time()
        test(result, self._runcondition, self.options)
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        if not self.batchmode:
            self.stream.writeln(result.separator2)
            run = result.testsRun
            self.stream.writeln("Ran %d test%s in %.3fs" %
                                (run, run != 1 and "s" or "", timeTaken))
            self.stream.writeln()
            if not result.wasSuccessful():
                if self.colorize:
                    self.stream.write(textutils.colorize_ansi("FAILED", color='red'))
                else:
                    self.stream.write("FAILED")
            else:
                if self.colorize:
                    self.stream.write(textutils.colorize_ansi("OK", color='green'))
                else:
                    self.stream.write("OK")
            failed, errored, skipped = map(len, (result.failures, result.errors,
                 result.skipped))

            det_results = []
            for name, value in (("failures", result.failures),
                                ("errors",result.errors),
                                ("skipped", result.skipped)):
                if value:
                    det_results.append("%s=%i" % (name, len(value)))
            if det_results:
                self.stream.write(" (")
                self.stream.write(', '.join(det_results))
                self.stream.write(")")
            self.stream.writeln("")
        return result


class keywords(dict):
    """Keyword args (**kwargs) support for generative tests."""

class starargs(tuple):
    """Variable arguments (*args) for generative tests."""
    def __new__(cls, *args):
        return tuple.__new__(cls, args)



class NonStrictTestLoader(unittest.TestLoader):
    """
    Overrides default testloader to be able to omit classname when
    specifying tests to run on command line.

    For example, if the file test_foo.py contains ::

        class FooTC(TestCase):
            def test_foo1(self): # ...
            def test_foo2(self): # ...
            def test_bar1(self): # ...

        class BarTC(TestCase):
            def test_bar2(self): # ...

    'python test_foo.py' will run the 3 tests in FooTC
    'python test_foo.py FooTC' will run the 3 tests in FooTC
    'python test_foo.py test_foo' will run test_foo1 and test_foo2
    'python test_foo.py test_foo1' will run test_foo1
    'python test_foo.py test_bar' will run FooTC.test_bar1 and BarTC.test_bar2
    """

    def __init__(self):
        self.skipped_patterns = []

    def loadTestsFromNames(self, names, module=None):
        suites = []
        for name in names:
            suites.extend(self.loadTestsFromName(name, module))
        return self.suiteClass(suites)

    def _collect_tests(self, module):
        tests = {}
        for obj in vars(module).values():
            if (issubclass(type(obj), (types.ClassType, type)) and
                 issubclass(obj, unittest.TestCase)):
                classname = obj.__name__
                if classname[0] == '_' or self._this_is_skipped(classname):
                    continue
                methodnames = []
                # obj is a TestCase class
                for attrname in dir(obj):
                    if attrname.startswith(self.testMethodPrefix):
                        attr = getattr(obj, attrname)
                        if callable(attr):
                            methodnames.append(attrname)
                # keep track of class (obj) for convenience
                tests[classname] = (obj, methodnames)
        return tests

    def loadTestsFromSuite(self, module, suitename):
        try:
            suite = getattr(module, suitename)()
        except AttributeError:
            return []
        assert hasattr(suite, '_tests'), \
               "%s.%s is not a valid TestSuite" % (module.__name__, suitename)
        # python2.3 does not implement __iter__ on suites, we need to return
        # _tests explicitly
        return suite._tests

    def loadTestsFromName(self, name, module=None):
        parts = name.split('.')
        if module is None or len(parts) > 2:
            # let the base class do its job here
            return [super(NonStrictTestLoader, self).loadTestsFromName(name)]
        tests = self._collect_tests(module)
        # import pprint
        # pprint.pprint(tests)
        collected = []
        if len(parts) == 1:
            pattern = parts[0]
            if callable(getattr(module, pattern, None)
                    )  and pattern not in tests:
                # consider it as a suite
                return self.loadTestsFromSuite(module, pattern)
            if pattern in tests:
                # case python unittest_foo.py MyTestTC
                klass, methodnames = tests[pattern]
                for methodname in methodnames:
                    collected = [klass(methodname)
                        for methodname in methodnames]
            else:
                # case python unittest_foo.py something
                for klass, methodnames in tests.values():
                    collected += [klass(methodname)
                        for methodname in methodnames]
        elif len(parts) == 2:
            # case "MyClass.test_1"
            classname, pattern = parts
            klass, methodnames = tests.get(classname, (None, []))
            for methodname in methodnames:
                collected = [klass(methodname) for methodname in methodnames]
        return collected

    def _this_is_skipped(self, testedname):
        return any([(pat in testedname) for pat in self.skipped_patterns])

    def getTestCaseNames(self, testCaseClass):
        """Return a sorted sequence of method names found within testCaseClass
        """
        is_skipped = self._this_is_skipped
        classname = testCaseClass.__name__
        if classname[0] == '_' or is_skipped(classname):
            return []
        testnames = super(NonStrictTestLoader, self).getTestCaseNames(
                testCaseClass)
        return [testname for testname in testnames if not is_skipped(testname)]


class SkipAwareTestProgram(unittest.TestProgram):
    # XXX: don't try to stay close to unittest.py, use optparse
    USAGE = """\
Usage: %(progName)s [options] [test] [...]

Options:
  -h, --help       Show this message
  -v, --verbose    Verbose output
  -i, --pdb        Enable test failure inspection
  -x, --exitfirst  Exit on first failure
  -c, --capture    Captures and prints standard out/err only on errors
  -p, --printonly  Only prints lines matching specified pattern
                   (implies capture)
  -s, --skip       skip test matching this pattern (no regexp for now)
  -q, --quiet      Minimal output
  --color          colorize tracebacks

  -m, --match      Run only test whose tag match this pattern

  -P, --profile    FILE: Run the tests using cProfile and saving results
                   in FILE

Examples:
  %(progName)s                               - run default set of tests
  %(progName)s MyTestSuite                   - run suite 'MyTestSuite'
  %(progName)s MyTestCase.testSomething      - run MyTestCase.testSomething
  %(progName)s MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
"""
    def __init__(self, module='__main__', defaultTest=None, batchmode=False,
                 cvg=None, options=None, outstream=sys.stderr):
        self.batchmode = batchmode
        self.cvg = cvg
        self.options = options
        self.outstream = outstream
        super(SkipAwareTestProgram, self).__init__(
            module=module, defaultTest=defaultTest,
            testLoader=NonStrictTestLoader())

    def parseArgs(self, argv):
        self.pdbmode = False
        self.exitfirst = False
        self.capture = 0
        self.printonly = None
        self.skipped_patterns = []
        self.test_pattern = None
        self.tags_pattern = None
        self.colorize = False
        self.profile_name = None
        import getopt
        try:
            options, args = getopt.getopt(argv[1:], 'hHvixrqcp:s:m:P:',
                                          ['help', 'verbose', 'quiet', 'pdb',
                                           'exitfirst', 'restart', 'capture', 'printonly=',
                                           'skip=', 'color', 'match=', 'profile='])
            for opt, value in options:
                if opt in ('-h', '-H', '--help'):
                    self.usageExit()
                if opt in ('-i', '--pdb'):
                    self.pdbmode = True
                if opt in ('-x', '--exitfirst'):
                    self.exitfirst = True
                if opt in ('-r', '--restart'):
                    self.restart = True
                    self.exitfirst = True
                if opt in ('-q', '--quiet'):
                    self.verbosity = 0
                if opt in ('-v', '--verbose'):
                    self.verbosity = 2
                if opt in ('-c', '--capture'):
                    self.capture += 1
                if opt in ('-p', '--printonly'):
                    self.printonly = re.compile(value)
                if opt in ('-s', '--skip'):
                    self.skipped_patterns = [pat.strip() for pat in
                                             value.split(', ')]
                if opt == '--color':
                    self.colorize = True
                if opt in ('-m', '--match'):
                    #self.tags_pattern = value
                    self.options["tag_pattern"] = value
                if opt in ('-P', '--profile'):
                    self.profile_name = value
            self.testLoader.skipped_patterns = self.skipped_patterns
            if self.printonly is not None:
                self.capture += 1
            if len(args) == 0 and self.defaultTest is None:
                suitefunc = getattr(self.module, 'suite', None)
                if isinstance(suitefunc, (types.FunctionType,
                        types.MethodType)):
                    self.test = self.module.suite()
                else:
                    self.test = self.testLoader.loadTestsFromModule(self.module)
                return
            if len(args) > 0:
                self.test_pattern = args[0]
                self.testNames = args
            else:
                self.testNames = (self.defaultTest, )
            self.createTests()
        except getopt.error, msg:
            self.usageExit(msg)


    def runTests(self):
        if self.profile_name:
            import cProfile
            cProfile.runctx('self._runTests()', globals(), locals(), self.profile_name )
        else:
            return self._runTests()

    def _runTests(self):
        if hasattr(self.module, 'setup_module'):
            try:
                self.module.setup_module(self.options)
            except Exception, exc:
                print 'setup_module error:', exc
                sys.exit(1)
        self.testRunner = SkipAwareTextTestRunner(verbosity=self.verbosity,
                                                  stream=self.outstream,
                                                  exitfirst=self.exitfirst,
                                                  capture=self.capture,
                                                  printonly=self.printonly,
                                                  pdbmode=self.pdbmode,
                                                  cvg=self.cvg,
                                                  test_pattern=self.test_pattern,
                                                  skipped_patterns=self.skipped_patterns,
                                                  colorize=self.colorize,
                                                  batchmode=self.batchmode,
                                                  options=self.options)

        def removeSucceededTests(obj, succTests):
            """ Recursive function that removes succTests from
            a TestSuite or TestCase
            """
            if isinstance(obj, TestSuite):
                removeSucceededTests(obj._tests, succTests)
            if isinstance(obj, list):
                for el in obj[:]:
                    if isinstance(el, TestSuite):
                        removeSucceededTests(el, succTests)
                    elif isinstance(el, TestCase):
                        descr = '.'.join((el.__class__.__module__,
                                el.__class__.__name__,
                                el._testMethodName))
                        if descr in succTests:
                            obj.remove(el)
        # take care, self.options may be None
        if getattr(self.options, 'restart', False):
            # retrieve succeeded tests from FILE_RESTART
            try:
                restartfile = open(FILE_RESTART, 'r')
                try:
                    try:
                        succeededtests = list(elem.rstrip('\n\r') for elem in
                            restartfile.readlines())
                        removeSucceededTests(self.test, succeededtests)
                    except Exception, e:
                        raise e
                finally:
                    restartfile.close()
            except Exception ,e:
                raise "Error while reading \
succeeded tests into", osp.join(os.getcwd(),FILE_RESTART)

        result = self.testRunner.run(self.test)
        # help garbage collection: we want TestSuite, which hold refs to every
        # executed TestCase, to be gc'ed
        del self.test
        if hasattr(self.module, 'teardown_module'):
            try:
                self.module.teardown_module(self.options, result)
            except Exception, exc:
                print 'teardown_module error:', exc
                sys.exit(1)
        if result.debuggers and self.pdbmode:
            start_interactive_mode(result)
        if not self.batchmode:
            sys.exit(not result.wasSuccessful())
        self.result = result




class FDCapture:
    """adapted from py lib (http://codespeak.net/py)
    Capture IO to/from a given os-level filedescriptor.
    """
    def __init__(self, fd, attr='stdout', printonly=None):
        self.targetfd = fd
        self.tmpfile = os.tmpfile() # self.maketempfile()
        self.printonly = printonly
        # save original file descriptor
        self._savefd = os.dup(fd)
        # override original file descriptor
        os.dup2(self.tmpfile.fileno(), fd)
        # also modify sys module directly
        self.oldval = getattr(sys, attr)
        setattr(sys, attr, self) # self.tmpfile)
        self.attr = attr

    def write(self, msg):
        # msg might be composed of several lines
        for line in msg.splitlines():
            line += '\n' # keepdend=True is not enough
            if self.printonly is None or self.printonly.search(line) is None:
                self.tmpfile.write(line)
            else:
                os.write(self._savefd, line)

##     def maketempfile(self):
##         tmpf = os.tmpfile()
##         fd = os.dup(tmpf.fileno())
##         newf = os.fdopen(fd, tmpf.mode, 0) # No buffering
##         tmpf.close()
##         return newf

    def restore(self):
        """restore original fd and returns captured output"""
        #XXX: hack hack hack
        self.tmpfile.flush()
        try:
            ref_file = getattr(sys, '__%s__' % self.attr)
            ref_file.flush()
        except AttributeError:
            pass
        if hasattr(self.oldval, 'flush'):
            self.oldval.flush()
        # restore original file descriptor
        os.dup2(self._savefd, self.targetfd)
        # restore sys module
        setattr(sys, self.attr, self.oldval)
        # close backup descriptor
        os.close(self._savefd)
        # go to beginning of file and read it
        self.tmpfile.seek(0)
        return self.tmpfile.read()


def _capture(which='stdout', printonly=None):
    """private method, should not be called directly
    (cf. capture_stdout() and capture_stderr())
    """
    assert which in ('stdout', 'stderr'
        ), "Can only capture stdout or stderr, not %s" % which
    if which == 'stdout':
        fd = 1
    else:
        fd = 2
    return FDCapture(fd, which, printonly)

def capture_stdout(printonly=None):
    """captures the standard output

    returns a handle object which has a `restore()` method.
    The restore() method returns the captured stdout and restores it
    """
    return _capture('stdout', printonly)

def capture_stderr(printonly=None):
    """captures the standard error output

    returns a handle object which has a `restore()` method.
    The restore() method returns the captured stderr and restores it
    """
    return _capture('stderr', printonly)


def unittest_main(module='__main__', defaultTest=None,
                  batchmode=False, cvg=None, options=None,
                  outstream=sys.stderr):
    """use this function if you want to have the same functionality
    as unittest.main"""
    return SkipAwareTestProgram(module, defaultTest, batchmode,
                                cvg, options, outstream)

class TestSkipped(Exception):
    """raised when a test is skipped"""

class InnerTestSkipped(TestSkipped):
    """raised when a test is skipped"""

def is_generator(function):
    flags = function.func_code.co_flags
    return flags & CO_GENERATOR


def parse_generative_args(params):
    args = []
    varargs = ()
    kwargs = {}
    flags = 0 # 2 <=> starargs, 4 <=> kwargs
    for param in params:
        if isinstance(param, starargs):
            varargs = param
            if flags:
                raise TypeError('found starargs after keywords !')
            flags |= 2
            args += list(varargs)
        elif isinstance(param, keywords):
            kwargs = param
            if flags & 4:
                raise TypeError('got multiple keywords parameters')
            flags |= 4
        elif flags & 2 or flags & 4:
            raise TypeError('found parameters after kwargs or args')
        else:
            args.append(param)

    return args, kwargs

class InnerTest(tuple):
    def __new__(cls, name, *data):
        instance = tuple.__new__(cls, data)
        instance.name = name
        return instance


class TestCase(unittest.TestCase):
    """unittest.TestCase with some additional methods"""

    capture = False
    pdbclass = Debugger

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName)
        # internal API changed in python2.5
        if sys.version_info >= (2, 5):
            self.__exc_info = self._exc_info
            self.__testMethodName = self._testMethodName
        else:
            # let's give easier access to _testMethodName to every subclasses
            self._testMethodName = self.__testMethodName
        self._captured_stdout = ""
        self._captured_stderr = ""
        self._out = []
        self._err = []
        self._current_test_descr = None
        self._options_ = None

    def datadir(cls): # pylint: disable-msg=E0213
        """helper attribute holding the standard test's data directory

        NOTE: this is a logilab's standard
        """
        mod = __import__(cls.__module__)
        return osp.join(osp.dirname(osp.abspath(mod.__file__)), 'data')
    # cache it (use a class method to cache on class since TestCase is
    # instantiated for each test run)
    datadir = classproperty(cached(datadir))

    def datapath(cls, *fname):
        """joins the object's datadir and `fname`"""
        return osp.join(cls.datadir, *fname)
    datapath = classmethod(datapath)

    def set_description(self, descr):
        """sets the current test's description.
        This can be useful for generative tests because it allows to specify
        a description per yield
        """
        self._current_test_descr = descr

    # override default's unittest.py feature
    def shortDescription(self):
        """override default unitest shortDescription to handle correctly
        generative tests
        """
        if self._current_test_descr is not None:
            return self._current_test_descr
        return super(TestCase, self).shortDescription()


    def captured_output(self):
        """return a two tuple with standard output and error stripped"""
        return self._captured_stdout.strip(), self._captured_stderr.strip()

    def _start_capture(self):
        """start_capture if enable"""
        if self.capture:
            warnings.simplefilter('ignore', DeprecationWarning)
            self.start_capture()

    def _stop_capture(self):
        """stop_capture and restore previous output"""
        self._force_output_restore()

    def start_capture(self, printonly=None):
        """start_capture"""
        self._out.append(capture_stdout(printonly or self._printonly))
        self._err.append(capture_stderr(printonly or self._printonly))

    def printonly(self, pattern, flags=0):
        """set the pattern of line to print"""
        rgx = re.compile(pattern, flags)
        if self._out:
            self._out[-1].printonly = rgx
            self._err[-1].printonly = rgx
        else:
            self.start_capture(printonly=rgx)

    def stop_capture(self):
        """stop output and error capture"""
        if self._out:
            _out = self._out.pop()
            _err = self._err.pop()
            return _out.restore(), _err.restore()
        return '', ''

    def _force_output_restore(self):
        """remove all capture set"""
        while self._out:
            self._captured_stdout += self._out.pop().restore()
            self._captured_stderr += self._err.pop().restore()

    def quiet_run(self, result, func, *args, **kwargs):
        self._start_capture()
        try:
            func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            self._stop_capture()
            raise
        except:
            self._stop_capture()
            result.addError(self, self.__exc_info())
            return False
        self._stop_capture()
        return True

    def _get_test_method(self):
        """return the test method"""
        return getattr(self, self.__testMethodName)


    def optval(self, option, default=None):
        """return the option value or default if the option is not define"""
        return getattr(self._options_, option, default)

    def __call__(self, result=None, runcondition=None, options=None):
        """rewrite TestCase.__call__ to support generative tests
        This is mostly a copy/paste from unittest.py (i.e same
        variable names, same logic, except for the generative tests part)
        """
        if result is None:
            result = self.defaultTestResult()
        result.pdbclass = self.pdbclass
        # if self.capture is True here, it means it was explicitly specified
        # in the user's TestCase class. If not, do what was asked on cmd line
        self.capture = self.capture or getattr(result, 'capture', False)
        self._options_ = options
        self._printonly = getattr(result, 'printonly', None)
        # if result.cvg:
        #     result.cvg.start()
        testMethod = self._get_test_method()
        if runcondition and not runcondition(testMethod):
            return # test is skipped
        result.startTest(self)
        try:
            if not self.quiet_run(result, self.setUp):
                return
            generative = is_generator(testMethod.im_func)
            # generative tests
            if generative:
                self._proceed_generative(result, testMethod,
                                         runcondition)
            else:
                status = self._proceed(result, testMethod)
                success = (status == 0)
            if not self.quiet_run(result, self.tearDown):
                return
            if not generative and success:
                if hasattr(options, "exitfirst") and options.exitfirst:
                    # add this test to restart file
                    try:
                        restartfile = open(FILE_RESTART, 'a')
                        try:
                            try:
                                descr = '.'.join((self.__class__.__module__,
                                    self.__class__.__name__,
                                    self._testMethodName))
                                restartfile.write(descr+os.linesep)
                            except Exception, e:
                                raise e
                        finally:
                            restartfile.close()
                    except Exception, e:
                        print >> sys.__stderr__, "Error while saving \
succeeded test into", osp.join(os.getcwd(),FILE_RESTART)
                        raise e
                result.addSuccess(self)
        finally:
            # if result.cvg:
            #     result.cvg.stop()
            result.stopTest(self)



    def _proceed_generative(self, result, testfunc, runcondition=None):
        # cancel startTest()'s increment
        result.testsRun -= 1
        self._start_capture()
        success = True
        try:
            for params in testfunc():
                if runcondition and not runcondition(testfunc,
                        skipgenerator=False):
                    if not (isinstance(params, InnerTest)
                            and runcondition(params)):
                        continue
                if not isinstance(params, (tuple, list)):
                    params = (params, )
                func = params[0]
                args, kwargs = parse_generative_args(params[1:])
                # increment test counter manually
                result.testsRun += 1
                status = self._proceed(result, func, args, kwargs)
                if status == 0:
                    result.addSuccess(self)
                    success = True
                else:
                    success = False
                    if status == 2:
                        result.shouldStop = True
                if result.shouldStop: # either on error or on exitfirst + error
                    break
        except:
            # if an error occurs between two yield
            result.addError(self, self.__exc_info())
            success = False
        self._stop_capture()
        return success

    def _proceed(self, result, testfunc, args=(), kwargs=None):
        """proceed the actual test
        returns 0 on success, 1 on failure, 2 on error

        Note: addSuccess can't be called here because we have to wait
        for tearDown to be successfully executed to declare the test as
        successful
        """
        self._start_capture()
        kwargs = kwargs or {}
        try:
            testfunc(*args, **kwargs)
            self._stop_capture()
        except self.failureException:
            self._stop_capture()
            result.addFailure(self, self.__exc_info())
            return 1
        except KeyboardInterrupt:
            self._stop_capture()
            raise
        except InnerTestSkipped, e:
            result.addSkipped(self, e)
            return 1
        except:
            self._stop_capture()
            result.addError(self, self.__exc_info())
            return 2
        return 0

    def defaultTestResult(self):
        """return a new instance of the defaultTestResult"""
        return SkipAwareTestResult()

    def skip(self, msg=None):
        """mark a test as skipped for the <msg> reason"""
        msg = msg or 'test was skipped'
        raise TestSkipped(msg)

    def innerSkip(self, msg=None):
        """mark a generative test as skipped for the <msg> reason"""
        msg = msg or 'test was skipped'
        raise InnerTestSkipped(msg)

    def assertIn(self, object, set):
        """assert <object> are in <set>"""
        self.assert_(object in set, "%s not in %s" % (object, set))

    def assertNotIn(self, object, set):
        """assert <object> are not in <set>"""
        self.assert_(object not in set, "%s in %s" % (object, set))

    def assertDictEquals(self, dict1, dict2):
        """compares two dicts

        If the two dict differ, the first difference is shown in the error
        message
        """
        dict1 = dict(dict1)
        msgs = []
        for key, value in dict2.items():
            try:
                if dict1[key] != value:
                    msgs.append('%r != %r for key %r' % (dict1[key], value,
                        key))
                del dict1[key]
            except KeyError:
                msgs.append('missing %r key' % key)
        if dict1:
            msgs.append('dict2 is lacking %r' % dict1)
        if msgs:
            self.fail('\n'.join(msgs))
    assertDictEqual = assertDictEquals



    def assertUnorderedIterableEquals(self, got, expected, msg=None):
        """compares two iterable and shows difference between both"""
        got, expected = list(got), list(expected)
        self.assertSetEqual(set(got), set(expected), msg)
        if len(got) != len(expected):
            if msg is None:
                msg = ['Iterable have the same elements but not the same number',
                       '\t<element>\t<expected>i\t<got>']
                got_count = {}
                expected_count = {}
                for element in got:
                    got_count[element] = got_count.get(element,0) + 1
                for element in expected:
                    expected_count[element] = expected_count.get(element,0) + 1
                # we know that got_count.key() == expected_count.key()
                # because of assertSetEquals
                for element, count in got_count.iteritems():
                    other_count = expected_count[element]
                    if other_count != count:
                        msg.append('\t%s\t%s\t%s' % (element, other_count, count))

            self.fail(msg)

    assertUnorderedIterableEqual = assertUnorderedIterableEquals
    assertUnordIterEquals = assertUnordIterEqual = assertUnorderedIterableEqual

    def assertSetEquals(self,got,expected, msg=None):
        if not(isinstance(got, set) and isinstance(expected, set)):
            warnings.warn("the assertSetEquals function if now intended for set only."\
                          "use assertUnorderedIterableEquals instead.",
                DeprecationWarning, 2)
            return self.assertUnorderedIterableEquals(got,expected, msg)

        items={}
        items['missing'] = expected - got
        items['unexpected'] = got - expected
        if any(items.itervalues()):
            if msg is None:
                msg = '\n'.join('%s:\n\t%s' % (key,"\n\t".join(str(value) for value in values))
                    for key, values in items.iteritems() if values)
            self.fail(msg)


    assertSetEqual = assertSetEquals

    def assertListEquals(self, list_1, list_2, msg=None):
        """compares two lists

        If the two list differ, the first difference is shown in the error
        message
        """
        _l1 = list_1[:]
        for i, value in enumerate(list_2):
            try:
                if _l1[0] != value:
                    from pprint import pprint
                    pprint(list_1)
                    pprint(list_2)
                    self.fail('%r != %r for index %d' % (_l1[0], value, i))
                del _l1[0]
            except IndexError:
                if msg is None:
                    msg = 'list_1 has only %d elements, not %s '\
                        '(at least %r missing)'% (i, len(list_2), value)
                self.fail(msg)
        if _l1:
            if msg is None:
                msg = 'list_2 is lacking %r' % _l1
            self.fail(msg)
    assertListEqual = assertListEquals

    def assertLinesEquals(self, list_1, list_2, msg=None, striplines=False):
        """assert list of lines are equal"""
        lines1 = list_1.splitlines()
        if striplines:
            lines1 = [l.strip() for l in lines1]
        lines2 = list_2.splitlines()
        if striplines:
            lines2 = [l.strip() for l in lines2]
        self.assertListEquals(lines1, lines2, msg)
    assertLineEqual = assertLinesEquals

    def assertXMLWellFormed(self, stream, msg=None, context=2):
        """asserts the XML stream is well-formed (no DTD conformance check)
        :context: number of context lines in standard msg. all data if negativ
                  only available with element tree
        """
        try:
            from xml.etree.ElementTree import parse
            self._assertETXMLWellFormed(stream, parse, msg)
        except ImportError:
            from xml.sax import make_parser, SAXParseException
            parser = make_parser()
            try:
                parser.parse(stream)
            except SAXParseException, ex:
                if msg is None:
                    stream.seek(0)
                    for _ in xrange(ex.getLineNumber()):
                        line = stream.readline()
                    pointer = ('' * (ex.getLineNumber() - 1)) + '^'
                    msg = 'XML stream not well formed: %s\n%s%s' % (ex, line, pointer)
                self.fail(msg)

    def assertXMLStringWellFormed(self, xml_string, msg=None, context=2):
        """asserts the XML string is well-formed (no DTD conformance check)
        :context: number of context lines in standard msg. all data if negativ
                  only available with element tree
        """
        try:
            from xml.etree.ElementTree import fromstring
            self._assertETXMLWellFormed(xml_string, fromstring, msg)
        except ImportError:
            raise
            stream = StringIO(xml_string)
            self.assertXMLWellFormed(stream, msg)

    def _assertETXMLWellFormed(self, data, parse, msg=None, context=2):
        """internal function used by /assertXML(String)?WellFormed/ functions
        :data: xml_data
        :parse: appropriate parser function for this data
        :msg: error message
        :context: number of context lines in standard msg. all data if negativ
                  only available with element tree
        """
        from xml.parsers.expat import ExpatError
        try:
            parse(data)
        except ExpatError, ex:
            if msg is None:
                if hasattr(data, 'readlines'): #file like object
                    stream.seek(0)
                    lines = stream.readlines()
                else:
                    lines =data.splitlines(True)
                nb_lines = len(lines)
                context_lines = []

                if  context < 0:
                    start = 1
                    end   = nb_lines
                else:
                    start = max(ex.lineno-context, 1)
                    end   = min(ex.lineno+context, nb_lines)
                line_number_length = len('%i' % end)
                line_pattern = " %%%ii: %%s" % line_number_length

                for line_no in xrange(start, ex.lineno):
                    context_lines.append(line_pattern % (line_no, lines[line_no-1]))
                context_lines.append(line_pattern % (ex.lineno, lines[ex.lineno-1]))
                context_lines.append('%s^\n' % (' ' * (1 + line_number_length + 2 +ex.offset)))
                for line_no in xrange(ex.lineno+1, end+1):
                    context_lines.append(line_pattern % (line_no, lines[line_no-1]))

                rich_context = ''.join(context_lines)
                msg = 'XML stream not well formed: %s\n%s' % (ex, rich_context)
            self.fail(msg)


    def assertXMLEqualsTuple(self, element, tup):
        """compare an ElementTree Element to a tuple formatted as follow:
        (tagname, [attrib[, children[, text[, tail]]]])"""
        # check tag
        self.assertTextEquals(element.tag, tup[0])
        # check attrib
        if len(element.attrib) or len(tup)>1:
            if len(tup)<=1:
                self.fail( "tuple %s has no attributes (%s expected)"%(tup,
                    dict(element.attrib)))
            self.assertDictEquals(element.attrib, tup[1])
        # check children
        if len(element) or len(tup)>2:
            if len(tup)<=2:
                self.fail( "tuple %s has no children (%i expected)"%(tup,
                    len(element)))
            if len(element) != len(tup[2]):
                self.fail( "tuple %s has %i children%s (%i expected)"%(tup,
                    len(tup[2]),
                        ('', 's')[len(tup[2])>1], len(element)))
            for index in xrange(len(tup[2])):
                self.assertXMLEqualsTuple(element[index], tup[2][index])
        #check text
        if element.text or len(tup)>3:
            if len(tup)<=3:
                self.fail( "tuple %s has no text value (%r expected)"%(tup,
                    element.text))
            self.assertTextEquals(element.text, tup[3])
        #check tail
        if element.tail or len(tup)>4:
            if len(tup)<=4:
                self.fail( "tuple %s has no tail value (%r expected)"%(tup,
                    element.tail))
            self.assertTextEquals(element.tail, tup[4])

    def _difftext(self, lines1, lines2, junk=None, msg_prefix='Texts differ'):
        junk = junk or (' ', '\t')
        # result is a generator
        result = difflib.ndiff(lines1, lines2, charjunk=lambda x: x in junk)
        read = []
        for line in result:
            read.append(line)
            # lines that don't start with a ' ' are diff ones
            if not line.startswith(' '):
                self.fail('\n'.join(['%s\n'%msg_prefix]+read + list(result)))

    def assertTextEquals(self, text1, text2, junk=None,
            msg_prefix='Text differ', striplines=False):
        """compare two multiline strings (using difflib and splitlines())"""
        msg = []
        if not isinstance(text1, basestring):
            msg.append('text1 is not a string (%s)'%(type(text1)))
        if not isinstance(text2, basestring):
            msg.append('text2 is not a string (%s)'%(type(text2)))
        if msg:
            self.fail('\n'.join(msg))
        lines1 = text1.strip().splitlines(True)
        lines2 = text2.strip().splitlines(True)
        if striplines:
            lines1 = [line.strip() for line in lines1]
            lines2 = [line.strip() for line in lines2]
        self._difftext(lines1, lines2, junk,  msg_prefix)
    assertTextEqual = assertTextEquals

    def assertStreamEquals(self, stream1, stream2, junk=None,
            msg_prefix='Stream differ'):
        """compare two streams (using difflib and readlines())"""
        # if stream2 is stream2, readlines() on stream1 will also read lines
        # in stream2, so they'll appear different, although they're not
        if stream1 is stream2:
            return
        # make sure we compare from the beginning of the stream
        stream1.seek(0)
        stream2.seek(0)
        # compare
        self._difftext(stream1.readlines(), stream2.readlines(), junk,
             msg_prefix)

    assertStreamEqual = assertStreamEquals
    def assertFileEquals(self, fname1, fname2, junk=(' ', '\t')):
        """compares two files using difflib"""
        self.assertStreamEqual(file(fname1), file(fname2), junk,
            msg_prefix='Files differs\n-:%s\n+:%s\n'%(fname1, fname2))
    assertFileEqual = assertFileEquals


    def assertDirEquals(self, path_a, path_b):
        """compares two files using difflib"""
        assert osp.exists(path_a), "%s doesn't exists" % path_a
        assert osp.exists(path_b), "%s doesn't exists" % path_b

        all_a = [ (ipath[len(path_a):].lstrip('/'), idirs, ifiles)
                    for ipath, idirs, ifiles in os.walk(path_a)]
        all_a.sort(key=itemgetter(0))

        all_b = [ (ipath[len(path_b):].lstrip('/'), idirs, ifiles)
                    for ipath, idirs, ifiles in os.walk(path_b)]
        all_b.sort(key=itemgetter(0))

        iter_a, iter_b = iter(all_a), iter(all_b)
        partial_iter = True
        ipath_a, idirs_a, ifiles_a = data_a = None, None, None
        while True:
            try:
                ipath_a, idirs_a, ifiles_a = datas_a = iter_a.next()
                partial_iter = False
                ipath_b, idirs_b, ifiles_b = datas_b = iter_b.next()
                partial_iter = True


                self.assert_(ipath_a == ipath_b,
                    "unexpected %s in %s while looking %s from %s" %
                    (ipath_a, path_a, ipath_b, path_b))


                errors = {}
                sdirs_a = set(idirs_a)
                sdirs_b = set(idirs_b)
                errors["unexpected directories"] = sdirs_a - sdirs_b
                errors["missing directories"] = sdirs_b - sdirs_a

                sfiles_a = set(ifiles_a)
                sfiles_b = set(ifiles_b)
                errors["unexpected files"] = sfiles_a - sfiles_b
                errors["missing files"] = sfiles_b - sfiles_a


                msgs = [ "%s: %s"% (name, items)
                    for name, items in errors.iteritems() if items]

                if msgs:
                    msgs.insert(0,"%s and %s differ :" % (
                        osp.join(path_a, ipath_a),
                        osp.join(path_b, ipath_b),
                        ))
                    self.fail("\n".join(msgs))

                for files in (ifiles_a, ifiles_b):
                    files.sort()

                for index, path in enumerate(ifiles_a):
                    self.assertFileEquals(osp.join(path_a, ipath_a, path),
                        osp.join(path_b, ipath_b, ifiles_b[index]))

            except StopIteration:
                break


    assertDirEqual = assertDirEquals


    def assertIsInstance(self, obj, klass, msg=None, strict=False):
        """compares two files using difflib"""
        if msg is None:
            if strict:
                msg = '%r is not of class %s but of %s'
            else:
                msg = '%r is not an instance of %s but of %s'
            msg = msg % (obj, klass, type(obj))
        if strict:
            self.assert_(obj.__class__ is klass, msg)
        else:
            self.assert_(isinstance(obj, klass), msg)

    def assertIs(self, obj, other, msg=None):
        """compares identity of two reference"""
        if msg is None:
            msg = "%r is not %r"%(obj, other)
        self.assert_(obj is other, msg)


    def assertIsNot(self, obj, other, msg=None):
        """compares identity of two reference"""
        if msg is None:
            msg = "%r is %r"%(obj, other)
        self.assert_(obj is not other, msg )

    def assertNone(self, obj, msg=None):
        """assert obj is None"""
        if msg is None:
            msg = "reference to %r when None expected"%(obj,)
        self.assert_( obj is None, msg )

    def assertNotNone(self, obj, msg=None):
        """assert obj is not None"""
        if msg is None:
            msg = "unexpected reference to None"
        self.assert_( obj is not None, msg )

    def assertFloatAlmostEquals(self, obj, other, prec=1e-5, msg=None):
        """compares two floats"""
        if msg is None:
            msg = "%r != %r" % (obj, other)
        self.assert_(math.fabs(obj - other) < prec, msg)

    def failUnlessRaises(self, excClass, callableObj, *args, **kwargs):
        """override default failUnlessRaise method to return the raised
        exception instance.

        Fail unless an exception of class excClass is thrown
        by callableObj when invoked with arguments args and keyword
        arguments kwargs. If a different type of exception is
        thrown, it will not be caught, and the test case will be
        deemed to have suffered an error, exactly as for an
        unexpected exception.
        """
        try:
            callableObj(*args, **kwargs)
        except excClass, exc:
            return exc
        else:
            if hasattr(excClass, '__name__'):
                excName = excClass.__name__
            else:
                excName = str(excClass)
            raise self.failureException, "%s not raised" % excName

    assertRaises = failUnlessRaises

import doctest

class SkippedSuite(unittest.TestSuite):
    def test(self):
        """just there to trigger test execution"""
        self.skipped_test('doctest module has no DocTestSuite class')


# DocTestFinder was introduced in python2.4
if sys.version_info >= (2, 4):
    class DocTestFinder(doctest.DocTestFinder):

        def __init__(self, *args, **kwargs):
            self.skipped = kwargs.pop('skipped', ())
            doctest.DocTestFinder.__init__(self, *args, **kwargs)

        def _get_test(self, obj, name, module, globs, source_lines):
            """override default _get_test method to be able to skip tests
            according to skipped attribute's value

            Note: Python (<=2.4) use a _name_filter which could be used for that
                  purpose but it's no longer available in 2.5
                  Python 2.5 seems to have a [SKIP] flag
            """
            if getattr(obj, '__name__', '') in self.skipped:
                return None
            return doctest.DocTestFinder._get_test(self, obj, name, module,
                                                   globs, source_lines)
else:
    # this is a hack to make skipped work with python <= 2.3
    class DocTestFinder(object):
        def __init__(self, skipped):
            self.skipped = skipped
            self.original_find_tests = doctest._find_tests
            doctest._find_tests = self._find_tests

        def _find_tests(self, module, prefix=None):
            tests = []
            for testinfo  in self.original_find_tests(module, prefix):
                testname, _, _, _ = testinfo
                # testname looks like A.B.C.function_name
                testname = testname.split('.')[-1]
                if testname not in self.skipped:
                    tests.append(testinfo)
            return tests


class DocTest(TestCase):
    """trigger module doctest
    I don't know how to make unittest.main consider the DocTestSuite instance
    without this hack
    """
    skipped = ()
    def __call__(self, result=None, runcondition=None, options=None):\
            # pylint: disable-msg=W0613
        try:
            finder = DocTestFinder(skipped=self.skipped)
            if sys.version_info >= (2, 4):
                suite = doctest.DocTestSuite(self.module, test_finder=finder)
            else:
                suite = doctest.DocTestSuite(self.module)
        except AttributeError:
            suite = SkippedSuite()
        return suite.run(result)
    run = __call__

    def test(self):
        """just there to trigger test execution"""

MAILBOX = None

class MockSMTP:
    """fake smtplib.SMTP"""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        global MAILBOX
        self.reveived = MAILBOX = []

    def set_debuglevel(self, debuglevel):
        """ignore debug level"""

    def sendmail(self, fromaddr, toaddres, body):
        """push sent mail in the mailbox"""
        self.reveived.append((fromaddr, toaddres, body))

    def quit(self):
        """ignore quit"""


class MockConfigParser(ConfigParser):
    """fake ConfigParser.ConfigParser"""

    def __init__(self, options):
        ConfigParser.__init__(self)
        for section, pairs in options.iteritems():
            self.add_section(section)
            for key, value in pairs.iteritems():
                self.set(section,key,value)
    def write(self, _):
        raise NotImplementedError()


class MockConnection:
    """fake DB-API 2.0 connexion AND cursor (i.e. cursor() return self)"""

    def __init__(self, results):
        self.received = []
        self.states = []
        self.results = results

    def cursor(self):
        """Mock cursor method"""
        return self
    def execute(self, query, args=None):
        """Mock execute method"""
        self.received.append( (query, args) )
    def fetchone(self):
        """Mock fetchone method"""
        return self.results[0]
    def fetchall(self):
        """Mock fetchall method"""
        return self.results
    def commit(self):
        """Mock commiy method"""
        self.states.append( ('commit', len(self.received)) )
    def rollback(self):
        """Mock rollback method"""
        self.states.append( ('rollback', len(self.received)) )
    def close(self):
        """Mock close method"""
        pass


def mock_object(**params):
    """creates an object using params to set attributes
    >>> option = mock_object(verbose=False, index=range(5))
    >>> option.verbose
    False
    >>> option.index
    [0, 1, 2, 3, 4]
    """
    return type('Mock', (), params)()


def create_files(paths, chroot):
    """Creates directories and files found in <path>.

    :param paths: list of relative paths to files or directories
    :param chroot: the root directory in which paths will be created

    >>> from os.path import isdir, isfile
    >>> isdir('/tmp/a')
    False
    >>> create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], '/tmp')
    >>> isdir('/tmp/a')
    True
    >>> isdir('/tmp/a/b/c')
    True
    >>> isfile('/tmp/a/b/c/d/e.py')
    True
    >>> isfile('/tmp/a/b/foo.py')
    True
    """
    dirs, files = set(), set()
    for path in paths:
        path = osp.join(chroot, path)
        filename = osp.basename(path)
        # path is a directory path
        if filename == '':
            dirs.add(path)
        # path is a filename path
        else:
            dirs.add(osp.dirname(path))
            files.add(path)
    for dirpath in dirs:
        if not osp.isdir(dirpath):
            os.makedirs(dirpath)
    for filepath in files:
        file(filepath, 'w').close()

def enable_dbc(*args):
    """
    Without arguments, return True if contracts can be enabled and should be
    enabled (see option -d), return False otherwise.

    With arguments, return False if contracts can't or shouldn't be enabled,
    otherwise weave ContractAspect with items passed as arguments.
    """
    if not ENABLE_DBC:
        return False
    try:
        from logilab.aspects.weaver import weaver
        from logilab.aspects.lib.contracts import ContractAspect
    except ImportError:
        sys.stderr.write(
            'Warning: logilab.aspects is not available. Contracts disabled.')
        return False
    for arg in args:
        weaver.weave_module(arg, ContractAspect)
    return True


class AttrObject: # XXX cf mock_object
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def tag(*args):
    """descriptor adding tag to a function"""
    def desc(func):
        assert not hasattr(func, 'tags')
        func.tags = Tags(args)
        return func
    return desc

class Tags(set):
    """A set of tag able validate an expression"""
    def __getitem__(self, key):
        return key in self

    def match(self, exp):
        return eval(exp, {}, self)

def require_version(version):
    """ Compare version of python interpreter to the given one. Skip the test
    if older.
    """
    def check_require_version(f):
        version_elements = version.split('.')
        try:
            compare = tuple([int(v) for v in version_elements])
        except ValueError:
            raise ValueError('%s is not a correct version : should be X.Y[.Z].' % version)
        current = sys.version_info[:3]
        #print 'comp', current, compare
        if current < compare:
            #print 'version too old'
            def new_f(self, *args, **kwargs):
                self.skip('Need at least %s version of python. Current version is %s.' % (version, '.'.join([str(element) for element in current])))
            new_f.__name__ = f.__name__
            return new_f
        else:
            #print 'version young enough'
            return f
    return check_require_version

def require_module(module):
    """ Check if the given module is loaded. Skip the test if not.
    """
    def check_require_module(f):
        try:
            __import__(module)
            #print module, 'imported'
            return f
        except ImportError:
            #print module, 'can not be imported'
            def new_f(self, *args, **kwargs):
                self.skip('%s can not be imported.' % module)
            new_f.__name__ = f.__name__
            return new_f
    return check_require_module
