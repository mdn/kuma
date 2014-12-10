#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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
#

"""
Interface to the Xapian indexing engine for the Translate Toolkit

Xapian v1.0 or higher is supported.

If you are interested in writing an interface for Xapian 0.x, then
you should checkout the following::
    svn export -r 7235 https://translate.svn.sourceforge.net/svnroot/translate/src/branches/translate-search-indexer-generic-merging/translate/search/indexer/
It is not completely working, but it should give you a good start.
"""

__revision__ = "$Id: XapianIndexer.py 13411 2009-11-30 20:51:48Z alaaosh $"

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


def is_available():
    return xapian.major_version() > 0


# in xapian there is a length restriction for term strings
# see http://osdir.com/ml/search.xapian.general/2006-11/msg00210.html
# a maximum length of around 240 is described there - but we need less anyway
_MAX_TERM_LENGTH = 128


class XapianDatabase(CommonIndexer.CommonDatabase):
    """interface to the xapian (http://xapian.org) indexer
    """

    QUERY_TYPE = xapian.Query
    INDEX_DIRECTORY_NAME = "xapian"

    def __init__(self, basedir, analyzer=None, create_allowed=True):
        """initialize or open a xapian database

        @raise ValueError: the given location exists, but the database type
                is incompatible (e.g. created by a different indexing engine)
        @raise OSError: the database failed to initialize

        @param basedir: the parent directory of the database
        @type basedir: str
        @param analyzer: bitwise combination of possible analyzer flags
            to be used as the default analyzer for this database. Leave it empty
            to use the system default analyzer (self.ANALYZER_DEFAULT).
            see self.ANALYZER_TOKENIZE, self.ANALYZER_PARTIAL, ...
        @type analyzer: int
        @param create_allowed: create the database, if necessary; default: True
        @type create_allowed: bool
        """
        # call the __init__ function of our parent
        super(XapianDatabase, self).__init__(basedir, analyzer=analyzer,
                create_allowed=create_allowed)
        if os.path.exists(self.location):
            # try to open an existing database
            try:
                self.database = xapian.WritableDatabase(self.location,
                    xapian.DB_OPEN)
            except xapian.DatabaseOpeningError, err_msg:
                raise ValueError("Indexer: failed to open xapian database " \
                        + "(%s) - maybe it is not a xapian database: %s" \
                        % (self.location, err_msg))
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
            except IOError, err_msg:
                raise OSError("Indexer: failed to create the parent " \
                        + "directory (%s) of the indexing database: %s" \
                        % (parent_path, err_msg))
            try:
                self.database = xapian.WritableDatabase(self.location,
                        xapian.DB_CREATE_OR_OPEN)
            except xapian.DatabaseOpeningError, err_msg:
                raise OSError("Indexer: failed to open or create a xapian " \
                        + "database (%s): %s" % (self.location, err_msg))

    def flush(self, optimize=False):
        """force to write the current changes to disk immediately

        @param optimize: ignored for xapian
        @type optimize: bool
        """
        # write changes to disk (only if database is read-write)
        if (isinstance(self.database, xapian.WritableDatabase)):
            self.database.flush()
        # free the database to remove locks - this is a xapian-specific issue
        self.database = None
        # reopen it as read-only
        self._prepare_database()

    def _create_query_for_query(self, query):
        """generate a query based on an existing query object

        basically this function should just create a copy of the original

        @param query: the original query object
        @type query: xapian.Query
        @return: the resulting query object
        @rtype: xapian.Query
        """
        # create a copy of the original query
        return xapian.Query(query)

    def _create_query_for_string(self, text, require_all=True,
            analyzer=None):
        """generate a query for a plain term of a string query

        basically this function parses the string and returns the resulting
        query

        @param text: the query string
        @type text: str
        @param require_all: boolean operator
            (True -> AND (default) / False -> OR)
        @type require_all: bool
        @param analyzer: Define query options (partial matching, exact matching,
            tokenizing, ...) as bitwise combinations of
            CommonIndexer.ANALYZER_???.
            This can override previously defined field analyzer settings.
            If analyzer is None (default), then the configured analyzer for the
            field is used.
        @type analyzer: int
        @return: resulting query object
        @rtype: xapian.Query
        """
        qp = xapian.QueryParser()
        qp.set_database(self.database)
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

        @param field: the fieldname to be used
        @type field: str
        @param value: the wanted value of the field
        @type value: str
        @param analyzer: Define query options (partial matching, exact matching,
            tokenizing, ...) as bitwise combinations of
            CommonIndexer.ANALYZER_???.
            This can override previously defined field analyzer settings.
            If analyzer is None (default), then the configured analyzer for the
            field is used.
        @type analyzer: int
        @return: the resulting query object
        @rtype: xapian.Query
        """
        if analyzer is None:
            analyzer = self.analyzer
        if analyzer == self.ANALYZER_EXACT:
            # exact matching -> keep special characters
            return xapian.Query("%s%s" % (field.upper(), value))
        # other queries need a parser object
        qp = xapian.QueryParser()
        qp.set_database(self.database)
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

        @param queries: list of the original queries
        @type queries: list of xapian.Query
        @param require_all: boolean operator
            (True -> AND (default) / False -> OR)
        @type require_all: bool
        @return: the resulting combined query object
        @rtype: xapian.Query
        """
        if require_all:
            query_op = xapian.Query.OP_AND
        else:
            query_op = xapian.Query.OP_OR
        return xapian.Query(query_op, queries)

    def _create_empty_document(self):
        """create an empty document to be filled and added to the index later

        @return: the new document object
        @rtype: xapian.Document
        """
        return xapian.Document()

    def _add_plain_term(self, document, term, tokenize=True):
        """add a term to a document

        @param document: the document to be changed
        @type document: xapian.Document
        @param term: a single term to be added
        @type term: str
        @param tokenize: should the term be tokenized automatically
        @type tokenize: bool
        """
        if tokenize:
            term_gen = xapian.TermGenerator()
            term_gen.set_document(document)
            term_gen.index_text(term)
        else:
            document.add_term(_truncate_term_length(term))

    def _add_field_term(self, document, field, term, tokenize=True):
        """add a field term to a document

        @param document: the document to be changed
        @type document: xapian.Document
        @param field: name of the field
        @type field: str
        @param term: term to be associated to the field
        @type term: str
        @param tokenize: should the term be tokenized automatically
        @type tokenize: bool
        """
        if tokenize:
            term_gen = xapian.TermGenerator()
            term_gen.set_document(document)
            term_gen.index_text(term, 1, field.upper())
        else:
            document.add_term(_truncate_term_length("%s%s" % \
                        (field.upper(), term)))

    def _add_document_to_index(self, document):
        """add a prepared document to the index database

        @param document: the document to be added
        @type document: xapian.Document
        """
        # open the database for writing
        self._prepare_database(writable=True)
        self.database.add_document(document)

    def begin_transaction(self):
        """begin a transaction

        Xapian supports transactions to group multiple database modifications.
        This avoids intermediate flushing and therefore increases performance.
        """
        self._prepare_database(writable=True)
        self.database.begin_transaction()

    def cancel_transaction(self):
        """cancel an ongoing transaction

        no changes since the last execution of 'begin_transcation' are written
        """
        self._prepare_database(writable=True)
        self.database.cancel_transaction()

    def commit_transaction(self):
        """submit the changes of an ongoing transaction

        all changes since the last execution of 'begin_transaction' are written
        """
        self._prepare_database(writable=True)
        self.database.commit_transaction()

    def get_query_result(self, query):
        """return an object containing the results of a query

        @param query: a pre-compiled xapian query
        @type query: xapian.Query
        @return: an object that allows access to the results
        @rtype: XapianIndexer.CommonEnquire
        """
        enquire = xapian.Enquire(self.database)
        enquire.set_query(query)
        return XapianEnquire(enquire)

    def delete_document_by_id(self, docid):
        """delete a specified document

        @param docid: the document ID to be deleted
        @type docid: int
        """
        # open the database for writing
        self._prepare_database(writable=True)
        try:
            self.database.delete_document(docid)
            return True
        except xapian.DocNotFoundError:
            return False

    def search(self, query, fieldnames):
        """return a list of the contents of specified fields for all matches of
        a query

        @param query: the query to be issued
        @type query: xapian.Query
        @param fieldnames: the name(s) of a field of the document content
        @type fieldnames: string | list of strings
        @return: a list of dicts containing the specified field(s)
        @rtype: list of dicts
        """
        result = []
        if isinstance(fieldnames, basestring):
            fieldnames = [fieldnames]
        self._walk_matches(query, _extract_fieldvalues, (result, fieldnames))
        return result

    def _prepare_database(self, writable=False):
        """reopen the database as read-only or as writable if necessary

        this fixes a xapian specific issue regarding open locks for
        writable databases

        @param writable: True for opening a writable database
        @type writable: bool
        """
        if writable and (not isinstance(self.database,
                xapian.WritableDatabase)):
            self.database = xapian.WritableDatabase(self.location,
                    xapian.DB_OPEN)
        elif not writable and (not isinstance(self.database, xapian.Database)):
            self.database = xapian.Database(self.location)


class XapianEnquire(CommonIndexer.CommonEnquire):
    """interface to the xapian object for storing sets of matches
    """

    def get_matches(self, start, number):
        """return a specified number of qualified matches of a previous query

        @param start: index of the first match to return (starting from zero)
        @type start: int
        @param number: the number of matching entries to return
        @type number: int
        @return: a set of matching entries and some statistics
        @rtype: tuple of (returned number, available number, matches)
                "matches" is a dictionary of::
                    ["rank", "percent", "document", "docid"]
        """
        matches = self.enquire.get_mset(start, number)
        result = []
        for match in matches:
            elem = {}
            elem["rank"] = match[xapian.MSET_RANK]
            elem["docid"] = match[xapian.MSET_DID]
            elem["percent"] = match[xapian.MSET_PERCENT]
            elem["document"] = match[xapian.MSET_DOCUMENT]
            result.append(elem)
        return (matches.size(), matches.get_matches_estimated(), result)


def _truncate_term_length(term, taken=0):
    """truncate the length of a term string length to the maximum allowed
    for xapian terms

    @param term: the value of the term, that should be truncated
    @type term: str
    @param taken: since a term consists of the name of the term and its
        actual value, this additional parameter can be used to reduce the
        maximum count of possible characters
    @type taken: int
    @return: the truncated string
    @rtype: str
    """
    if len(term) > _MAX_TERM_LENGTH - taken:
        return term[0:_MAX_TERM_LENGTH - taken - 1]
    else:
        return term

def _extract_fieldvalues(match, (result, fieldnames)):
    """add a dict of field values to a list

    usually this function should be used together with '_walk_matches'
    for traversing a list of matches
    @param match: a single match object
    @type match: xapian.MSet
    @param result: the resulting dict will be added to this list
    @type result: list of dict
    @param fieldnames: the names of the fields to be added to the dict
    @type fieldnames: list of str
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
            if item_fields.has_key(fname):
                item_fields[fname].append(value)
            else:
                item_fields[fname] = [value]
    result.append(item_fields)
