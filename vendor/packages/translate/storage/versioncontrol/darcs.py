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
    """check if darcs is installed"""
    exitcode, output, error = run_command(["darcs", "--version"])
    return exitcode == 0


class darcs(GenericRevisionControlSystem):
    """Class to manage items under revision control of darcs."""

    RCS_METADIR = "_darcs"
    SCAN_PARENTS = True

    def update(self, revision=None, needs_revert=True):
        """Does a clean update of the given path

        :param revision: ignored for darcs
        """
        output_revert = ""
        if needs_revert:
            # revert local changes (avoids conflicts)
            command = ["darcs", "revert", "--repodir", self.root_dir,
                    "-a", self.location_rel]
            exitcode, output_revert, error = run_command(command)
            if exitcode != 0:
                raise IOError("[Darcs] error running '%s': %s" % (command, error))

        # pull new patches
        command = ["darcs", "pull", "--repodir", self.root_dir, "-a"]
        exitcode, output_pull, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Darcs] error running '%s': %s" % (command, error))
        return output_revert + output_pull

    def add(self, files, message=None, author=None):
        """Add and commit files."""
        files = prepare_filelist(files)
        command = ["darcs", "add", "--repodir", self.root_dir] + files
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" % (
                          command, error))

        # go down as deep as possible in the tree to avoid accidental commits
        # TODO: explicitly commit files by name
        ancestor = youngest_ancestor(files)
        return output + type(self)(ancestor).commit(message, author)

    def commit(self, message=None, author=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        # set change message
        command = ["darcs", "record", "-a", "--repodir", self.root_dir,
                "--skip-long-comment", "-m", message]
        # add the 'author' to the list of arguments if it was given
        if author:
            command.extend(["--author", author])
        # the location of the file is the last argument
        command.append(self.location_rel)
        exitcode, output_record, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" % (
                          command, error))
        # push changes
        command = ["darcs", "push", "-a", "--repodir", self.root_dir]
        exitcode, output_push, error = run_command(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" % (
                          command, error))
        return output_record + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the darcs repository

        :param revision: ignored for darcs
        """
        import os
        filename = os.path.join(self.root_dir, self.RCS_METADIR, 'pristine',
                self.location_rel)
        try:
            darcs_file = open(filename)
            output = darcs_file.read()
            darcs_file.close()
        except IOError as error:
            raise IOError("[Darcs] error reading original file '%s': %s" % (
                          filename, error))
        return output
