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


"""
base class for interfaces to indexing engines for pootle
"""

import os

import translate.lang.data


def is_available():
    """Check if this indexing engine interface is usable.

    This function must exist in every module that contains indexing engine
    interfaces.

    :return: is this interface usable?
    :rtype: bool
    """
    return False


class CommonDatabase(object):
    """Base class for indexing support.

    Any real implementation must override most methods of this class.
    """

    field_analyzers = {}
    """mapping of field names and analyzers - see
    :meth:`~.CommonDatabase.set_field_analyzers`"""

    ANALYZER_EXACT = 0
    """exact matching: the query string must equal the whole term string"""

    ANALYZER_PARTIAL = 1 << 1
    """partial matching: a document matches, even if the query string only
    matches the beginning of the term value."""

    ANALYZER_TOKENIZE = 1 << 2
    """tokenize terms and queries automatically"""

    ANALYZER_DEFAULT = ANALYZER_TOKENIZE | ANALYZER_PARTIAL
    """the default analyzer to be used if nothing is configured"""

    QUERY_TYPE = None
    """override this with the query class of the implementation"""

    INDEX_DIRECTORY_NAME = None
    """override this with a string to be used as the name of the indexing
    directory/file in the filesystem
    """

    def __init__(self, basedir, analyzer=None, create_allowed=True):
        """initialize or open an indexing database

        Any derived class must override ``__init__``.

        Any implementation can rely on the "self.location" attribute to be set
        by the ``__init__`` function of the super class.

        :raise ValueError: the given location exists, but the database type
                           is incompatible (e.g. created by a different
                           indexing engine)
        :raise OSError: the database failed to initialize

        :param basedir: the parent directory of the database
        :type basedir: str
        :param analyzer: bitwise combination of possible analyzer flags
                         to be used as the default analyzer for this
                         database. Leave it empty to use the system
                         default analyzer (``self.ANALYZER_DEFAULT``).
                         see :attr:`CommonDatabase.ANALYZER_TOKENIZE`,
                         :attr:`CommonDatabase.ANALYZER_PARTIAL`, ...
        :type analyzer: int
        :param create_allowed: create the database, if necessary.
        :type create_allowed: bool
        """
        # just do some checks
        if self.QUERY_TYPE is None:
            raise NotImplementedError("Incomplete indexer implementation: "
                                      "'QUERY_TYPE' is undefined")
        if self.INDEX_DIRECTORY_NAME is None:
            raise NotImplementedError("Incomplete indexer implementation: "
                                      "'INDEX_DIRECTORY_NAME' is undefined")
        self.location = os.path.join(basedir, self.INDEX_DIRECTORY_NAME)
        if (not create_allowed) and (not os.path.exists(self.location)):
            raise OSError("Indexer: the database does not exist - and I am"
                          " not configured to create it.")
        if analyzer is None:
            self.analyzer = self.ANALYZER_DEFAULT
        else:
            self.analyzer = analyzer
        self.field_analyzers = {}

    def flush(self, optimize=False):
        """Flush the content of the database - to force changes to be written
        to disk.

        Some databases also support index optimization.

        :param optimize: should the index be optimized if possible?
        :type optimize: bool
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'flush' is missing")

    def make_query(self, args, require_all=True, analyzer=None):
        """Create simple queries (strings or field searches) or
        combine multiple queries (AND/OR).

        To specifiy rules for field searches, you may want to take a look at
        :meth:`~.CommonDatabase.set_field_analyzers`. The parameter
        'match_text_partial' can override the previously defined
        default setting.

        :param args: queries or search string or description of field query
                     examples::

                        [xapian.Query("foo"), xapian.Query("bar")]
                        xapian.Query("foo")
                        "bar"
                        {"foo": "bar", "foobar": "foo"}

        :type args: list of queries | single query | str | dict
        :param require_all: boolean operator
                            (True -> AND (default) / False -> OR)
        :type require_all: boolean
        :param analyzer: (only applicable for 'dict' or 'str')
                         Define query options (partial matching, exact
                         matching, tokenizing, ...) as bitwise
                         combinations of *CommonIndexer.ANALYZER_???*.

                         This can override previously defined field
                         analyzer settings.

                         If analyzer is ``None`` (default), then the
                         configured analyzer for the field is used.
        :type analyzer: int
        :return: the combined query
        :rtype: query type of the specific implementation
        """
        # turn a dict into a list if necessary
        if isinstance(args, dict):
            args = args.items()
        # turn 'args' into a list if necessary
        if not isinstance(args, list):
            args = [args]
        # combine all given queries
        result = []
        for query in args:
            # just add precompiled queries
            if isinstance(query, self.QUERY_TYPE):
                result.append(self._create_query_for_query(query))
            # create field/value queries out of a tuple
            elif isinstance(query, tuple):
                field, value = query
                # perform unicode normalization
                field = translate.lang.data.normalize(unicode(field))
                value = translate.lang.data.normalize(unicode(value))
                # check for the choosen match type
                if analyzer is None:
                    analyzer = self.get_field_analyzers(field)
                result.append(self._create_query_for_field(field, value,
                        analyzer=analyzer))
            # parse plaintext queries
            elif isinstance(query, basestring):
                if analyzer is None:
                    analyzer = self.analyzer
                # perform unicode normalization
                query = translate.lang.data.normalize(unicode(query))
                result.append(self._create_query_for_string(query,
                        require_all=require_all, analyzer=analyzer))
            else:
                # other types of queries are not supported
                raise ValueError("Unable to handle query type: %s" %
                                 str(type(query)))
        # return the combined query
        return self._create_query_combined(result, require_all)

    def _create_query_for_query(self, query):
        """Generate a query based on an existing query object.

        Basically this function should just create a copy of the original.

        :param query: the original query object
        :type query: ``xapian.Query``
        :return: the resulting query object
        :rtype: ``xapian.Query`` | ``PyLucene.Query``
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_create_query_for_query' is missing")

    def _create_query_for_string(self, text, require_all=True,
            analyzer=None):
        """Generate a query for a plain term of a string query.

        Basically this function parses the string and returns the resulting
        query.

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
        :rtype: xapian.Query | PyLucene.Query
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_create_query_for_string' is missing")

    def _create_query_for_field(self, field, value, analyzer=None):
        """Generate a field query.

        This functions creates a field->value query.

        :param field: the fieldname to be used
        :type field: str
        :param value: the wanted value of the field
        :type value: str
        :param analyzer: Define query options (partial matching, exact matching,
                         tokenizing, ...) as bitwise combinations of
                         *CommonIndexer.ANALYZER_???*.
                         This can override previously defined field
                         analyzer settings.
                         If analyzer is None (default), then the configured
                         analyzer for the field is used.
        :type analyzer: int
        :return: resulting query object
        :rtype: ``xapian.Query`` | ``PyLucene.Query``
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_create_query_for_field' is missing")

    def _create_query_combined(self, queries, require_all=True):
        """generate a combined query

        :param queries: list of the original queries
        :type queries: list of xapian.Query
        :param require_all: boolean operator
                            (True -> AND (default) / False -> OR)
        :type require_all: bool
        :return: the resulting combined query object
        :rtype: ``xapian.Query`` | ``PyLucene.Query``
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_create_query_combined' is missing")

    def index_document(self, data):
        """Add the given data to the database.

        :param data: the data to be indexed.
                     A dictionary will be treated as ``fieldname:value``
                     combinations.
                     If the fieldname is None then the value will be
                     interpreted as a plain term or as a list of plain terms.
                     Lists of terms are indexed separately.
                     Lists of strings are treated as plain terms.
        :type data: dict | list of str
        """
        doc = self._create_empty_document()
        if isinstance(data, dict):
            data = data.items()
        # add all data
        for dataset in data:
            if isinstance(dataset, tuple):
                # the dataset tuple consists of '(key, value)'
                key, value = dataset
                if key is None:
                    if isinstance(value, list):
                        terms = value[:]
                    elif isinstance(value, basestring):
                        terms = [value]
                    else:
                        raise ValueError("Invalid data type to be indexed: %s" %
                                         str(type(data)))
                    for one_term in terms:
                        self._add_plain_term(doc, self._decode(one_term),
                                (self.ANALYZER_DEFAULT & self.ANALYZER_TOKENIZE > 0))
                else:
                    analyze_settings = self.get_field_analyzers(key)
                    # handle multiple terms
                    if not isinstance(value, list):
                        value = [value]
                    for one_term in value:
                        self._add_field_term(doc, key, self._decode(one_term),
                                (analyze_settings & self.ANALYZER_TOKENIZE > 0))
            elif isinstance(dataset, basestring):
                self._add_plain_term(doc, self._decode(dataset),
                        (self.ANALYZER_DEFAULT & self.ANALYZER_TOKENIZE > 0))
            else:
                raise ValueError("Invalid data type to be indexed: %s" %
                                 str(type(data)))
        self._add_document_to_index(doc)

    def _create_empty_document(self):
        """Create an empty document to be filled and added to the index later.

        :return: the new document object
        :rtype: ``xapian.Document`` | ``PyLucene.Document``
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_create_empty_document' is missing")

    def _add_plain_term(self, document, term, tokenize=True):
        """Add a term to a document.

        :param document: the document to be changed
        :type document: ``xapian.Document`` | ``PyLucene.Document``
        :param term: a single term to be added
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_add_plain_term' is missing")

    def _add_field_term(self, document, field, term, tokenize=True):
        """Add a field term to a document.

        :param document: the document to be changed
        :type document: ``xapian.Document`` | ``PyLucene.Document``
        :param field: name of the field
        :type field: str
        :param term: term to be associated to the field
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_add_field_term' is missing")

    def _add_document_to_index(self, document):
        """Add a prepared document to the index database.

        :param document: the document to be added
        :type document: xapian.Document | PyLucene.Document
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'_add_document_to_index' is missing")

    def begin_transaction(self):
        """begin a transaction

        You can group multiple modifications of a database as a transaction.
        This prevents time-consuming database flushing and helps, if you want
        that a changeset is committed either completely or not at all.
        No changes will be written to disk until 'commit_transaction'.
        'cancel_transaction' can be used to revert an ongoing transaction.

        Database types that do not support transactions may silently ignore it.
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'begin_transaction' is missing")

    def cancel_transaction(self):
        """cancel an ongoing transaction

        See 'start_transaction' for details.
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'cancel_transaction' is missing")

    def commit_transaction(self):
        """Submit the currently ongoing transaction and write changes to disk.

        See 'start_transaction' for details.
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'commit_transaction' is missing")

    def get_query_result(self, query):
        """return an object containing the results of a query

        :param query: a pre-compiled query
        :type query: a query object of the real implementation
        :return: an object that allows access to the results
        :rtype: subclass of CommonEnquire
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'get_query_result' is missing")

    def delete_document_by_id(self, docid):
        """Delete a specified document.

        :param docid: the document ID to be deleted
        :type docid: int
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'delete_document_by_id' is missing")

    def search(self, query, fieldnames):
        """Return a list of the contents of specified fields for all
        matches of a query.

        :param query: the query to be issued
        :type query: a query object of the real implementation
        :param fieldnames: the name(s) of a field of the document content
        :type fieldnames: string | list of strings
        :return: a list of dicts containing the specified field(s)
        :rtype: list of dicts
        """
        raise NotImplementedError("Incomplete indexer implementation: "
                                  "'search' is missing")

    def delete_doc(self, ident):
        """Delete the documents returned by a query.

        :param ident: [list of] document IDs | dict describing a query | query
        :type ident: int | list of tuples | dict | list of dicts |
                     query (e.g. xapian.Query) | list of queries
        """
        # turn a doc-ID into a list of doc-IDs
        if isinstance(ident, list):
            # it is already a list
            ident_list = ident
        else:
            ident_list = [ident]
        if len(ident_list) == 0:
            # no matching items
            return 0
        if isinstance(ident_list[0], int) or isinstance(ident_list[0], long):
            # create a list of IDs of all successfully removed documents
            success_delete = [match for match in ident_list
                    if self.delete_document_by_id(match)]
            return len(success_delete)
        if isinstance(ident_list[0], dict):
            # something like: { "msgid": "foobar" }
            # assemble all queries
            query = self.make_query([self.make_query(query_dict,
                    require_all=True) for query_dict in ident_list],
                    require_all=True)
        elif isinstance(ident_list[0], object):
            # assume a query object (with 'AND')
            query = self.make_query(ident_list, require_all=True)
        else:
            # invalid element type in list (not necessarily caught in the
            # lines above)
            raise TypeError("description of documents to-be-deleted is not "
                            "supported: list of %s" % type(ident_list[0]))
        # we successfully created a query - now iterate through the result
        # no documents deleted so far ...
        remove_list = []
        # delete all resulting documents step by step

        def add_docid_to_list(match):
            """Collect every document ID."""
            remove_list.append(match["docid"])
        self._walk_matches(query, add_docid_to_list)
        return self.delete_doc(remove_list)

    def _walk_matches(self, query, function, arg_for_function=None):
        """Use this function if you want to do something with every single match
        of a query.

        Example::

            self._walk_matches(query, function_for_match, arg_for_func)

        *function_for_match* expects only one argument: the matched object

        :param query: a query object of the real implementation
        :type query: xapian.Query | PyLucene.Query
        :param function: the function to execute with every match
        :type function: function
        :param arg_for_function: an optional argument for the function
        :type arg_for_function: anything
        """
        # execute the query
        enquire = self.get_query_result(query)
        # start with the first element
        start = 0
        # do the loop at least once
        size, avail = (0, 1)
        # how many results per 'get_matches'?
        steps = 2
        while start < avail:
            (size, avail, matches) = enquire.get_matches(start, steps)
            for match in matches:
                if arg_for_function is None:
                    function(match)
                else:
                    function(match, arg_for_function)
            start += size

    def set_field_analyzers(self, field_analyzers):
        """Set the analyzers for different fields of the database documents.

        All bitwise combinations of *CommonIndexer.ANALYZER_???* are possible.

        :param field_analyzers: mapping of field names and analyzers
        :type field_analyzers: dict containing field names and analyzers
        :raise TypeError: invalid values in *field_analyzers*
        """
        for field, analyzer in field_analyzers.items():
            # check for invald input types
            if not isinstance(field, (str, unicode)):
                raise TypeError("field name must be a string")
            if not isinstance(analyzer, int):
                raise TypeError("the analyzer must be a whole number (int)")
            # map the analyzer to the field name
            self.field_analyzers[field] = analyzer

    def get_field_analyzers(self, fieldnames=None):
        """Return the analyzer that was mapped to a specific field.

        See :meth:`~.CommonDatabase.set_field_analyzers` for details.

        :param fieldnames: the analyzer of this field (or all/multiple fields)
                           is requested; leave empty (or *None*) to
                           request all fields.
        :type fieldnames: str | list of str | None
        :return: The analyzer setting of the field - see
                 *CommonDatabase.ANALYZER_???* or a dict of field names
                 and analyzers
        :rtype: int | dict
        """
        # all field analyzers are requested
        if fieldnames is None:
            # return a copy
            return dict(self.field_analyzers)
        # one field is requested
        if isinstance(fieldnames, (str, unicode)):
            if fieldnames in self.field_analyzers:
                return self.field_analyzers[fieldnames]
            else:
                return self.analyzer
        # a list of fields is requested
        if isinstance(fieldnames, list):
            result = {}
            for field in fieldnames:
                result[field] = self.get_field_analyzers(field)
            return result
        return self.analyzer

    def _decode(self, text):
        """Decode the string from utf-8 or charmap perform
        unicode normalization."""
        if isinstance(text, str):
            try:
                result = unicode(text.decode("UTF-8"))
            except UnicodeEncodeError as e:
                result = unicode(text.decode("charmap"))
        elif not isinstance(text, unicode):
            result = unicode(text)
        else:
            result = text
        # perform unicode normalization
        return translate.lang.data.normalize(result)


class CommonEnquire(object):
    """An enquire object contains the information about the result of a request.
    """

    def __init__(self, enquire):
        """Intialization of a wrapper around enquires of different backends

        :param enquire: a previous enquire
        :type enquire: xapian.Enquire | pylucene-enquire
        """
        self.enquire = enquire

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
        raise NotImplementedError("Incomplete indexing implementation: "
                                  "'get_matches' for the 'Enquire' class is missing")

    def get_matches_count(self):
        """Return the estimated number of matches.

        Use :meth:`translate.search.indexing.CommonIndexer.search`
        to retrieve the exact number of matches

        :return: The estimated number of matches
        :rtype: int
        """
        (returned, estimate_count, matches) = self.get_matches(0, 1)
        return estimate_count
