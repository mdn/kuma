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

from lxml import etree


__all__ = ['FileExistsInProjectError', 'FileNotInProjectError', 'ProjectStore']


class FileExistsInProjectError(Exception):
    pass


class FileNotInProjectError(Exception):
    pass


class ProjectStore(object):
    """Basic project file container."""

    # INITIALIZERS #
    def __init__(self):
        self._files = {}
        self._sourcefiles = []
        self._targetfiles = []
        self._transfiles = []
        self.settings = {}
        self.convert_map = {}
        # The above map maps the conversion of input files (keys) to its output
        # file and template used (2-tuple). All values are project file names.
        # eg. convert_map = {
        #    'sources/doc.odt':   ('trans/doc.odt.xlf', None),
        #    'trans/doc.odt.xlf': ('targets/doc.odt', 'sources/doc.odt')
        #}

        # The following dict groups together sets of mappings from a file
        # "type" string ("src", "tgt" or "trans") to various other values
        # or objects.
        self.TYPE_INFO = {
            # type => prefix for new files
            'f_prefix': {
                'src': 'sources/',
                'tgt': 'targets/',
                'trans': 'trans/',
            },
            # type => list containing filenames for that type
            'lists': {
                'src': self._sourcefiles,
                'tgt': self._targetfiles,
                'trans': self._transfiles,
            },
            # type => next type in process: src => trans => tgt
            'next_type': {
                'src': 'trans',
                'trans': 'tgt',
                'tgt': None,
            },
            # type => name of the sub-section in the settings file/dict
            'settings': {
                'src': 'sources',
                'tgt': 'targets',
                'trans': 'transfiles',
            }
        }

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # ACCESSORS #
    def _get_sourcefiles(self):
        """Read-only access to ``self._sourcefiles``."""
        return tuple(self._sourcefiles)
    sourcefiles = property(_get_sourcefiles)

    def _get_targetfiles(self):
        """Read-only access to ``self._targetfiles``."""
        return tuple(self._targetfiles)
    targetfiles = property(_get_targetfiles)

    def _get_transfiles(self):
        """Read-only access to ``self._transfiles``."""
        return tuple(self._transfiles)
    transfiles = property(_get_transfiles)

    # SPECIAL METHODS #
    def __in__(self, lhs):
        """@returns ``True`` if ``lhs`` is a file name or file object in the project store."""
        return lhs in self._sourcefiles or \
               lhs in self._targetfiles or \
               lhs in self._transfiles or \
               lhs in self._files or \
               lhs in self._files.values()

    # METHODS #
    def append_file(self, afile, fname, ftype='trans', delete_orig=False):
        """Append the given file to the project with the given filename, marked
            to be of type ``ftype`` ('src', 'trans', 'tgt').

            :type  delete_orig: bool
            :param delete_orig: Whether or not the original (given) file should
                                be deleted after being appended. This is set to
                                ``True`` by
                                :meth:`~translate.storage.project.convert_forward`
                                . Not used in this class."""
        if not ftype in self.TYPE_INFO['f_prefix']:
            raise ValueError('Invalid file type: %s' % (ftype))

        if isinstance(afile, basestring) and os.path.isfile(afile) and not fname:
            # Try and use afile as the file name
            fname, afile = afile, open(afile)

        # Check if we can get an real file name
        realfname = fname
        if realfname is None or not os.path.isfile(realfname):
            realfname = getattr(afile, 'name', None)
        if realfname is None or not os.path.isfile(realfname):
            realfname = getattr(afile, 'filename', None)
        if not realfname or not os.path.isfile(realfname):
            realfname = None

        # Try to get the file name from the file object, if it was not given:
        if not fname:
            fname = getattr(afile, 'name', None)
        if not fname:
            fname = getattr(afile, 'filename', None)

        fname = self._fix_type_filename(ftype, fname)

        if not fname:
            raise ValueError('Could not deduce file name and none given')
        if fname in self._files:
            raise FileExistsInProjectError(fname)

        if realfname is not None and os.path.isfile(realfname):
            self._files[fname] = realfname
        else:
            self._files[fname] = afile
        self.TYPE_INFO['lists'][ftype].append(fname)

        return afile, fname

    def append_sourcefile(self, afile, fname=None):
        return self.append_file(afile, fname, ftype='src')

    def append_targetfile(self, afile, fname=None):
        return self.append_file(afile, fname, ftype='tgt')

    def append_transfile(self, afile, fname=None):
        return self.append_file(afile, fname, ftype='trans')

    def remove_file(self, fname, ftype=None):
        """Remove the file with the given project name from the project.
            If the file type ('src', 'trans' or 'tgt') is not given, it is
            guessed."""
        if fname not in self._files:
            raise FileNotInProjectError(fname)
        if not ftype:
            # Guess file type (source/trans/target)
            for ft, prefix in self.TYPE_INFO['f_prefix'].items():
                if fname.startswith(prefix):
                    ftype = ft
                    break

        self.TYPE_INFO['lists'][ftype].remove(fname)
        if self._files[fname] and hasattr(self._files[fname], 'close'):
            self._files[fname].close()
        del self._files[fname]

    def remove_sourcefile(self, fname):
        self.remove_file(fname, ftype='src')

    def remove_targetfile(self, fname):
        self.remove_file(fname, ftype='tgt')

    def remove_transfile(self, fname):
        self.remove_file(fname, ftype='trans')

    def close(self):
        self.save()

    def get_file(self, fname, mode='rb'):
        """Retrieve the file with the given name from the project store.

        The file is looked up in the ``self._files`` dictionary. The values
        in this dictionary may be ``None``, to indicate that the file is not
        cacheable and needs to be retrieved in a special way. This special
        way must be defined in this method of sub-classes. The value may
        also be a string, which indicates that it is a real file accessible
        via ``open``.

        :type  mode: str
        :param mode: The mode in which to re-open the file (if it is closed).
        """
        if fname not in self._files:
            raise FileNotInProjectError(fname)

        rfile = self._files[fname]
        if isinstance(rfile, basestring):
            rfile = open(rfile, 'rb')
        # Check that the file is actually open
        if getattr(rfile, 'closed', False):
            rfname = fname
            if not os.path.isfile(rfname):
                rfname = getattr(rfile, 'name', None)
            if not rfile or not os.path.isfile(rfname):
                rfname = getattr(rfile, 'filename', None)
            if not rfile or not os.path.isfile(rfname):
                raise IOError('Could not locate file: %s (%s)' % (rfile, fname))
            rfile = open(rfname, mode)
            self._files[fname] = rfile

        return rfile

    def get_filename_type(self, fname):
        """Get the type of file ('src', 'trans', 'tgt') with the given name."""
        for ftype in self.TYPE_INFO['lists']:
            if fname in self.TYPE_INFO['lists'][ftype]:
                return ftype
        raise FileNotInProjectError(fname)

    def get_proj_filename(self, realfname):
        """Try and find a project file name for the given real file name."""
        for fname in self._files:
            if fname == realfname or self._files[fname] == realfname:
                return fname
        raise ValueError('Real file not in project store: %s' % (realfname))

    def load(self, *args, **kwargs):
        """Load the project in some way. Undefined for this (base) class."""
        pass

    def save(self, filename=None, *args, **kwargs):
        """Save the project in some way. Undefined for this (base) class."""
        pass

    def update_file(self, pfname, infile):
        """Remove the project file with name ``pfname`` and add the contents
            from ``infile`` to the project under the same file name.

            :returns: the results from :meth:`ProjectStore.append_file`."""
        ftype = self.get_filename_type(pfname)
        self.remove_file(pfname)
        self.append_file(infile, pfname, ftype)

    def _fix_type_filename(self, ftype, fname):
        """Strip the path from the filename and prepend the correct prefix."""
        path, fname = os.path.split(fname)
        return self.TYPE_INFO['f_prefix'][ftype] + fname

    def _generate_settings(self):
        """@returns A XML string that represents the current settings."""
        xml = etree.Element('translationproject')

        # Add file names to settings XML
        if self._sourcefiles:
            sources_el = etree.Element('sources')
            for fname in self._sourcefiles:
                src_el = etree.Element('filename')
                src_el.text = fname
                sources_el.append(src_el)
            xml.append(sources_el)
        if self._transfiles:
            transfiles_el = etree.Element('transfiles')
            for fname in self._transfiles:
                trans_el = etree.Element('filename')
                trans_el.text = fname
                transfiles_el.append(trans_el)
            xml.append(transfiles_el)
        if self._targetfiles:
            target_el = etree.Element('targets')
            for fname in self._targetfiles:
                tgt_el = etree.Element('filename')
                tgt_el.text = fname
                target_el.append(tgt_el)
            xml.append(target_el)

        # Add conversion mappings
        if self.convert_map:
            conversions_el = etree.Element('conversions')
            for in_fname, (out_fname, templ_fname) in self.convert_map.iteritems():
                if in_fname not in self._files or out_fname not in self._files:
                    continue
                conv_el = etree.Element('conv')

                input_el = etree.Element('input')
                input_el.text = in_fname
                conv_el.append(input_el)

                output_el = etree.Element('output')
                output_el.text = out_fname
                conv_el.append(output_el)

                if templ_fname:
                    templ_el = etree.Element('template')
                    templ_el.text = templ_fname
                    conv_el.append(templ_el)

                conversions_el.append(conv_el)
            xml.append(conversions_el)

        # Add options to settings
        if 'options' in self.settings:
            options_el = etree.Element('options')
            for option, value in self.settings['options'].items():
                opt_el = etree.Element('option')
                opt_el.attrib['name'] = option
                opt_el.text = value
                options_el.append(opt_el)
            xml.append(options_el)

        return etree.tostring(xml, pretty_print=True)

    def _load_settings(self, settingsxml):
        """Load project settings from the given XML string.
        ``settingsxml`` is parsed into a DOM tree (``lxml.etree.fromstring``)
        which is then inspected."""
        settings = {}
        xml = etree.fromstring(settingsxml)

        # Load files in project
        for section in ('sources', 'targets', 'transfiles'):
            groupnode = xml.find(section)
            if groupnode is None:
                continue

            settings[section] = []
            for fnode in groupnode.getchildren():
                settings[section].append(fnode.text)

        conversions_el = xml.find('conversions')
        if conversions_el is not None:
            self.convert_map = {}
            for conv_el in conversions_el.iterchildren():
                in_fname, out_fname, templ_fname = None, None, None
                for child_el in conv_el.iterchildren():
                    if child_el.tag == 'input':
                        in_fname = child_el.text
                    elif child_el.tag == 'output':
                        out_fname = child_el.text
                    elif child_el.tag == 'template':
                        templ_fname = child_el.text
                # Make sure that in_fname and out_fname exist in
                # settings['sources'], settings['targets'] or
                # settings['transfiles']
                in_found, out_found, templ_found = False, False, False
                for section in ('sources', 'transfiles', 'targets'):
                    if section not in settings:
                        continue
                    if in_fname in settings[section]:
                        in_found = True
                    if out_fname in settings[section]:
                        out_found = True
                    if templ_fname and templ_fname in settings[section]:
                        templ_found = True
                if in_found and out_found and (not templ_fname or templ_found):
                    self.convert_map[in_fname] = (out_fname, templ_fname)

        # Load options
        groupnode = xml.find('options')
        if groupnode is not None:
            settings['options'] = {}
            for opt in groupnode.iterchildren():
                settings['options'][opt.attrib['name']] = opt.text

        self.settings = settings
