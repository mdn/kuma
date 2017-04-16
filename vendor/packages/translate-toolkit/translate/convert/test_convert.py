#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import convert
import os
import sys
from py import test
try:
    import psyco
except Exception:
    psyco = None

class TestConvertCommand:
    """Tests running actual commands on files"""
    convertmodule = convert
    defaultoptions = {"progress": "none"}
    if psyco:
        defaultoptions["psyco"] = "none"

    def setup_method(self, method):
        """creates a clean test directory for the given method"""
        self.testdir = "%s_%s" % (self.__class__.__name__, method.__name__)
        self.cleardir()
        os.mkdir(self.testdir)
        self.rundir = os.path.abspath(os.getcwd())

    def teardown_method(self, method):
        """removes the test directory for the given method"""
        os.chdir(self.rundir)
        self.cleardir()

    def cleardir(self):
        """removes the test directory"""
        if os.path.exists(self.testdir):
            for dirpath, subdirs, filenames in os.walk(self.testdir, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(self.testdir): os.rmdir(self.testdir)
        assert not os.path.exists(self.testdir)

    def run_command(self, *argv, **kwargs):
        """runs the command via the main function, passing self.defaultoptions and keyword arguments as --long options and argv arguments straight"""
        os.chdir(self.testdir)
        argv = list(argv)
        kwoptions = getattr(self, "defaultoptions", {}).copy()
        kwoptions.update(kwargs)
        for key, value in kwoptions.iteritems():
            if value is True:
                argv.append("--%s" % key)
            else:
                argv.append("--%s=%s" % (key, value))
        try:
            self.convertmodule.main(argv)
        finally:
            os.chdir(self.rundir)

    def get_testfilename(self, filename):
        """gets the path to the test file"""
        return os.path.join(self.testdir, filename)

    def open_testfile(self, filename, mode="r"):
        """opens the given filename in the testdirectory in the given mode"""
        filename = self.get_testfilename(filename)
        if not mode.startswith("r"):
            subdir = os.path.dirname(filename)
            currentpath = ""
            if not os.path.isdir(subdir):
                for part in subdir.split(os.sep):
                    currentpath = os.path.join(currentpath, part)
                    if not os.path.isdir(currentpath):
                        os.mkdir(currentpath)
        return open(filename, mode)

    def create_testfile(self, filename, contents):
        """creates the given file in the testdirectory with the given contents"""
        testfile = self.open_testfile(filename, "w")
        testfile.write(contents)

    def read_testfile(self, filename):
        """reads the given file in the testdirectory and returns the contents"""
        testfile = open(self.get_testfilename(filename))
        return testfile.read()

    def help_check(self, options, option, last=False):
        """check that a help string occurs and remove it"""
        assert option in options 
        newoptions = []
        for line in options.splitlines():
            if option in line or not line.lstrip().startswith("-"):
                continue
            newoptions.append(line)
        if last:
            assert newoptions == []
        return "\n".join(newoptions)

    def test_help(self):
        """tests getting help (returning the help_string so further tests can be done)"""
        stdout = sys.stdout
        helpfile = self.open_testfile("help.txt", "w")
        sys.stdout = helpfile
        try:
            test.raises(SystemExit, self.run_command, help=True)
        finally:
            sys.stdout = stdout
        helpfile.close()
        help_string = self.read_testfile("help.txt")
        print help_string
        convertsummary = self.convertmodule.__doc__.split("\n")[0]
        # the convertsummary might be wrapped. this will probably unwrap it
        assert convertsummary in help_string.replace("\n", " ")
        usageline = help_string[:help_string.find("\n")]
        # Different versions of optparse might contain either upper or 
        # lowercase versions of 'Usage:' and 'Options:', so we need to take 
        # that into account
        assert (usageline.startswith("Usage: ") or usageline.startswith("usage: ")) \
            and "[--version] [-h|--help]" in usageline
        options = help_string[help_string.find("ptions:\n"):]
        options = options[options.find("\n")+1:]
        options = self.help_check(options, "--progress=PROGRESS")
        options = self.help_check(options, "--version")
        options = self.help_check(options, "-h, --help")
        options = self.help_check(options, "--manpage")
        options = self.help_check(options, "--errorlevel=ERRORLEVEL")
        if psyco:
            options = self.help_check(options, "--psyco=MODE")
        options = self.help_check(options, "-i INPUT, --input=INPUT")
        options = self.help_check(options, "-x EXCLUDE, --exclude=EXCLUDE")
        options = self.help_check(options, "-o OUTPUT, --output=OUTPUT")
        return options

