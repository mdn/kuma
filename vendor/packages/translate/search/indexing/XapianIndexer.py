#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2011 Zuza Software Foundation
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

"""
Interface to the Xapian indexing engine for the Translate Toolkit

Xapian v1.0 or higher is supported.

If you are interested in writing an interface for Xapian 0.x, then
you should checkout the following::

    svn export -r 7235 https://translate.svn.sourceforge.net/svnroot/translate/src/branches/translate-search-indexer-generic-merging/translate/search/indexer/

It is not completely working, but it should give you a good start.
"""

# xapian module versions before 1.0.13 hangs apache under mod_python
import sys
import re

# detect if running under apache
if 'apache' in sys.modules or '_apache' in sys.modules or 'mod_wsgi' in sys.modules:

    def _str2version(version):
        return [int(i) for i in version.split('.')]

    import subprocess
    # even checking xapian version leads to deadlock under apache, must figure version from command line
    try:
        command = subprocess.Popen(['xapian-check', '--version'], stdout=subprocess.PIPE)
        stdout, stderr = command.communicate()
        if _str2version(re.match('.*([0-9]+\.[0-9]+\.[0-9]+).*', stdout).groups()[0]) < [1, 0, 13]:
            raise ImportError("Running under apache, can't load xapain")
    except:
        #FIXME: report is xapian-check command is missing?
        raise ImportError("Running under apache, can't load xapian")

import CommonIndexer
import xapian
import os
import time
import logging


def is_available():
    return xapian.major_version() > 0


# in xapian there is a length restriction for term strings
# see http://osdir.com/ml/search.xapian.general/2006-11/msg00210.html
# a maximum length of around 240 is described there - but we need less anyway
_MAX_TERM_LENGTH = 128


class XapianDatabase(CommonIndexer.CommonDatabase):
    """Interface to the `Xapian indexer <http://xapian.org>`_."""

    QUERY_TYPE = xapian.Query
    INDEX_DIRECTORY_NAME = "xapian"

    def __init__(self, basedir, analyzer=None, create_allowed=True):
        """Initialize or open a Xapian database.

        :raise ValueError: the given location exists, but the database type
                is incompatible (e.g. created by a different indexing engine)
        :raise OSError: the database failed to initialize

        :param basedir: the parent directory of the database
        :type basedir: str
        :param analyzer: Bitwise combination of possible analyzer flags
                         to be used as the default analyzer for this
                         database. Leave it empty to use the system default
                         analyzer (self.ANALYZER_DEFAULT).

                         See self.ANALYZER_TOKENIZE, self.ANALYZER_PARTIAL, ...
        :type analyzer: int
        :param create_allowed: create the database, if necessary; default: True
        :type create_allowed: bool
        """
        # call the __init__ function of our parent
        super(XapianDatabase, self).__init__(basedir, analyzer=analyzer,
                create_allowed=create_allowed)
        self.reader = None
        self.writer = None
        if os.path.exists(self.location):
            # try to open an existing database
            try:
                self.reader = xapian.Database(self.location)
            except xapian.DatabaseOpeningError as err_msg:
                raise ValueError("Indexer: failed to open xapian database "
                                 "(%s) - maybe it is not a xapian database: %s" % (
                                 self.location, str(err_msg)))
        else:
            # create a new database
            if not create_allowed:
                raise OSError("Indexer: skipping database creation")
            try:
                # create the parent directory if it does not exist
                parent_path = os.path.dirname(self.location)
                if not os.path.isdir(parent_path):
                    # recursively create all directories up to parent_path
                    os.makedirs(parent_path)
            except IOError as err_msg:
                raise OSError("Indexer: failed to create the parent "
                              "directory (%s) of the indexing database: %s" % (
                              parent_path, str(err_msg)))
            try:
                self.writer = xapian.WritableDatabase(self.location,
                        xapian.DB_CREATE_OR_OPEN)
                self.flush()
            except xapian.DatabaseOpeningError as err_msg:
                raise OSError("Indexer: failed to open or create a xapian "
                              "database (%s): %s" % (self.location, str(err_msg)))

    def __del__(self):
        self.reader = None
        self._writer_close()

    def flush(self, optimize=False):
        """force to write the current changes to disk immediately

        :param optimize: ignored for xapian
        :type optimize: bool
        """
        # write changes to disk (only if database is read-write)
        if self._writer_is_open():
            self._writer_close()
        self._index_refresh()

    def make_query(self, *args, **kwargs):
        try:
            return super(XapianDatabase, self).make_query(*args, **kwargs)
        except xapian.DatabaseModifiedError:
            self._index_refresh()
            return super(XapianDatabase, self).make_query(*args, **kwargs)

    def _create_query_for_query(self, query):
        """generate a query based on an existing query object

        basically this function should just create a copy of the original

        :param query: the original query object
        :type query: xapian.Query
        :return: the resulting query object
        :rtype: xapian.Query
        """
        # create a copy of the original query
        return xapian.Query(query)

    def _create_query_for_string(self, text, require_all=True,
            analyzer=None):
        """generate a query for a plain term of a string query

        basically this function parses the string and returns the resulting
        query

        :param text: the query string
        :type text: str
        :param require_all: boolean operator
                            (True -> AND (default) / False -> OR)
        :type require_all: bool
        :param analyzer: Define query options (partial matching, exact matching,
                         tokenizing, ...) as bitwise combinations of
                         *CommonIndexer.ANALYZER_???*.

                         This can override previously defined field
                         analyzer settings.

                         If analyzer is None (default), then the configured
                         analyzer for the field is used.
        :type analyzer: int
        :return: resulting query object
        :rtype: xapian.Query
        """
        qp = xapian.QueryParser()
        qp.set_database(self.reader)
        if require_all:
            qp.set_default_op(xapian.Query.OP_AND)
        else:
            qp.set_default_op(xapian.Query.OP_OR)
        if analyzer is None:
            analyzer = self.analyzer
        if analyzer & self.ANALYZER_PARTIAL > 0:
            match_flags = xapian.QueryParser.FLAG_PARTIAL
            return qp.parse_query(text, match_flags)
        elif analyzer == self.ANALYZER_EXACT:
            # exact matching -
            return xapian.Query(text)
        else:
            # everything else (not partial and not exact)
            match_flags = 0
            return qp.parse_query(text, match_flags)

    def _create_query_for_field(self, field, value, analyzer=None):
        """generate a field query

        this functions creates a field->value query

        :param field: the fieldname to be used
        :type field: str
        :param value: the wanted value of the field
        :type value: str
        :param analyzer: Define query options (partial matching, exact
                         matching, tokenizing, ...) as bitwise combinations of
                         *CommonIndexer.ANALYZER_???*.

                         This can override previously defined field
                         analyzer settings.

                         If analyzer is None (default), then the configured
                         analyzer for the field is used.
        :type analyzer: int
        :return: the resulting query object
        :rtype: xapian.Query
        """
        if analyzer is None:
            analyzer = self.analyzer
        if analyzer == self.ANALYZER_EXACT:
            # exact matching -> keep special characters
            return xapian.Query("%s%s" % (field.upper(), value))
        # other queries need a parser object
        qp = xapian.QueryParser()
        qp.set_database(self.reader)
        if (analyzer & self.ANALYZER_PARTIAL > 0):
            # partial matching
            match_flags = xapian.QueryParser.FLAG_PARTIAL
            return qp.parse_query(value, match_flags, field.upper())
        else:
            # everything else (not partial and not exact)
            match_flags = 0
            return qp.parse_query(value, match_flags, field.upper())

    def _create_query_combined(self, queries, require_all=True):
        """generate a combined query

        :param queries: list of the original queries
        :type queries: list of xapian.Query
        :param require_all: boolean operator
                            (True -> AND (default) / False -> OR)
        :type require_all: bool
        :return: the resulting combined query object
        :rtype: xapian.Query
        """
        if require_all:
            query_op = xapian.Query.OP_AND
        else:
            query_op = xapian.Query.OP_OR
        return xapian.Query(query_op, queries)

    def _create_empty_document(self):
        """create an empty document to be filled and added to the index later

        :return: the new document object
        :rtype: xapian.Document
        """
        return xapian.Document()

    def _add_plain_term(self, document, term, tokenize=True):
        """add a term to a document

        :param document: the document to be changed
        :type document: xapian.Document
        :param term: a single term to be added
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        if tokenize:
            term_gen = xapian.TermGenerator()
            term_gen.set_document(document)
            term_gen.index_text(term)
        else:
            document.add_term(_truncate_term_length(term))

    def _add_field_term(self, document, field, term, tokenize=True):
        """add a field term to a document

        :param document: the document to be changed
        :type document: xapian.Document
        :param field: name of the field
        :type field: str
        :param term: term to be associated to the field
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        if tokenize:
            term_gen = xapian.TermGenerator()
            term_gen.set_document(document)
            term_gen.index_text(term, 1, field.upper())
        else:
            document.add_term(_truncate_term_length("%s%s" % (field.upper(), term)))

    def _add_document_to_index(self, document):
        """add a prepared document to the index database

        :param document: the document to be added
        :type document: xapian.Document
        """
        # open the database for writing
        self._writer_open()
        self.writer.add_document(document)

    def begin_transaction(self):
        """Begin a transaction.

        Xapian supports transactions to group multiple database modifications.
        This avoids intermediate flushing and therefore increases performance.
        """
        self._writer_open()
        self.writer.begin_transaction()

    def cancel_transaction(self):
        """cancel an ongoing transaction

        no changes since the last execution of 'begin_transcation' are written
        """
        self.writer.cancel_transaction()
        self._writer_close()

    def commit_transaction(self):
        """Submit the changes of an ongoing transaction.

        All changes since the last execution of 'begin_transaction'
        are written.
        """
        self.writer.commit_transaction()
        self._writer_close()

    def get_query_result(self, query):
        """Return an object containing the results of a query.

        :param query: a pre-compiled xapian query
        :type query: xapian.Query
        :return: an object that allows access to the results
        :rtype: XapianIndexer.CommonEnquire
        """
        enquire = xapian.Enquire(self.reader)
        enquire.set_query(query)
        return XapianEnquire(enquire)

    def delete_document_by_id(self, docid):
        """Delete a specified document.

        :param docid: the document ID to be deleted
        :type docid: int
        """
        # open the database for writing
        self._writer_open()
        try:
            self.writer.delete_document(docid)
            return True
        except xapian.DocNotFoundError:
            return False

    def search(self, query, fieldnames):
        """Return a list of the contents of specified fields for all matches
        of a query.

        :param query: the query to be issued
        :type query: xapian.Query
        :param fieldnames: the name(s) of a field of the document content
        :type fieldnames: string | list of strings
        :return: a list of dicts containing the specified field(s)
        :rtype: list of dicts
        """
        result = []
        if isinstance(fieldnames, basestring):
            fieldnames = [fieldnames]
        try:
            self._walk_matches(query, _extract_fieldvalues,
                               (result, fieldnames))
        except xapian.DatabaseModifiedError:
            self._index_refresh()
            self._walk_matches(query, _extract_fieldvalues,
                               (result, fieldnames))
        return result

    def _delete_stale_lock(self):
        if not self._writer_is_open():
            lockfile = os.path.join(self.location, 'flintlock')
            if (os.path.exists(lockfile) and
                (time.time() - os.path.getmtime(lockfile)) / 60 > 15):
                logging.warning("Stale lock found in %s, removing.",
                                self.location)
                os.remove(lockfile)

    def _writer_open(self):
        """Open write access for the indexing database and acquire an
        exclusive lock.
        """
        if not self._writer_is_open():
            self._delete_stale_lock()
            try:
                self.writer = xapian.WritableDatabase(self.location, xapian.DB_OPEN)
            except xapian.DatabaseOpeningError as err_msg:

                raise ValueError("Indexer: failed to open xapian database "
                                 "(%s) - maybe it is not a xapian database: %s" % (
                                 self.location, str(err_msg)))

    def _writer_close(self):
        """close indexing write access and remove database lock"""
        if self._writer_is_open():
            self.writer.flush()
            self.writer = None

    def _writer_is_open(self):
        """check if the indexing write access is currently open"""
        return hasattr(self, "writer") and not self.writer is None

    def _index_refresh(self):
        """re-read the indexer database"""
        try:
            if self.reader is None:
                self.reader = xapian.Database(self.location)
            else:
                self.reader.reopen()
        except xapian.DatabaseOpeningError as err_msg:
            raise ValueError("Indexer: failed to open xapian database "
                             "(%s) - maybe it is not a xapian database: %s" % (
                             self.location, str(err_msg)))


class XapianEnquire(CommonIndexer.CommonEnquire):
    """interface to the xapian object for storing sets of matches
    """

    def get_matches(self, start, number):
        """Return a specified number of qualified matches of a previous query.

        :param start: index of the first match to return (starting from zero)
        :type start: int
        :param number: the number of matching entries to return
        :type number: int
        :return: a set of matching entries and some statistics
        :rtype: tuple of (returned number, available number, matches)
                "matches" is a dictionary of::

                    ["rank", "percent", "document", "docid"]
        """
        matches = self.enquire.get_mset(start, number)
        result = []
        for match in matches:
            elem = {}
            elem["rank"] = match.rank
            elem["docid"] = match.docid
            elem["percent"] = match.percent
            elem["document"] = match.document
            result.append(elem)
        return (matches.size(), matches.get_matches_estimated(), result)


def _truncate_term_length(term, taken=0):
    """truncate the length of a term string length to the maximum allowed
    for xapian terms

    :param term: the value of the term, that should be truncated
    :type term: str
    :param taken: since a term consists of the name of the term and its
        actual value, this additional parameter can be used to reduce the
        maximum count of possible characters
    :type taken: int
    :return: the truncated string
    :rtype: str
    """
    if len(term) > _MAX_TERM_LENGTH - taken:
        return term[0:_MAX_TERM_LENGTH - taken - 1]
    else:
        return term


def _extract_fieldvalues(match, (result, fieldnames)):
    """Add a dict of field values to a list.

    Usually this function should be used together with :func:`_walk_matches`
    for traversing a list of matches.

    :param match: a single match object
    :type match: xapian.MSet
    :param result: the resulting dict will be added to this list
    :type result: list of dict
    :param fieldnames: the names of the fields to be added to the dict
    :type fieldnames: list of str
    """
    # prepare empty dict
    item_fields = {}
    # fill the dict
    for term in match["document"].termlist():
        for fname in fieldnames:
            if ((fname is None) and re.match("[^A-Z]", term.term)):
                value = term.term
            elif re.match("%s[^A-Z]" % str(fname).upper(), term.term):
                value = term.term[len(fname):]
            else:
                continue
            # we found a matching field/term
            if fname in item_fields:
                item_fields[fname].append(value)
            else:
                item_fields[fname] = [value]
    result.append(item_fields)
