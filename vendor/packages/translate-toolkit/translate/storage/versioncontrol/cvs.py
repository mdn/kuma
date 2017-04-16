#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2007 Zuza Software Foundation
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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
from translate.storage.versioncontrol import run_command
from translate.storage.versioncontrol import GenericRevisionControlSystem


def is_available():
    """check if cvs is installed"""
    exitcode, output, error = run_command(["cvs", "--version"])
    return exitcode == 0


class cvs(GenericRevisionControlSystem):
    """Class to manage items under revision control of CVS."""

    RCS_METADIR = "CVS"
    SCAN_PARENTS = False

    def _readfile(self, cvsroot, path, revision=None):
        """
        Read a single file from the CVS repository without checking out a full 
        working directory.
        
        @param cvsroot: the CVSROOT for the repository
        @param path: path to the file relative to cvs root
        @param revision: revision or tag to get (retrieves from HEAD if None)
        """
        command = ["cvs", "-d", cvsroot, "-Q", "co", "-p"]
        if revision:
            command.extend(["-r", revision])
        # the path is the last argument
        command.append(path)
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[CVS] Could not read '%s' from '%s': %s / %s" % \
                    (path, cvsroot, output, error))
        return output

    def getcleanfile(self, revision=None):
        """Get the content of the file for the given revision"""
        parentdir = os.path.dirname(self.location_abs)
        cvsdir = os.path.join(parentdir, "CVS")
        cvsroot = open(os.path.join(cvsdir, "Root"), "r").read().strip()
        cvspath = open(os.path.join(cvsdir, "Repository"), "r").read().strip()
        cvsfilename = os.path.join(cvspath, os.path.basename(self.location_abs))
        if revision is None:
            cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
            revision = self._getcvstag(cvsentries)
        if revision == "BASE":
            cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
            revision = self._getcvsrevision(cvsentries)
        return self._readfile(cvsroot, cvsfilename, revision)

    def update(self, revision=None):
        """Does a clean update of the given path"""
        working_dir = os.path.dirname(self.location_abs)
        filename = self.location_abs
        filename_backup = filename + os.path.extsep + "bak"
        # rename the file to be updated
        try:
            os.rename(filename, filename_backup)
        except OSError, error:
            raise IOError("[CVS] could not move the file '%s' to '%s': %s" % \
                    (filename, filename_backup, error))
        command = ["cvs", "-Q", "update", "-C"]
        if revision:
            command.extend(["-r", revision])
        # the filename is the last argument
        command.append(os.path.basename(filename))
        # run the command within the given working_dir
        exitcode, output, error = run_command(command, working_dir)
        # restore backup in case of an error - remove backup for success
        try:
            if exitcode != 0:
                os.rename(filename_backup, filename)
            else:
                os.remove(filename_backup)
        except OSError:
            pass
        # raise an error or return successfully - depending on the CVS command
        if exitcode != 0:
            raise IOError("[CVS] Error running CVS command '%s': %s" \
                    % (command, error))
        else:
            return output

    def commit(self, message=None, author=None):
        """Commits the file and supplies the given commit message if present
        
        the 'author' parameter is not suitable for CVS, thus it is ignored
        """
        working_dir = os.path.dirname(self.location_abs)
        filename = os.path.basename(self.location_abs)
        command = ["cvs", "-Q", "commit"]
        if message:
            command.extend(["-m", message])
        # the filename is the last argument
        command.append(filename)
        exitcode, output, error = run_command(command, working_dir)
        # raise an error or return successfully - depending on the CVS command
        if exitcode != 0:
            raise IOError("[CVS] Error running CVS command '%s': %s" \
                    % (command, error))
        else:
            return output

    def _getcvsrevision(self, cvsentries):
        """returns the revision number the file was checked out with by looking
        in the lines of cvsentries
        """
        filename = os.path.basename(self.location_abs)
        for cvsentry in cvsentries:
            # an entries line looks like the following:
            #  /README.TXT/1.19/Sun Dec 16 06:00:12 2001//
            cvsentryparts = cvsentry.split("/")
            if len(cvsentryparts) < 6:
                continue
            if os.path.normcase(cvsentryparts[1]) == os.path.normcase(filename):
                return cvsentryparts[2].strip()
        return None

    def _getcvstag(self, cvsentries):
        """Returns the sticky tag the file was checked out with by looking in 
        the lines of cvsentries.
        """
        filename = os.path.basename(self.location_abs)
        for cvsentry in cvsentries:
            # an entries line looks like the following:
            #  /README.TXT/1.19/Sun Dec 16 06:00:12 2001//
            cvsentryparts = cvsentry.split("/")
            if len(cvsentryparts) < 6:
                continue
            if os.path.normcase(cvsentryparts[1]) == os.path.normcase(filename):
                if cvsentryparts[5].startswith("T"):
                    return cvsentryparts[5][1:].strip()
        return None

