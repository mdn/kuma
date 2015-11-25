#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import tempfile
from zipfile import ZipFile

from translate.storage.projstore import *


__all__ = ['BundleProjectStore', 'InvalidBundleError']


class InvalidBundleError(Exception):
    pass


class BundleProjectStore(ProjectStore):
    """Represents a translate project bundle (zip archive)."""

    # INITIALIZERS #
    def __init__(self, fname):
        super(BundleProjectStore, self).__init__()
        self._tempfiles = {}
        if fname and os.path.isfile(fname):
            self.load(fname)
        else:
            self.zip = ZipFile(fname, 'w')
            self.save()
            self.zip.close()
            self.zip = ZipFile(fname, 'a')

    # CLASS METHODS #
    @classmethod
    def from_project(cls, proj, fname=None):
        if fname is None:
            fname = 'bundle.zip'

        bundle = BundleProjectStore(fname)
        for fn in proj.sourcefiles:
            bundle.append_sourcefile(proj.get_file(fn))
        for fn in proj.transfiles:
            bundle.append_transfile(proj.get_file(fn))
        for fn in proj.targetfiles:
            bundle.append_targetfile(proj.get_file(fn))
        bundle.settings = proj.settings.copy()
        bundle.save()
        return bundle

    # METHODS #
    def append_file(self, afile, fname, ftype='trans', delete_orig=False):
        """Append the given file to the project with the given filename, marked
            to be of type ``ftype`` ('src', 'trans', 'tgt').

            :param delete_orig: If ``True``, as set by
                                :meth:`~translate.storage.Project.convert_forward`,
                                ``afile`` is deleted after appending, if
                                possible.

            .. note:: For this implementation, the appended file will be deleted
                      from disk if ``delete_orig`` is ``True``.
            """
        if fname and fname in self.zip.namelist():
            raise ValueError("File already in bundle archive: %s" % (fname))
        if not fname and isinstance(afile, basestring) and afile in self.zip.namelist():
            raise ValueError("File already in bundle archive: %s" % (afile))

        afile, fname = super(BundleProjectStore, self).append_file(afile, fname, ftype)
        self._zip_add(fname, afile)

        if delete_orig and hasattr(afile, 'name') and afile.name not in self._tempfiles:
            try:
                os.unlink(afile.name)
            except Exception:
                pass

        return self.get_file(fname), fname

    def remove_file(self, fname, ftype=None):
        """Remove the file with the given project name from the project."""
        super(BundleProjectStore, self).remove_file(fname, ftype)
        self._zip_delete([fname])
        tempfiles = [tmpf for tmpf, prjf in self._tempfiles.iteritems() if prjf == fname]
        if tempfiles:
            for tmpf in tempfiles:
                try:
                    os.unlink(tmpf)
                except Exception:
                    pass
                del self._tempfiles[tmpf]

    def close(self):
        super(BundleProjectStore, self).close()
        self.cleanup()
        self.zip.close()

    def cleanup(self):
        """Clean up our mess: remove temporary files."""
        for tempfname in self._tempfiles:
            if os.path.isfile(tempfname):
                os.unlink(tempfname)
        self._tempfiles = {}

    def get_file(self, fname):
        """Retrieve a project file (source, translation or target file) from the
            project archive."""
        retfile = None
        if fname in self._files or fname in self.zip.namelist():
            # Check if the file has not already been extracted to a temp file
            tempfname = [tfn for tfn in self._tempfiles if self._tempfiles[tfn] == fname]
            if tempfname and os.path.isfile(tempfname[0]):
                tempfname = tempfname[0]
            else:
                tempfname = ''
            if not tempfname:
                # Extract the file to a temporary file
                zfile = self.zip.open(fname)
                tempfname = os.path.split(fname)[-1]
                tempfd, tempfname = tempfile.mkstemp(suffix='_' + tempfname)
                os.close(tempfd)
                open(tempfname, 'w').write(zfile.read())
            retfile = open(tempfname)
            self._tempfiles[tempfname] = fname

        if not retfile:
            raise FileNotInProjectError(fname)
        return retfile

    def get_proj_filename(self, realfname):
        """Try and find a project file name for the given real file name."""
        try:
            fname = super(BundleProjectStore, self).get_proj_filename(realfname)
        except ValueError as ve:
            fname = None
        if fname:
            return fname
        if realfname in self._tempfiles:
            return self._tempfiles[realfname]
        raise ValueError('Real file not in project store: %s' % (realfname))

    def load(self, zipname):
        """Load the bundle project from the zip file of the given name."""
        self.zip = ZipFile(zipname, mode='a')
        self._load_settings()

        append_section = {
            'sources': self._sourcefiles.append,
            'targets': self._targetfiles.append,
            'transfiles': self._transfiles.append,
        }
        for section in ('sources', 'targets', 'transfiles'):
            if section in self.settings:
                for fname in self.settings[section]:
                    append_section[section](fname)
                    self._files[fname] = None

    def save(self, filename=None):
        """Save all project files to the bundle zip file."""
        self._update_from_tempfiles()

        if filename:
            newzip = ZipFile(filename, 'w')
        else:
            newzip = self._create_temp_zipfile()

        # Write project file for the new zip bundle
        newzip.writestr('project.xtp', self._generate_settings())
        # Copy project files from project to the new zip file
        project_files = self._sourcefiles + self._transfiles + self._targetfiles
        for fname in project_files:
            newzip.writestr(fname, self.get_file(fname).read())
        # Copy any extra (non-project) files from the current zip
        for fname in self.zip.namelist():
            if fname in project_files or fname == 'project.xtp':
                continue
            newzip.writestr(fname, self.zip.read(fname))

        self._replace_project_zip(newzip)

    def update_file(self, pfname, infile):
        """Updates the file with the given project file name with the contents
            of ``infile``.

            :returns: the results from :meth:`BundleProjStore.append_file`."""
        if pfname not in self._files:
            raise FileNotInProjectError(pfname)

        if pfname not in self.zip.namelist():
            return super(BundleProjectStore, self).update_file(pfname, infile)

        self._zip_delete([pfname])
        self._zip_add(pfname, infile)

    def _load_settings(self):
        """Grab the project.xtp file from the zip file and load it."""
        if 'project.xtp' not in self.zip.namelist():
            raise InvalidBundleError('Not a translate project bundle')
        super(BundleProjectStore, self)._load_settings(self.zip.open('project.xtp').read())

    def _create_temp_zipfile(self):
        """Create a new zip file with a temporary file name (with mode 'w')."""
        newzipfd, newzipfname = tempfile.mkstemp(prefix='translate_bundle', suffix='.zip')
        os.close(newzipfd)
        return ZipFile(newzipfname, 'w')

    def _replace_project_zip(self, zfile):
        """Replace the currently used zip file (``self.zip``) with the given zip
            file. Basically, ``os.rename(zfile.filename, self.zip.filename)``."""
        if not zfile.fp.closed:
            zfile.close()
        if not self.zip.fp.closed:
            self.zip.close()
        shutil.move(zfile.filename, self.zip.filename)
        self.zip = ZipFile(self.zip.filename, mode='a')

    def _update_from_tempfiles(self):
        """Update project files from temporary files."""
        for tempfname in self._tempfiles:
            tmp = open(tempfname)
            self.update_file(self._tempfiles[tempfname], tmp)
            if not tmp.closed:
                tmp.close()

    def _zip_add(self, pfname, infile):
        """Add the contents of ``infile`` to the zip with file name ``pfname``."""
        if hasattr(infile, 'seek'):
            infile.seek(0)
        self.zip.writestr(pfname, infile.read())
        # Clear the cached file object to force the file to be read from the
        # zip file.
        self._files[pfname] = None

    def _zip_delete(self, fnames):
        """Delete the files with the given names from the zip file (``self.zip``)."""
        # Sanity checking
        if not isinstance(fnames, (list, tuple)):
            raise ValueError("fnames must be list or tuple: %s" % (fnames))
        if not self.zip:
            raise ValueError("No zip file to work on")
        zippedfiles = self.zip.namelist()
        for fn in fnames:
            if fn not in zippedfiles:
                raise KeyError("File not in zip archive: %s" % (fn))

        newzip = self._create_temp_zipfile()
        newzip.writestr('project.xtp', self._generate_settings())

        for fname in zippedfiles:
            # Copy all files from self.zip that are not project.xtp (already
            # in the new zip file) or in fnames (they are to be removed, after
            # all.
            if fname in fnames or fname == 'project.xtp':
                continue
            newzip.writestr(fname, self.zip.read(fname))

        self._replace_project_zip(newzip)
