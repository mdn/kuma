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
    """check if hg is installed"""
    exitcode, output, error = run_command(["hg", "--version"])
    return exitcode == 0


_version = None


def get_version():
    """Return a tuple of (major, minor) for the installed mercurial client."""
    global _version
    if _version:
        return _version

    import re
    command = ["hg", "--version"]
    exitcode, output, error = run_command(command)
    if exitcode == 0:
        version_line = output.splitlines()[0]
        version_match = re.search(r"\d+\.\d+", version_line)
        if version_match:
            major, minor = version_match.group().split(".")
            if (major.isdigit() and minor.isdigit()):
                _version = (int(major), int(minor))
                return _version
    # if anything broke before, then we return the invalid version number
    return (0, 0)


class hg(GenericRevisionControlSystem):
    """Class to manage items under revision control of mercurial."""

    RCS_METADIR = ".hg"
    SCAN_PARENTS = True

    def update(self, revision=None, needs_revert=True):
        """Does a clean update of the given path

        :param revision: ignored for hg
        """
        output_revert = ""
        if needs_revert:
            # revert local changes (avoids conflicts)
            command = ["hg", "-R", self.root_dir, "revert",
                    "--all", self.location_abs]
            exitcode, output_revert, error = run_command(command)
            if exitcode != 0:
                raise IOError("[Mercurial] error running '%s': %s" %
                              (command, error))

        # pull new patches
        command = ["hg", "-R", self.root_dir, "pull"]
        exitcode, output_pull, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Mercurial] error running '%s': %s" %
                          (command, error))
        # update working directory
        command = ["hg", "-R", self.root_dir, "update"]
        exitcode, output_update, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Mercurial] error running '%s': %s" %
                          (command, error))
        return output_revert + output_pull + output_update

    def add(self, files, message=None, author=None):
        """Add and commit the new files."""
        files = prepare_filelist(files)
        command = ["hg", "add", "-q"] + files
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Mercurial] Error running '%s': %s" %
                          (command, error))

        # go down as deep as possible in the tree to avoid accidental commits
        # TODO: explicitly commit files by name
        ancestor = youngest_ancestor(files)
        return output + type(self)(ancestor).commit(message, author)

    def commit(self, message=None, author=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        # commit changes
        command = ["hg", "-R", self.root_dir, "commit", "-m", message]
        # add the 'author' argument, if it was given (only supported
        # since v1.0)
        if author and (get_version() >= (1, 0)):
            command.extend(["--user", author])
        # the location is the last argument
        command.append(self.location_abs)
        exitcode, output_commit, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Mercurial] Error running '%s': %s" % (
                          command, error))
        # push changes
        command = ["hg", "-R", self.root_dir, "push"]
        exitcode, output_push, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Mercurial] Error running '%s': %s" % (
                          command, error))
        return output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the hg repository"""
        # run hg cat
        command = ["hg", "-R", self.root_dir, "cat",
                self.location_abs]
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Mercurial] Error running '%s': %s" % (
                          command, error))
        return output
