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
interface for the pylucene (v1.x) indexing engine

take a look at PyLuceneIndexer.py for PyLucene v2.x support
"""

# this module is based on PyLuceneIndexer (for PyLucene v2.x)
import PyLuceneIndexer
import PyLucene


def is_available():
    return PyLuceneIndexer._get_pylucene_version() == 1


class PyLuceneDatabase(PyLuceneIndexer.PyLuceneDatabase):
    """manage and use a pylucene indexing database"""

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
            # exact matching - no substitution ...
            # for PyLucene: nothing special is necessary
            pass
        # don't care about special characters ...
        if analyzer == self.ANALYZER_EXACT:
            analyzer_obj = self.ExactAnalyzer()
        else:
            text = _escape_term_value(text)
            analyzer_obj = PyLucene.StandardAnalyzer()
        qp = PyLucene.QueryParser(analyzer=analyzer_obj)
        if require_all:
            qp.setDefaultOperator(qp.Operator.AND)
        else:
            qp.setDefaultOperator(qp.Operator.OR)
        if (analyzer & self.ANALYZER_PARTIAL) > 0:
            # PyLucene uses explicit wildcards for partial matching
            text += "*"
        return qp.parse(text)

    def _create_query_for_field(self, field, value, analyzer=None):
        """Generate a field query.

        This functions creates a field->value query.

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
        :return: Resulting query object
        :rtype: PyLucene.Query
        """
        if analyzer is None:
            analyzer = self.analyzer
        if analyzer == self.ANALYZER_EXACT:
            analyzer_obj = self.ExactAnalyzer()
        else:
            value = _escape_term_value(value)
            analyzer_obj = PyLucene.StandardAnalyzer()
        if (analyzer & self.ANALYZER_PARTIAL) > 0:
            # PyLucene uses explicit wildcards for partial matching
            value += "*"
        return PyLucene.QueryParser.parse(value, field, analyzer_obj)

    def _create_query_combined(self, queries, require_all=True):
        """generate a combined query

        :param queries: list of the original queries
        :type queries: list of xapian.Query
        :param require_all: boolean operator
            (True -> AND (default) / False -> OR)
        :type require_all: bool
        :return: the resulting combined query object
        :rtype: PyLucene.Query
        """
        combined_query = PyLucene.BooleanQuery()
        for query in queries:
            combined_query.add(
                    PyLucene.BooleanClause(query, require_all, False))
        return combined_query

    def _add_plain_term(self, document, term, tokenize=True):
        """add a term to a document

        :param document: the document to be changed
        :type document: xapian.Document | PyLucene.Document
        :param term: a single term to be added
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        # Field parameters: name, string, store, index, token
        document.add(PyLucene.Field(str(PyLuceneIndex.UNNAMED_FIELD_NAME), term,
                True, True, tokenize))

    def _add_field_term(self, document, field, term, tokenize=True):
        """add a field term to a document

        :param document: the document to be changed
        :type document: xapian.Document | PyLucene.Document
        :param field: name of the field
        :type field: str
        :param term: term to be associated to the field
        :type term: str
        :param tokenize: should the term be tokenized automatically
        :type tokenize: bool
        """
        # TODO: decoding (utf-8) is missing
        # Field parameters: name, string, store, index, token
        document.add(PyLucene.Field(str(field), term,
                True, True, tokenize))

    def get_query_result(self, query):
        """return an object containing the results of a query

        :param query: a pre-compiled query
        :type query: a query object of the real implementation
        :return: an object that allows access to the results
        :rtype: subclass of CommonEnquire
        """
        return PyLucene.indexSearcher.search(query)

    def search(self, query, fieldnames):
        """return a list of the contents of specified fields for all matches of
        a query

        :param query: the query to be issued
        :type query: a query object of the real implementation
        :param fieldnames: the name(s) of a field of the document content
        :type fieldnames: string | list of strings
        :return: a list of dicts containing the specified field(s)
        :rtype: list of dicts
        """
        if isinstance(fieldnames, basestring):
            fieldnames = [fieldnames]
        hits = PyLucene.indexSearcher.search(query)
        result = []
        for hit, doc in hits:
            fields = {}
            for fieldname in fieldnames:
                content = doc.get(fieldname)
                if not content is None:
                    fields[fieldname] = content
            result.append(fields)
        return result

    def _writer_open(self):
        """open write access for the indexing database and acquire an
        exclusive lock
        """
        super(PyLuceneIndexer1, self)._writer_open_()
        self.writer.maxFieldLength = PyLuceneIndexer.MAX_FIELD_SIZE
