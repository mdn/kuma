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

from translate.convert import factory as convert_factory
from translate.storage.projstore import ProjectStore


__all__ = ['Project']


def split_extensions(filename):
    """Split the given filename into a name and extensions part.
        The extensions part is defined by any sequence of extensions, where an
        extension is a 3-letter, .-separated string or one of "po" or
        "properties". If the file name consists entirely out of extensions, the
        first part is assumed to be the file name and the rest extensions."""
    # FIXME: Isn't there a better place for this function?
    # XXX: Make sure that all extensions supported in translate.convert.factory
    #      that are not 3 letters long are added to the first "if" statement in
    #      split_extensions() below.
    filename_parts = filename.split(os.extsep)
    extensions = []
    for part in reversed(filename_parts):
        if len(part) != 3 and part not in ('po', 'properties'):
            break
        extensions.append(part)
    if not extensions:
        return filename, ''
    extensions = [x for x in reversed(extensions)]

    if len(extensions) == len(filename_parts):
        extensions = extensions[1:]
    return os.extsep.join(filename_parts[:-len(extensions)]), os.extsep.join(extensions)


class Project(object):
    """Manages a project store as well as the processes involved in a project
        workflow."""

    # INITIALIZERS #
    def __init__(self, projstore=None):
        if projstore is None:
            projstore = ProjectStore()
        self.store = projstore

    def __del__(self):
        if self.store:
            del self.store

    # METHODS #
    def add_source(self, srcfile, src_fname=None):
        """Proxy for ``self.store.append_sourcefile()``."""
        return self.store.append_sourcefile(srcfile, src_fname)

    def add_source_convert(self, srcfile, src_fname=None, convert_options=None, extension=None):
        """Convenience method that calls :meth:`~Project.add_source` and
        :meth:`~Project.convert_forward` and returns the results from both."""
        srcfile, srcfname = self.add_source(srcfile, src_fname)
        transfile, transfname = self.convert_forward(srcfname, convert_options=convert_options)
        return srcfile, srcfname, transfile, transfname

    def close(self):
        """Proxy for ``self.store.close()``."""
        self.store.close()

    def convert_forward(self, input_fname, template=None, output_fname=None, **options):
        """Convert the given input file to the next type in the process:

        Source document (eg. ODT) -> Translation file (eg. XLIFF) ->
        Translated document (eg. ODT).

        :type  input_fname: basestring
        :param input_fname: The project name of the file to convert
        :type  convert_options: dict (optional)
        :param convert_options: Passed as-is to
                                :meth:`translate.convert.factory.convert`.
        :returns 2-tuple: the converted file object and its project name."""
        inputfile = self.get_file(input_fname)
        input_type = self.store.get_filename_type(input_fname)

        if input_type == 'tgt':
            raise ValueError('Cannot convert a target document further: %s' % (input_fname))

        templ_fname = None
        if isinstance(template, basestring):
            template, templ_fname = self.get_file(template)

        if template and not templ_fname:
            templ_fname = template.name

        # Check if we can determine a template from the conversion map
        if template is None:
            convert_map = self.store.convert_map
            if input_fname in convert_map:
                templ_fname = convert_map[input_fname][1]
                template = self.get_file(templ_fname)
            elif input_type == 'trans':
                # inputfile is a translatable file, so it needed to be converted
                # from some input document. Let's try and use that document as a
                # template for this conversion.
                for in_name, (out_name, tmpl_name) in self.store.convert_map.items():
                    if input_fname == out_name:
                        template, templ_fname = self.get_file(in_name), in_name
                        break

        # Populate the conv_options dict with the options we can detect
        conv_options = dict(in_fname=input_fname)

        if input_fname in self.store.convert_map:
            out_name, tmpl_name = self.store.convert_map[input_fname]
            if out_name in self.store._files and options.get('overwrite_output', True):
                self.remove_file(out_name)

        converted_file, converted_ext = convert_factory.convert(
            inputfile,
            template=template,
            options=conv_options,
            convert_options=options.get('convert_options', None))

        # Determine the file name and path where the output should be moved.
        if not output_fname:
            _dir, fname = os.path.split(input_fname)
            directory = ''
            if hasattr(inputfile, 'name'):
                # Prefer to put it in the same directory as the input file
                directory, _fn = os.path.split(inputfile.name)
            else:
                # Otherwise put it in the current working directory
                directory = os.getcwd()
            output_fname = os.path.join(directory, fname)
        output_fname, output_ext = split_extensions(output_fname)
        output_ext_parts = output_ext.split(os.extsep)

        # Add the output suffix, if supplied
        if 'output_suffix' in options:
            output_fname += options['output_suffix']

        # Check if we are in the situation where the output has an extension
        # of, for example, .odt.xlf.odt. If so, we want to change that to only
        # .odt.
        if len(output_ext_parts) >= 2 and output_ext_parts[-2] == converted_ext:
            output_ext_parts = output_ext_parts[:-1]
        else:
            output_ext_parts.append(converted_ext)
        output_fname += os.extsep.join([''] + output_ext_parts)

        if os.path.isfile(output_fname):
            # If the output file already exist, we can't assume that it's safe
            # to overwrite it.
            os.unlink(converted_file.name)
            raise IOError("Output file already exists: %s" % (output_fname))

        os.rename(converted_file.name, output_fname)

        output_type = self.store.TYPE_INFO['next_type'][input_type]
        outputfile, output_fname = self.store.append_file(
            output_fname, None, ftype=output_type, delete_orig=True)
        self.store.convert_map[input_fname] = (output_fname, templ_fname)

        return outputfile, output_fname

    def export_file(self, fname, destfname):
        """Export the file with the specified filename to the given destination.
            This method will raise
            :exc:`~translate.storage.projstore.FileNotInProjectError`
            via the call to
            :meth:`~translate.storage.projstore.ProjectStore.get_file`
            if *fname* is not found in the project."""
        open(destfname, 'w').write(self.store.get_file(fname).read())

    def get_file(self, fname):
        """Proxy for ``self.store.get_file()``."""
        return self.store.get_file(fname)

    def get_proj_filename(self, realfname):
        """Proxy for ``self.store.get_proj_filename()``."""
        return self.store.get_proj_filename(realfname)

    def get_real_filename(self, projfname):
        """Try and find a real file name for the given project file name."""
        projfile = self.get_file(projfname)
        rfname = getattr(projfile, 'name', getattr(projfile, 'filename', None))
        if rfname is None:
            raise ValueError('Project file has no real file: %s' % (projfname))
        return rfname

    def remove_file(self, projfname, ftype=None):
        """Proxy for ``self.store.remove_file()``."""
        self.store.remove_file(projfname, ftype)

    def save(self, filename=None):
        """Proxy for ``self.store.save()``."""
        self.store.save(filename)

    def update_file(self, proj_fname, infile):
        """Proxy for ``self.store.update_file()``."""
        self.store.update_file(proj_fname, infile)
