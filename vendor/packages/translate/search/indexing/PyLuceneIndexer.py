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
interface for the PyLucene (v2.x) indexing engine

take a look at PyLuceneIndexer1.py for the PyLucene v1.x interface
"""

import logging
import os
import time

# try to import the PyLucene package (with the two possible names)
# remember the type of the detected package (compiled with jcc (>=v2.3) or
# with gcj (<=v2.2)
try:
    import PyLucene
    _COMPILER = 'gcj'
except ImportError:
    # if this fails, then there is no pylucene installed
    import lucene
    PyLucene = lucene
    PyLucene.initVM(PyLucene.CLASSPATH)
    _COMPILER = 'jcc'

import CommonIndexer


UNNAMED_FIELD_NAME = "FieldWithoutAName"
MAX_FIELD_SIZE = 1048576


def is_available():
    return _get_pylucene_version() == 2


class PyLuceneDatabase(CommonIndexer.CommonDatabase):
    """Manage and use a pylucene indexing database."""

    QUERY_TYPE = PyLucene.Query
    INDEX_DIRECTORY_NAME = "lucene"

    def __init__(self, basedir, analyzer=None, create_allowed=True):
        """Initialize or open an indexing database.

        Any derived class must override __init__.

        :raise ValueError: The given location exists, but the database type
                           is incompatible (e.g. created by a different indexing engine)
        :raise OSError: the database failed to initialize

        :param basedir: The parent directory of the database
        :type basedir: str
        :param analyzer: Bitwise combination of possible analyzer flags
                         to be used as the default analyzer for this database.
                         Leave it empty to use the system default analyzer
                         (self.ANALYZER_DEFAULT). See self.ANALYZER_TOKENIZE,
                         self.ANALYZER_PARTIAL, ...
        :type analyzer: int
        :param create_allowed: create the database, if necessary; default: True
        :type create_allowed: bool
        """
        jvm = PyLucene.getVMEnv()
        jvm.attachCurrentThread()
        super(PyLuceneDatabase, self).__init__(basedir, analyzer=analyzer,
                create_allowed=create_allowed)
        self.pyl_analyzer = PyLucene.StandardAnalyzer()
        self.writer = None
        self.reader = None
        self.index_version = None
        try:
            # try to open an existing database
            tempreader = PyLucene.IndexReader.open(self.location)
            tempreader.close()
        except PyLucene.JavaError as err_msg:
            # Write an error out, in case this is a real problem instead of an absence of an index
            # TODO: turn the following two lines into debug output
            #errorstr = str(e).strip() + "\n" + self.errorhandler.traceback_str()
            #DEBUG_FOO("could not open index, so going to create: " + errorstr)
            # Create the index, so we can open cached readers on it
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
                              parent_path, err_msg))
            try:
                tempwriter = PyLucene.IndexWriter(self.location,
                        self.pyl_analyzer, True)
                tempwriter.close()
            except PyLucene.JavaError as err_msg:
                raise OSError("Indexer: failed to open or create a Lucene"
                              " database (%s): %s" % (self.location, err_msg))
        # the indexer is initialized - now we prepare the searcher
        # windows file locking seems inconsistent, so we try 10 times
        numtries = 0
        #self.dir_lock.acquire(blocking=True)
        # read "self.reader", "self.indexVersion" and "self.searcher"
        try:
            while numtries < 10:
                try:
                    self.reader = PyLucene.IndexReader.open(self.location)
                    self.indexVersion = self.reader.getCurrentVersion(
                        self.location)
                    self.searcher = PyLucene.IndexSearcher(self.reader)
                    break
                except PyLucene.JavaError as e:
                    # store error message for possible later re-raise (below)
                    lock_error_msg = e
                    time.sleep(0.01)
                    numtries += 1
            else:
                # locking failed for 10 times
                raise OSError("Indexer: failed to lock index database"
                              " (%s)" % lock_error_msg)
        finally:
            pass
        #    self.dir_lock.release()
        # initialize the searcher and the reader
        self._index_refresh()

    def __del__(self):
        """remove lock and close writer after loosing the last reference"""
        jvm = PyLucene.getVMEnv()
        jvm.attachCurrentThread()
        self._writer_close()
        if hasattr(self, "reader") and self.reader is not None:
            self.reader.close()
            self.reader = None
        if hasattr(self, "searcher") and self.searcher is not None:
            self.searcher.close()
            self.searcher = None

    def flush(self, optimize=False):
        """flush the content of the database - to force changes to be written
        to disk

        some databases also support index optimization

        :param optimize: should the index be optimized if possible?
        :type optimize: bool
        """
        keep_open = self._writer_is_open()
        self._writer_open()
        try:
            if optimize:
                self.writer.optimize()
        finally:
            self.writer.flush()
        if not keep_open:
            self._writer_close()

    def make_query(self, *args, **kwargs):
        jvm = PyLucene.getVMEnv()
        jvm.attachCurrentThread()
        return super(PyLuceneDatabase, self).make_query(*args, **kwargs)

    def _create_query_for_query(self, query):
        """generate a query based on an existing query object

        basically this function should just create a copy of the original

        :param query: the original query object
        :type query: PyLucene.Query
        :return: resulting query object
        :rtype: PyLucene.Query
        """
        # TODO: a deep copy or a clone would be safer
        # somehow not working (returns "null"): copy.deepcopy(query)
        return query

    def _escape_term_value(self, value):
        """Escapes special :param:`value` characters."""
        # The indexer seems to strip hyphens, but not the analyzer. If we
        # didn't replace it with space, searching for words with hyphen fails
        value = value.replace("-", " ")
        return PyLucene.QueryParser.escape(value)

    def _create_query_for_string(self, text, require_all=True,
            analyzer=None):
        """generate a query for a plain term of a string query

        basically this function parses the string and returns the resulting
        query

        :param text: The query string
        :type text: str
        :param require_all: boolean operator
                            (True -> AND (default) / False -> OR)
        :type require_all: bool
        :param analyzer: The analyzer to be used
                         Possible analyzers are:
                         -  :attr:`CommonDatabase.ANALYZER_TOKENIZE`
                            the field value is splitted to be matched word-wise
                         -  :attr:`CommonDatabase.ANALYZER_PARTIAL`
                            the field value must start with the query string
                         -  :attr:`CommonDatabase.ANALYZER_EXACT`
                            keep special characters and the like
        :type analyzer: bool
        :return: resulting query object
        :rtype: PyLucene.Query
        """
        if analyzer is None:
            analyzer = self.analyzer
        if analyzer == self.ANALYZER_EXACT:
            analyzer_obj = PyLucene.KeywordAnalyzer()
        else:
            text = self._escape_term_value(text)
            analyzer_obj = PyLucene.StandardAnalyzer()
        qp = PyLucene.QueryParser(UNNAMED_FIELD_NAME, analyzer_obj)
        if (analyzer & self.ANALYZER_PARTIAL > 0):
            # PyLucene uses explicit wildcards for partial matching
            text += "*"
        if require_all:
            qp.setDefaultOperator(qp.Operator.AND)
        else:
            qp.setDefaultOperator(qp.Operator.OR)
        return qp.parse(text)

    def _create_query_for_field(self, field, value, analyzer=None):
        """generate a field query

        this functions creates a field->value query

        :param field: The fieldname to be used
        :type field: str
        :param value: The wanted value of the field
        :type value: str
        :param analyzer: The analyzer to be used
                         Possible analyzers are:
                         - :attr:`CommonDatabase.ANALYZER_TOKENIZE`
                           the field value is splitted to be matched word-wise
                         - :attr:`CommonDatabase.ANALYZER_PARTIAL`
                           the field value must start with the query string
                         - :attr:`CommonDatabase.ANALYZER_EXACT`
                           keep special characters and the like
        :type analyzer: bool
        :return: resulting query object
        :rtype: PyLucene.Query
        """
        if analyzer is None:
            analyzer = self.analyzer
        if analyzer == self.ANALYZER_EXACT:
            analyzer_obj = PyLucene.KeywordAnalyzer()
        else:
            value = self._escape_term_value(value)
            analyzer_obj = PyLucene.StandardAnalyzer()
        qp = PyLucene.QueryParser(field, analyzer_obj)
        if (analyzer & self.ANALYZER_PARTIAL > 0):
            # PyLucene uses explicit wildcards for partial matching
            value += "*"
        return qp.parse(value)

    def _create_query_combined(self, queries, require_all=True):
        """generate a combined query

        :param queries: list of the original queries
        :type queries: list of PyLucene.Query
        :param require_all: boolean operator
            (True -> AND (default) / False -> OR)
        :type require_all: bool
        :return: the resulting combined query object
        :rtype: PyLucene.Query
        """
        combined_query = PyLucene.BooleanQuery()
        for query in queries:
            combined_query.add(
                    PyLucene.BooleanClause(query, _occur(require_all, False)))
        return combined_query

    def _create_empty_document(self):
        """create an empty document to be filled and added to the index later

        :return: the new document object
        :rtype: PyLucene.Document
        """
        return PyLucene.Document()

    def _add_plain_term(self, document, term, tokenize=True):
        """add a term to a document

        :param document: the document to be changed
        :type document: PyLucene.Document
        :param term: a single term to be added
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        if tokenize:
            token_flag = PyLucene.Field.Index.TOKENIZED
        else:
            token_flag = PyLucene.Field.Index.UN_TOKENIZED
        document.add(PyLucene.Field(str(UNNAMED_FIELD_NAME), term,
                PyLucene.Field.Store.YES, token_flag))

    def _add_field_term(self, document, field, term, tokenize=True):
        """add a field term to a document

        :param document: the document to be changed
        :type document: PyLucene.Document
        :param field: name of the field
        :type field: str
        :param term: term to be associated to the field
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        if tokenize:
            token_flag = PyLucene.Field.Index.TOKENIZED
        else:
            token_flag = PyLucene.Field.Index.UN_TOKENIZED
        document.add(PyLucene.Field(str(field), term,
                PyLucene.Field.Store.YES, token_flag))

    def _add_document_to_index(self, document):
        """add a prepared document to the index database

        :param document: the document to be added
        :type document: PyLucene.Document
        """
        self._writer_open()
        self.writer.addDocument(document)

    def begin_transaction(self):
        """PyLucene does not support transactions

        Thus this function just opens the database for write access.
        Call "cancel_transaction" or "commit_transaction" to close write
        access in order to remove the exclusive lock from the database
        directory.
        """
        jvm = PyLucene.getVMEnv()
        jvm.attachCurrentThread()
        self._writer_open()

    def cancel_transaction(self):
        """PyLucene does not support transactions

        Thus this function just closes the database write access and removes
        the exclusive lock.

        See 'start_transaction' for details.
        """
        if self._writer_is_open():
            self.writer.abort()
        self._writer_close()

    def commit_transaction(self):
        """PyLucene does not support transactions

        Thus this function just closes the database write access and removes
        the exclusive lock.

        See 'start_transaction' for details.
        """
        self._writer_close()
        self._index_refresh()

    def get_query_result(self, query):
        """return an object containing the results of a query

        :param query: a pre-compiled query
        :type query: a query object of the real implementation
        :return: an object that allows access to the results
        :rtype: subclass of CommonEnquire
        """
        return PyLuceneHits(self.searcher.search(query))

    def delete_doc(self, ident):
        super(PyLuceneDatabase, self).delete_doc(ident)
        self.reader.flush()
        self._index_refresh()

    def delete_document_by_id(self, docid):
        """delete a specified document

        :param docid: the document ID to be deleted
        :type docid: int
        """
        if self._writer_is_open():
            self._writer_close()
        try:
            self.reader.deleteDocument(docid)
        except PyLucene.JavaError:
            self._index_refresh()
            self.reader.deleteDocument(docid)

    def search(self, query, fieldnames):
        """Return a list of the contents of specified fields for all matches of
        a query.

        :param query: the query to be issued
        :type query: a query object of the real implementation
        :param fieldnames: the name(s) of a field of the document content
        :type fieldnames: string | list of strings
        :return: a list of dicts containing the specified field(s)
        :rtype: list of dicts
        """
        if isinstance(fieldnames, basestring):
            fieldnames = [fieldnames]
        hits = self.searcher.search(query)
        if _COMPILER == 'jcc':
            # add the ranking number and the retrieved document to the array
            hits = [(hit, hits.doc(hit)) for hit in range(hits.length())]
        result = []
        for hit, doc in hits:
            fields = {}
            for fieldname in fieldnames:
                # take care for the special field "None"
                if fieldname is None:
                    pyl_fieldname = UNNAMED_FIELD_NAME
                else:
                    pyl_fieldname = fieldname
                fields[fieldname] = doc.getValues(pyl_fieldname)
            result.append(fields)
        return result

    def _delete_stale_lock(self):
        if self.reader.isLocked(self.location):
            #HACKISH: there is a lock but Lucene api can't tell us how old it
            # is, will have to check the filesystem
            try:
                # in try block just in case lock disappears on us while testing it
                stat = os.stat(os.path.join(self.location, 'write.lock'))
                age = (time.time() - stat.st_mtime) / 60
                if age > 15:
                    logging.warning("stale lock found in %s, removing.", self.location)
                    self.reader.unlock(self.reader.directory())
            except:
                pass

    def _writer_open(self):
        """open write access for the indexing database and acquire an
        exclusive lock
        """
        if not self._writer_is_open():
            self._delete_stale_lock()
            self.writer = PyLucene.IndexWriter(self.location, self.pyl_analyzer,
                    False)
            # "setMaxFieldLength" is available since PyLucene v2
            # we must stay compatible to v1 for the derived class
            # (PyLuceneIndexer1) - thus we make this step optional
            if hasattr(self.writer, "setMaxFieldLength"):
                self.writer.setMaxFieldLength(MAX_FIELD_SIZE)
        # do nothing, if it is already open

    def _writer_close(self):
        """close indexing write access and remove the database lock"""
        if self._writer_is_open():
            self.writer.close()
            self.writer = None

    def _writer_is_open(self):
        """check if the indexing write access is currently open"""
        return hasattr(self, "writer") and not self.writer is None

    def _index_refresh(self):
        """re-read the indexer database"""
        try:
            if self.reader is None or self.searcher is None:
                self.reader = PyLucene.IndexReader.open(self.location)
                self.searcher = PyLucene.IndexSearcher(self.reader)
            elif (self.index_version !=
                      self.reader.getCurrentVersion(self.location)):
                self.searcher.close()
                self.reader.close()
                self.reader = PyLucene.IndexReader.open(self.location)
                self.searcher = PyLucene.IndexSearcher(self.reader)
                self.index_version = self.reader.getCurrentVersion(self.location)
        except PyLucene.JavaError as e:
            # TODO: add some debugging output?
            #self.errorhandler.logerror("Error attempting to read index - try reindexing: "+str(e))
            pass


class PyLuceneHits(CommonIndexer.CommonEnquire):
    """an enquire object contains the information about the result of a request
    """

    def get_matches(self, start, number):
        """return a specified number of qualified matches of a previous query

        :param start: index of the first match to return (starting from zero)
        :type start: int
        :param number: the number of matching entries to return
        :type number: int
        :return: a set of matching entries and some statistics
        :rtype: tuple of (returned number, available number, matches)
                "matches" is a dictionary of::

                    ["rank", "percent", "document", "docid"]
        """
        # check if requested results do not exist
        # stop is the lowest index number to be ommitted
        stop = start + number
        if stop > self.enquire.length():
            stop = self.enquire.length()
        # invalid request range
        if stop <= start:
            return (0, self.enquire.length(), [])
        result = []
        for index in range(start, stop):
            item = {}
            item["rank"] = index
            item["docid"] = self.enquire.id(index)
            item["percent"] = self.enquire.score(index)
            item["document"] = self.enquire.doc(index)
            result.append(item)
        return ((stop - start), self.enquire.length(), result)


def _occur(required, prohibited):
    if required and not prohibited:
        return PyLucene.BooleanClause.Occur.MUST
    elif not required and not prohibited:
        return PyLucene.BooleanClause.Occur.SHOULD
    elif not required and prohibited:
        return PyLucene.BooleanClause.Occur.MUST_NOT
    else:
        # It is an error to specify a clause as both required
        # and prohibited
        return None


def _get_pylucene_version():
    """get the installed pylucene version

    :return: 1 -> PyLucene v1.x / 2 -> PyLucene v2.x / 0 -> unknown
    :rtype: int
    """
    version = PyLucene.VERSION
    if version.startswith("1."):
        return 1
    elif version.startswith("2."):
        return 2
    else:
        return 0
