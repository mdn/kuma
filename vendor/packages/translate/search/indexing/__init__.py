# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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
#


"""Interface for differrent indexing engines for the Translate Toolkit."""

import logging
import os
import shutil

import CommonIndexer


""" TODO for indexing engines:
    * get rid of jToolkit.glock dependency
    * add partial matching at the beginning of a term
    * do a proper cleanup - e.g.: the pylucene lockfiles remain in /tmp/
    * do unittests for PyLucene v1.x
    """


def _get_available_indexers():
    """get a list of the available supported indexing engines

    search through the translate.search.indexer package for modules derived from
    the CommonIndexer class
    """
    result = []
    # get the package directory
    indexer_dir = os.path.dirname(os.path.abspath(__file__))
    # sort the files in the directory by name - to make it determinable,
    # which indexing engine is chosen in case of multiple possibilities
    all_files = os.listdir(indexer_dir)
    all_files.sort()
    for mod_file in all_files:
        if mod_file == __file__:
            # we should not import ourself
            continue
        mod_path = os.path.join(indexer_dir, mod_file)
        if (not mod_path.endswith(".py") or
            not os.path.isfile(mod_path) or
            not os.access(mod_path, os.R_OK)):
            # no file / wrong extension / not readable -> skip it
            continue
        # strip the ".py" prefix
        mod_name = mod_file[:-3]
        # TODO - debug: "[Indexer]: trying to import indexing engines from '%s'" % mod_path
        try:
            module = __import__(mod_name, globals(), {})
        except ImportError:
            # maybe it is unusable or dependencies are missing
            continue
        # the module function "is_available" must return "True"
        if not (hasattr(module, "is_available") and
                callable(module.is_available) and
                module.is_available()):
            continue
        for item in dir(module):
            try:
                element = getattr(module, item)
            except TypeError:
                # this rarely happens: e.g. for 'item' being 'None'
                continue
            try:
                # the class must inherit CommonDatabase (without being the same)
                if issubclass(element, CommonIndexer.CommonDatabase) \
                        and not element is CommonIndexer.CommonDatabase:
                    # TODO: debug - "[Indexer]: indexing engine found in '%s': %s" % (mod_path, element)
                    # the interface is ok
                    result.append(element)
            except TypeError:
                # 'element' is not a class
                continue
    return result


def _sort_indexers_by_preference(indexer_classes, pref_order):
    """sort a given list of indexer classes according to the given order

    the list of preferred indexers are strings that should match the filenames
    (without suppix ".py") of the respective modules (e.g.: XapianIndexer or
    PyLuceneIndexer)

    :param indexer_classes: the list of all available indexer classes
    :type indexer_classes: list of CommonIndexer.CommonDatabase objects
    :param pref_order: list of preferred indexer names
    :type pref_order: str
    :return: sorted list of indexer classes
    :rtype: list of CommonIndexer.CommonDatabase objects
    """
    # define useful function for readability
    get_indexer_name = lambda indexer_class: \
            os.path.basename(indexer_class.__module__).split(".")[-1]
    # use a copy to avoid side effects
    avail_indexers = indexer_classes[:]
    result = []
    # go through all preferred items and move the matching indexers to 'result'
    for choice in pref_order:
        # find matching indexers
        matches = [indexer for indexer in avail_indexers
                   if get_indexer_name(indexer) == choice]
        # move all matching items to the 'result' queue
        for match_item in matches:
            result.append(match_item)
            avail_indexers.remove(match_item)
    # append the remaining indexers to the result
    return result + avail_indexers


# store the available indexers - this is done only once during the first import
_AVAILABLE_INDEXERS = _get_available_indexers()

# True for a not-empty list - this should be used to check if indexing support
# is available
HAVE_INDEXER = bool(_AVAILABLE_INDEXERS)


def get_indexer(basedir, preference=None):
    """return an appropriate indexer for the given directory

    If the directory already exists, then we check, if one of the available
    indexers knows how to handle it. Otherwise we return the first available
    indexer.

    :raise IndexError: there is no indexing engine available
    :raise ValueError: the database location already exists, but we did not find
                       a suitable indexing engine for it
    :raise OSError: any error that could occour while creating or opening the
                    database

    :param basedir: the parent directory of (possible) different indexing
             databases
    :type basedir: string
    :return: the class of the most appropriate indexer
    :rtype: subclass of :class:`CommonIndexer.CommonDatabase`
    """
    if not _AVAILABLE_INDEXERS:
        raise IndexError("Indexer: no indexing engines are available")
    if preference is None:
        preference = []
    # sort available indexers by preference
    preferred_indexers = _sort_indexers_by_preference(_AVAILABLE_INDEXERS,
                                                      preference)
    if os.path.exists(basedir):
        for index_class in preferred_indexers:
            try:
                # the first match is sufficient - but we do not want to
                # create a new database, if a database for another
                # indexing engine could exist. Thus we try it read-only first.
                return index_class(basedir, create_allowed=False)
            except (ValueError, OSError):
                # invalid type of database or some other error
                continue
        # the database does not exist yet or we did not find an appropriate
        # class that can handle it - so we remove the whole base directory
        shutil.rmtree(basedir, ignore_errors=True)
        logging.info("Deleting invalid indexing directory '%s'", basedir)

    # the database does not exist or it was deleted (see above)
    # we choose the first available indexing engine
    return preferred_indexers[0](basedir)


if __name__ == "__main__":
    # show all supported indexing engines (with fulfilled requirements)
    for ONE_INDEX in _AVAILABLE_INDEXERS:
        print(ONE_INDEX)
