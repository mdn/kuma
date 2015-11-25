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

"""Factory methods to convert supported input files to supported translatable files."""

import os


#from translate.convert import prop2po, po2prop, odf2xliff, xliff2odf


__all__ = ['converters', 'UnknownExtensionError', 'UnsupportedConversionError']

# Turn into property to support lazy loading of things?
converters = {}
#for module in (prop2po, po2prop, odf2xliff, xliff2odf):
#    if not hasattr(module, 'formats'):
#        continue
#    for extension in module.formats:
#        if extension not in converters:
#            converters[extension] = []
#        converters[extension].append(module.formats[extension])


class UnknownExtensionError(Exception):

    def __init__(self, afile):
        self.file = afile

    def __str__(self):
        return 'Unable to find extension for file: %s' % (self.file)

    def __unicode__(self):
        return unicode(str(self))


class UnsupportedConversionError(Exception):

    def __init__(self, in_ext=None, out_ext=None, templ_ext=None):
        self.in_ext = in_ext
        self.out_ext = out_ext
        self.templ_ext = templ_ext

    def __str__(self):
        msg = "Unsupported conversion from %s to %s" % (self.in_ext, self.out_ext)
        if self.templ_ext:
            msg += ' with template %s' % (self.templ_ext)
        return msg

    def __unicode__(self):
        return unicode(str(self))


def get_extension(filename):
    path, fname = os.path.split(filename)
    ext = fname.split(os.extsep)[-1]
    if ext == fname:
        return None
    return ext


def get_converter(in_ext, out_ext=None, templ_ext=None):
    convert_candidates = None
    if templ_ext:
        if (in_ext, templ_ext) in converters:
            convert_candidates = converters[(in_ext, templ_ext)]
        else:
            raise UnsupportedConversionError(in_ext, out_ext, templ_ext)
    else:
        if in_ext in converters:
            convert_candidates = converters[in_ext]
        elif (in_ext,) in converters:
            convert_candidates = converters[(in_ext,)]
        else:
            raise UnsupportedConversionError(in_ext, out_ext)

    convert_fn = None
    if not out_ext:
        out_ext, convert_fn = convert_candidates[0]
    else:
        for ext, func in convert_candidates:
            if ext == out_ext:
                convert_fn = func
                break

    if not convert_fn:
        raise UnsupportedConversionError(in_ext, out_ext, templ_ext)
    return convert_fn


def get_output_extensions(ext):
    """Compiles a list of possible output extensions for the given input extension."""
    out_exts = []
    for key in converters:
        in_ext = key
        if isinstance(key, tuple):
            in_ext = key[0]
        if in_ext == ext:
            for out_ext, convert_fn in converters[key]:
                out_exts.append(out_ext)
    return out_exts


def convert(inputfile, template=None, options=None, convert_options=None):
    """Convert the given input file to an appropriate output format, optionally
        using the given template file and further options.

        If the output extension (format) cannot be inferred the first converter
        that can handle the input file (and the format/extension it gives as
        output) is used.

        :type  inputfile: file
        :param inputfile: The input file to be converted
        :type  template: file
        :param template: Template file to use during conversion
        :type  options: dict (default: None)
        :param options: Valid options are:
            - in_ext: The extension (format) of the input file.
            - out_ext: The extension (format) to use for the output file.
            - templ_ext: The extension (format) of the template file.
            - in_fname: File name of the input file; used only to determine
              the input file extension (format).
            - templ_fname: File name of the template file; used only to
              determine the template file extension (format).
        :returns: a 2-tuple: The new output file (in a temporary directory) and
                  the extension (format) of the output file. The caller is
                  responsible for deleting the (temporary) output file."""
    in_ext, out_ext, templ_ext = None, None, None

    # Get extensions from options
    if options is None:
        options = {}
    else:
        if 'in_ext' in options:
            in_ext = options['in_ext']
        if 'out_ext' in options:
            out_ext = options['out_ext']
        if template and 'templ_ext' in options:
            templ_ext = options['templ_ext']

        # If we still do not have extensions, try and get it from the *_fname options
        if not in_ext and 'in_fname' in options:
            in_ext = get_extension(options['in_fname'])
        if template and not templ_ext and 'templ_fname' in options:
            templ_fname = get_extension(options['templ_fname'])

    # If we still do not have extensions, get it from the file names
    if not in_ext and hasattr(inputfile, 'name'):
        in_ext = get_extension(inputfile.name)
    if template and not templ_ext and hasattr(template, 'name'):
        templ_ext = get_extension(template.name)

    if not in_ext:
        raise UnknownExtensionError(inputfile)
    if template and not templ_ext:
        raise UnknownExtensionError(template)

    out_ext_candidates = get_output_extensions(in_ext)
    if not out_ext_candidates:
        # No converters registered for the in_ext we have
        raise UnsupportedConversionError(in_ext=in_ext, templ_ext=templ_ext)
    if out_ext and out_ext not in out_ext_candidates:
        # If out_ext has a value at this point, it was given in options, so
        # we just take a second to make sure that the conversion is supported.
        raise UnsupportedConversionError(in_ext, out_ext, templ_ext)

    if not out_ext and templ_ext in out_ext_candidates:
        # If we're using a template, chances are (pretty damn) good that the
        # output file will be of the same type
        out_ext = templ_ext
    else:
        # As a last resort, we'll just use the first possible output format
        out_ext = out_ext_candidates[0]

    # XXX: We are abusing tempfile.mkstemp() below: we are only using it to
    #      obtain a temporary file name to use the normal open() with. This is
    #      done because a tempfile.NamedTemporaryFile simply gave too many
    #      issues when being closed (and deleted) by the rest of the toolkit
    #      (eg. TranslationStore.savefile()). Therefore none of mkstemp()'s
    #      security features are being utilised.
    import tempfile
    tempfd, tempfname = tempfile.mkstemp(prefix='ttk_convert', suffix=os.extsep + out_ext)
    os.close(tempfd)
    outputfile = open(tempfname, 'w')

    if convert_options is None:
        convert_options = {}
    get_converter(in_ext, out_ext, templ_ext)(inputfile, outputfile, template, **convert_options)
    if hasattr(outputfile, 'closed') and hasattr(outputfile, 'close') and not outputfile.closed:
        outputfile.close()
    return outputfile, out_ext
