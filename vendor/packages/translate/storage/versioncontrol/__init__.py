#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009,2012 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""This module manages interaction with version control systems.

To implement support for a new version control system, inherit from
:class:`GenericRevisionControlSystem`.

TODO:
  - Add authentication handling
  - :func:`commitdirectory` should do a single commit instead of one for
    each file
  - Maybe implement some caching for :func:`get_versioned_object` - check
    profiler
"""

import os
import re
import subprocess


DEFAULT_RCS = ["svn", "cvs", "darcs", "git", "bzr", "hg"]
"""the names of all supported revision control systems

modules of the same name containing a class with the same name are expected
to be defined below 'translate.storage.versioncontrol'
"""

__CACHED_RCS_CLASSES = {}
"""The dynamically loaded revision control system implementations (python
modules) are cached here for faster access.
"""


def __get_rcs_class(name):
    if not name in __CACHED_RCS_CLASSES:
        try:
            module = __import__("translate.storage.versioncontrol.%s" % name,
                    globals(), {}, name)
            # the module function "is_available" must return "True"
            if (hasattr(module, "is_available") and
                callable(module.is_available) and
                module.is_available()):
                # we found an appropriate module
                rcs_class = getattr(module, name)
            else:
                # the RCS client does not seem to be installed
                rcs_class = None
                try:
                    DEFAULT_RCS.remove(name)
                except ValueError:
                    # we might have had a race condition and another thread
                    # already removed it
                    pass
        except (ImportError, AttributeError):
            rcs_class = None
        __CACHED_RCS_CLASSES[name] = rcs_class
    return __CACHED_RCS_CLASSES[name]


def run_command(command, cwd=None):
    """Runs a command (array of program name and arguments) and returns the
    exitcode, the output and the error as a tuple.

    :param command: list of arguments to be joined for a program call
    :type command: list
    :param cwd: optional directory where the command should be executed
    :type cwd: str
    """
    # ok - we use "subprocess"
    try:
        proc = subprocess.Popen(args=command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=cwd)
        (output, error) = proc.communicate()
        ret = proc.returncode
        return ret, output, error
    except OSError as err_msg:
        # failed to run the program (e.g. the executable was not found)
        return -1, "", err_msg


def prepare_filelist(files):
    if not isinstance(files, list):
        files = [files]
    return [os.path.realpath(f) for f in files]


def youngest_ancestor(files):
    return os.path.commonprefix([os.path.dirname(f) for f in files])


class GenericRevisionControlSystem(object):
    """The super class for all version control classes.

    Always inherit from this class to implement another RC interface.

    At least the two attributes :attr:`RCS_METADIR` and :attr:`SCAN_PARENTS`
    must be overriden by all implementations that derive from this class.

    By default, all implementations can rely on the following attributes:
      - :attr:`root_dir`: the parent of the metadata directory of the
        working copy
      - :attr:`location_abs`: the absolute path of the RCS object
      - :attr:`location_rel`: the path of the RCS object relative
        to :attr:`root_dir`
    """

    RCS_METADIR = None
    """The name of the metadata directory of the RCS

    e.g.: for Subversion -> ".svn"
    """

    SCAN_PARENTS = None
    """Whether to check the parent directories for the metadata directory of
    the RCS working copy

    Some revision control systems store their metadata directory only
    in the base of the working copy (e.g. bzr, GIT and Darcs)
    use ``True`` for these RCS

    Other RCS store a metadata directory in every single directory of
    the working copy (e.g. Subversion and CVS)
    use ``False`` for these RCS
    """

    def __init__(self, location, oldest_parent=None):
        """Find the relevant information about this RCS object

        The :exc:`IOError` exception indicates that the specified object (file
        or directory) is not controlled by the given version control system.

        :param oldest_parent: optional highest path where a recursive search
                              should be stopped
        :type oldest_parent: str
        """
        # check if the implementation looks ok - otherwise raise IOError
        self._self_check()
        # search for the repository information
        location = os.path.normpath(location)
        result = self._find_rcs_directory(location, oldest_parent)
        if result is None:
            raise IOError("Could not find revision control information: %s" %
                          location)

        self.root_dir, self.location_abs, self.location_rel = result
        if not os.path.isdir(location):
            if not self._file_exists(location):
                raise IOError("Not present in repository: %s" % location)

    def _find_rcs_directory(self, rcs_obj, oldest_parent=None):
        """Try to find the metadata directory of the RCS

        :param oldest_parent: optional highest path where a recursive search
                              should be stopped
        :type oldest_parent: str
        :rtype: tuple
        :return:
          - the absolute path of the directory, that contains the metadata
            directory
          - the absolute path of the RCS object
          - the relative path of the RCS object based on the directory above
        """
        if os.path.isdir(os.path.abspath(rcs_obj)):
            rcs_obj_dir = os.path.abspath(rcs_obj)
        else:
            rcs_obj_dir = os.path.dirname(os.path.abspath(rcs_obj))

        if os.path.isdir(os.path.join(rcs_obj_dir, self.RCS_METADIR)):
            # is there a metadir next to the rcs_obj?
            # (for Subversion, CVS, ...)
            location_abs = os.path.abspath(rcs_obj)
            location_rel = os.path.basename(location_abs)
            return (rcs_obj_dir, location_abs, location_rel)
        elif self.SCAN_PARENTS:
            # scan for the metadir in parent directories
            # (for bzr, GIT, Darcs, ...)
            return self._find_rcs_in_parent_directories(rcs_obj, oldest_parent)
        else:
            # no RCS metadata found
            return None

    def _find_rcs_in_parent_directories(self, rcs_obj, oldest_parent=None):
        """Try to find the metadata directory in all parent directories"""
        # first: resolve possible symlinks
        current_dir = os.path.dirname(os.path.realpath(rcs_obj))
        # prevent infite loops
        max_depth = 8
        if oldest_parent:
            oldest_parent = os.path.normpath(oldest_parent)
        # stop as soon as we find the metadata directory
        while not os.path.isdir(os.path.join(current_dir, self.RCS_METADIR)):
            if current_dir == oldest_parent:
                # we were instructed not to look higher up
                return None
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                # we reached the root directory - stop
                return None
            if max_depth <= 0:
                # some kind of dead loop or a _very_ deep directory structure
                return None
            # go to the next higher level
            current_dir = parent_dir
            max_depth -= 1
        # the loop was finished successfully
        # i.e.: we found the metadata directory
        rcs_dir = current_dir
        location_abs = os.path.realpath(rcs_obj)
        # strip the base directory from the path of the rcs_obj
        basedir = rcs_dir + os.path.sep
        if location_abs.startswith(basedir):
            # remove the base directory (including the trailing slash)
            location_rel = location_abs.replace(basedir, "", 1)
            # successfully finished
            return (rcs_dir, location_abs, location_rel)
        else:
            # this should never happen
            return None

    def _self_check(self):
        """Check if all necessary attributes are defined

        Useful to make sure, that a new implementation does not forget
        something like :attr:`RCS_METADIR`
        """
        if self.RCS_METADIR is None:
            raise IOError("Incomplete RCS interface implementation: "
                          "self.RCS_METADIR is None")
        if self.SCAN_PARENTS is None:
            raise IOError("Incomplete RCS interface implementation: "
                          "self.SCAN_PARENTS is None")
        # we do not check for implemented functions - they raise
        # NotImplementedError exceptions anyway
        return True

    def _file_exists(self, path):
        """Method to check if a file exists ``in the repository``."""
        # If getcleanfile() worked, we assume the file exits. Implementations
        # can provide optimised versions.
        return bool(self.getcleanfile())

    def getcleanfile(self, revision=None):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:"
                                  " 'getcleanfile' is missing")

    def commit(self, message=None, author=None):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:"
                                  " 'commit' is missing")

    def add(self, files, message=None, author=None):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:"
                                  " 'add' is missing")

    def update(self, revision=None, needs_revert=True):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:"
                                  " 'update' is missing")


def get_versioned_objects_recursive(
        location,
        versioning_systems=None,
        follow_symlinks=True):
    """return a list of objects, each pointing to a file below this directory
    """
    rcs_objs = []
    if versioning_systems is None:
        versioning_systems = DEFAULT_RCS[:]

    for dirpath, dirnames, filenames in os.walk(location):
        fnames = dirnames + filenames
        for fname in fnames:
            full_fname = os.path.join(dirpath, fname)
            if os.path.isfile(full_fname):
                try:
                    rcs_objs.append(get_versioned_object(full_fname,
                            versioning_systems, follow_symlinks))
                except IOError:
                    pass
    return rcs_objs


def get_versioned_object(
        location,
        versioning_systems=None,
        follow_symlinks=True,
        oldest_parent=None):
    """return a versioned object for the given file"""
    if versioning_systems is None:
        versioning_systems = DEFAULT_RCS[:]
    # go through all RCS and return a versioned object if possible
    possible_ver_objs = []
    for vers_sys in versioning_systems:
        try:
            vers_sys_class = __get_rcs_class(vers_sys)
            if vers_sys_class is None:
                continue
            ver_obj = vers_sys_class(location, oldest_parent)
            if not ver_obj.SCAN_PARENTS:
                return ver_obj
            possible_ver_objs.append(ver_obj)
        except IOError:
            continue
    # if we find any RCS, return the one with shorted rel path
    if len(possible_ver_objs):
        possible_ver_objs.sort(key=lambda ver_obj: len(ver_obj.location_rel))
        return possible_ver_objs[0]
    # if 'location' is a symlink, then we should try the original file
    if follow_symlinks and os.path.islink(location):
        return get_versioned_object(os.path.realpath(location),
                versioning_systems=versioning_systems,
                follow_symlinks=False)
    # if everything fails:
    raise IOError("Could not find version control information: %s" % location)


def get_available_version_control_systems():
    """ return the class objects of all locally available version control
    systems
    """
    result = []
    for rcs in DEFAULT_RCS:
        rcs_class = __get_rcs_class(rcs)
        if rcs_class:
            result.append(rcs_class)
    return result


# stay compatible to the previous version
def updatefile(filename):
    return get_versioned_object(filename).update()


def getcleanfile(filename, revision=None):
    return get_versioned_object(filename).getcleanfile(revision)


def commitfile(filename, message=None, author=None):
    return get_versioned_object(filename).commit(message=message,
                                                 author=author)


def commitdirectory(directory, message=None, author=None):
    """Commit all files below the given directory.

    Files that are just symlinked into the directory are supported, too
    """
    # for now all files are committed separately
    # should we combine them into one commit?
    for rcs_obj in get_versioned_objects_recursive(directory):
        rcs_obj.commit(message=message, author=author)


def updatedirectory(directory):
    """Update all files below the given directory.

    Files that are just symlinked into the directory are supported, too
    """
    # for now all files are updated separately
    # should we combine them into one update?
    for rcs_obj in get_versioned_objects_recursive(directory):
        rcs_obj.update()


def hasversioning(item, oldest_parent=None):
    try:
        # try all available version control systems
        get_versioned_object(item, oldest_parent=oldest_parent)
        return True
    except IOError:
        return False


if __name__ == "__main__":
    import sys
    filenames = sys.argv[1:]
    if filenames:
        # try to retrieve the given (local) file from a repository
        for filename in filenames:
            contents = getcleanfile(filename)
            sys.stdout.write("\n\n******** %s ********\n\n" % filename)
            sys.stdout.write(contents)
    else:
        # first: make sure, that the translate toolkit is available
        # (useful if "python __init__.py" was called without an appropriate
        # PYTHONPATH)
        import translate.storage.versioncontrol
        # print the names of locally available version control systems
        for rcs in get_available_version_control_systems():
            print(rcs)
