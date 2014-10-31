#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of translate.
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

"""Convert template files (like .pot or template .xlf files) translation files,
preserving existing translations.

See: http://translate.sourceforge.net/wiki/toolkit/pot2po for examples and
usage instructions.
"""

from translate.storage import factory
from translate.search import match
from translate.misc.multistring import multistring
from translate.tools import pretranslate
from translate.storage import poheader


def convertpot(input_file, output_file, template_file, tm=None, min_similarity=75, fuzzymatching=True, classes=factory.classes, **kwargs):
    """Main conversion function"""

    input_store = factory.getobject(input_file, classes=classes)
    template_store = None
    if template_file is not None:
        template_store = factory.getobject(template_file, classes=classes)
    output_store = convert_stores(input_store, template_store, tm, min_similarity, fuzzymatching, **kwargs)
    output_file.write(str(output_store))
    return 1

def convert_stores(input_store, template_store, tm=None, min_similarity=75, fuzzymatching=True, **kwargs):
    """Actual conversion function, works on stores not files, returns
    a properly initialized pretranslated output store, with structure
    based on input_store, metadata based on template_store, migrates
    old translations from template_store and pretranslating from tm"""

    #prepare for merging
    output_store = type(input_store)()
    #create fuzzy matchers to be used by pretranslate.pretranslate_unit
    matchers = []
    _prepare_merge(input_store, output_store, template_store)
    if fuzzymatching:
        if template_store:
            matcher = match.matcher(template_store, max_candidates=1, min_similarity=min_similarity, max_length=3000, usefuzzy=True)
            matcher.addpercentage = False
            matchers.append(matcher)
        if tm:
            matcher = pretranslate.memory(tm, max_candidates=1, min_similarity=min_similarity, max_length=1000)
            matcher.addpercentage = False
            matchers.append(matcher)

    #initialize store
    _store_pre_merge(input_store, output_store, template_store)

    # Do matching
    for input_unit in input_store.units:
        if input_unit.istranslatable():
            input_unit = pretranslate.pretranslate_unit(input_unit, template_store, matchers, mark_reused=True)
            _unit_post_merge(input_unit, input_store, output_store, template_store)
            output_store.addunit(input_unit)

    #finalize store
    _store_post_merge(input_store, output_store, template_store)

    return output_store


##dispatchers
def _prepare_merge(input_store, output_store, template_store, **kwargs):
    """Prepare stores & TM matchers before merging."""
    #dispatch to format specific functions
    prepare_merge_hook = "_prepare_merge_%s" % input_store.__class__.__name__
    if  globals().has_key(prepare_merge_hook):
        globals()[prepare_merge_hook](input_store, output_store, template_store, **kwargs)

    #generate an index so we can search by source string and location later on
    input_store.makeindex()
    if template_store:
        template_store.makeindex()


def _store_pre_merge(input_store, output_store, template_store, **kwargs) :
    """Initialize the new file with things like headers and metadata."""
    #formats that implement poheader interface are a special case
    if isinstance(input_store, poheader.poheader):
        _do_poheaders(input_store, output_store, template_store)

    #dispatch to format specific functions
    store_pre_merge_hook = "_store_pre_merge_%s" % input_store.__class__.__name__
    if  globals().has_key(store_pre_merge_hook):
        globals()[store_pre_merge_hook](input_store, output_store, template_store, **kwargs)


def _store_post_merge(input_store, output_store, template_store, **kwargs) :
    """Close file after merging all translations, used for adding
    statistics, obsolete messages and similar wrapup tasks."""
    #dispatch to format specific functions
    store_post_merge_hook = "_store_post_merge_%s" % input_store.__class__.__name__
    if  globals().has_key(store_post_merge_hook):
        globals()[store_post_merge_hook](input_store, output_store, template_store, **kwargs)

def _unit_post_merge(input_unit, input_store, output_store, template_store, **kwargs):
    """Handle any unit level cleanup and situations not handled by the merge()
    function."""
    #dispatch to format specific functions
    unit_post_merge_hook = "_unit_post_merge_%s" % input_unit.__class__.__name__
    if  globals().has_key(unit_post_merge_hook):
        globals()[unit_post_merge_hook](input_unit, input_store, output_store, template_store, **kwargs)


##format specific functions
def _prepare_merge_pofile(input_store, output_store, template_store):
    """PO format specific template preparation logic."""
    #we need to revive obsolete units to be able to consider
    #their translation when matching
    if template_store:
        for unit in template_store.units:
            if unit.isobsolete():
                unit.resurrect()


def _unit_post_merge_pounit(input_unit, input_store, output_store, template_store):
    """PO format specific plural string initializtion logic."""
    #FIXME: do we want to do that for poxliff also?
    if input_unit.hasplural() and len(input_unit.target) == 0:
        # untranslated plural unit; Let's ensure that we have the correct number of plural forms:
        nplurals, plural = output_store.getheaderplural()
        if nplurals and nplurals.isdigit() and nplurals != '2':
            input_unit.target = multistring([""]*int(nplurals))


def _store_post_merge_pofile(input_store, output_store, template_store):
    """PO format specific: adds newly obsoleted messages to end of store."""
    #Let's take care of obsoleted messages
    if template_store:
        newlyobsoleted = []
        for unit in template_store.units:
            if unit.isheader():
                continue
            if unit.target and not (input_store.findunit(unit.source) or hasattr(unit, "reused")):
                #not in .pot, make it obsolete
                unit.makeobsolete()
                newlyobsoleted.append(unit)
            elif unit.isobsolete():
                output_store.addunit(unit)
        for unit in newlyobsoleted:
            output_store.addunit(unit)


def _do_poheaders(input_store, output_store, template_store):
    """Adds initialized PO headers to output store."""
    # header values
    charset = "UTF-8"
    encoding = "8bit"
    project_id_version = None
    pot_creation_date = None
    po_revision_date = None
    last_translator = None
    language_team = None
    mime_version = None
    plural_forms = None
    kwargs = {}

    if template_store is not None and isinstance(template_store, poheader.poheader):
        templateheadervalues = template_store.parseheader()
        for key, value in templateheadervalues.iteritems():
            if key == "Project-Id-Version":
                project_id_version = value
            elif key == "Last-Translator":
                last_translator = value
            elif key == "Language-Team":
                language_team = value
            elif key == "PO-Revision-Date":
                po_revision_date = value
            elif key in ("POT-Creation-Date", "MIME-Version"):
                # don't know how to handle these keys, or ignoring them
                pass
            elif key == "Content-Type":
                kwargs[key] = value
            elif key == "Content-Transfer-Encoding":
                encoding = value
            elif key == "Plural-Forms":
                plural_forms = value
            else:
                kwargs[key] = value

    inputheadervalues = input_store.parseheader()
    for key, value in inputheadervalues.iteritems():
        if key in ("Project-Id-Version", "Last-Translator", "Language-Team", "PO-Revision-Date", "Content-Type", "Content-Transfer-Encoding", "Plural-Forms"):
            # want to carry these from the template so we ignore them
            pass
        elif key == "POT-Creation-Date":
            pot_creation_date = value
        elif key == "MIME-Version":
            mime_version = value
        else:
            kwargs[key] = value

    output_header = output_store.init_headers(charset=charset, encoding=encoding, project_id_version=project_id_version,
        pot_creation_date=pot_creation_date, po_revision_date=po_revision_date, last_translator=last_translator,
        language_team=language_team, mime_version=mime_version, plural_forms=plural_forms, **kwargs)

    # Get the header comments and fuzziness state

    # initial values from pot file
    input_header = input_store.header()
    if input_header is not None:
        if input_header.getnotes("developer"):
            output_header.addnote(input_header.getnotes("developer"), origin="developer", position="replace")
        if input_header.getnotes("translator"):
            output_header.addnote(input_header.getnotes("translator"), origin="translator", position="replace")
        output_header.markfuzzy(input_header.isfuzzy())

    # override some values from input file
    if template_store is not None:
        template_header = template_store.header()
        if template_header is not None:
            if template_header.getnotes("translator"):
                output_header.addnote(template_header.getnotes("translator"), "translator")
            output_header.markfuzzy(template_header.isfuzzy())


def main(argv=None):
    from translate.convert import convert
    formats = {"pot": ("po", convertpot), ("pot", "po"): ("po", convertpot),
               "xlf": ("xlf", convertpot), ("xlf", "xlf"): ("xlf", convertpot),
            }
    parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, 
        allowmissingtemplate=True, description=__doc__)
    parser.add_option("", "--tm", dest="tm", default=None,
        help="The file to use as translation memory when fuzzy matching")
    parser.passthrough.append("tm")
    defaultsimilarity = 75
    parser.add_option("-s", "--similarity", dest="min_similarity", default=defaultsimilarity,
        type="float", help="The minimum similarity for inclusion (default: %d%%)" % defaultsimilarity)
    parser.passthrough.append("min_similarity")
    parser.add_option("--nofuzzymatching", dest="fuzzymatching", action="store_false", 
        default=True, help="Disable fuzzy matching")
    parser.passthrough.append("fuzzymatching")
    parser.run(argv)


if __name__ == '__main__':
    main()
