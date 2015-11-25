#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2008,2012 Zuza Software Foundation
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


from translate.storage.versioncontrol import (GenericRevisionControlSystem,
                                              prepare_filelist, run_command,
                                              youngest_ancestor)


def is_available():
    """check if svn is installed"""
    exitcode, output, error = run_command(["svn", "--version"])
    return exitcode == 0

_version = None


def get_version():
    """return a tuple of (major, minor) for the installed subversion client"""
    global _version
    if _version:
        return _version

    command = ["svn", "--version", "--quiet"]
    exitcode, output, error = run_command(command)
    if exitcode == 0:
        major, minor = output.strip().split(".")[0:2]
        if (major.isdigit() and minor.isdigit()):
            _version = (int(major), int(minor))
            return _version
    # something went wrong above
    return (0, 0)


class svn(GenericRevisionControlSystem):
    """Class to manage items under revision control of Subversion."""

    RCS_METADIR = ".svn"
    SCAN_PARENTS = True

    def update(self, revision=None, needs_revert=True):
        """update the working copy - remove local modifications if necessary"""
        output_revert = ""
        if needs_revert:
            # revert the local copy (remove local changes)
            command = ["svn", "revert", self.location_abs]
            exitcode, output_revert, error = run_command(command)
            # any errors?
            if exitcode != 0:
                raise IOError("[SVN] Subversion error running '%s': %s" %
                              (command, error))

        # update the working copy to the given revision
        command = ["svn", "update"]
        if not revision is None:
            command.extend(["-r", revision])
        # the filename is the last argument
        command.append(self.location_abs)
        exitcode, output_update, error = run_command(command)
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" %
                          (command, error))
        return output_revert + output_update

    def add(self, files, message=None, author=None):
        """Add and commit the new files."""
        files = prepare_filelist(files)
        command = ["svn", "add", "-q", "--non-interactive", "--parents", "--force"] + files
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[SVN] Error running SVN command '%s': %s" %
                          (command, error))

        # go down as deep as possible in the tree to avoid accidental commits
        # TODO: explicitly commit files by name
        ancestor = youngest_ancestor(files)
        return output + type(self)(ancestor).commit(message, author)

    def commit(self, message=None, author=None):
        """commit the file and return the given message if present

        the 'author' parameter is used for revision property 'translate:author'
        """
        command = ["svn", "-q", "--non-interactive", "commit", "-m", message or ""]
        # the "--with-revprop" argument is support since svn v1.5
        if author and (get_version() >= (1, 5)):
            command.extend(["--with-revprop", "translate:author=%s" % author])
        # the location is the last argument
        command.append(self.location_abs)
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[SVN] Error running SVN command '%s': %s" %
                          (command, error))
        return output

    def getcleanfile(self, revision=None):
        """return the content of the 'head' revision of the file"""
        command = ["svn", "cat"]
        if not revision is None:
            command.extend(["-r", revision])
        # the filename is the last argument
        command.append(self.location_abs)
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" %
                          (command, error))
        return output
