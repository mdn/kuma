#!/usr/bin/env python
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
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#


import __init__ as indexing
import CommonIndexer
import os
import sys
import shutil

DATABASE = "tmp-index"

# overwrite this value to change the preferred indexing engine
default_engine = "" 

# order of tests to be done
ORDER_OF_TESTS = [ "XapianIndexer", "PyLuceneIndexer", "PyLuceneIndexer1" ]


def _get_indexer(location):
    """wrapper around "indexer.get_indexer" to enable a globally preferred
    indexing engine selection

    create an indexer based on the preference order 'default_engine'

    @param location: the path of the database to be created/opened
    @type location: str
    @return: the resulting indexing engine instance
    @rtype: CommonIndexer.CommonDatabase
    """
    return indexing.get_indexer(location, [default_engine])

def clean_database():
    """remove an existing database"""
    dbase_dir = os.path.abspath(DATABASE)
    # the database directory does not exist
    if not os.path.exists(dbase_dir):
        return
    # recursively remove the directory
    shutil.rmtree(dbase_dir)

def create_example_content(database):
    """add some defined documents to the database

    this may be used to check some specific queries

    @param database: a indexing database object
    @type database: CommonIndexer.CommonDatabase
    """
    # a reasonable foo-bar entry
    database.index_document(["foo", "bar", "med"])
    # and something more for another document with a unicode string
    database.index_document(["foo", "bar", u"HELO"])
    # another similar one - but with "barr" instead of "bar"
    database.index_document(["foo", "barr", "med", "HELO"])
    # some field indexed document data
    database.index_document({"fname1": "foo_field1", "fname2": "foo_field2"})
    database.index_document({"fname1": "bar_field1", "fname2": "foo_field2",
            None: ["HELO", "foo"]})
    database.index_document({ None: "med" })
    # for tokenizing tests
    database.set_field_analyzers({
            "fname1": database.ANALYZER_PARTIAL | database.ANALYZER_TOKENIZE,
            "fname2": database.ANALYZER_EXACT})
    database.index_document({"fname1": "qaz wsx", None: "edc rfv"})
    database.index_document({"fname2": "qaz wsx", None: "edc rfv"})
    # check a filename with the exact analyzer
    database.index_document({"fname2": "foo-bar.po"})
    # add a list of terms for a keyword
    database.index_document({"multiple": ["foo", "bar"]})
    assert _get_number_of_docs(database) == 10

def test_create_database():
    """create a new database from scratch"""
    # clean up everything first
    clean_database()
    new_db = _get_indexer(DATABASE)
    assert isinstance(new_db, CommonIndexer.CommonDatabase)
    assert os.path.exists(DATABASE)
    # clean up
    clean_database()

def test_open_database():
    """open an existing database"""
    # clean up everything first
    clean_database()
    # create a new database - it will be closed immediately afterwards
    # since the reference is lost again
    _get_indexer(DATABASE)
    # open the existing database again
    opened_db = _get_indexer(DATABASE)
    assert isinstance(opened_db, CommonIndexer.CommonDatabase)
    # clean up
    clean_database()

def test_make_queries():
    """create a simple query from a plain string"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # plaintext queries
    q_plain1 = new_db.make_query("foo")
    q_plain2 = new_db.make_query("foo bar")
    assert str(q_plain1) != str(q_plain2)
    # list 'and/or'
    q_combined_and = new_db.make_query([new_db.make_query("foo"),
        new_db.make_query("bar")])
    q_combined_or = new_db.make_query([new_db.make_query("foo"),
        new_db.make_query("bar")], require_all=False)
    assert str(q_combined_or) != str(q_combined_and)

def test_partial_text_matching():
    """check if implicit and explicit partial text matching works"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # this query should return three matches (disabled partial matching)
    q_plain_partial1 = new_db.make_query("bar",
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_plain_partial1 = new_db.get_query_result(q_plain_partial1).get_matches(0,10)
    assert r_plain_partial1[0] == 2
    # this query should return three matches (wildcard works)
    q_plain_partial2 = new_db.make_query("bar", analyzer=new_db.ANALYZER_PARTIAL)
    r_plain_partial2 = new_db.get_query_result(q_plain_partial2).get_matches(0,10)
    assert r_plain_partial2[0] == 3
    # return two matches (the wildcard is ignored without PARTIAL)
    q_plain_partial3 = new_db.make_query("bar*",
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_plain_partial3 = new_db.get_query_result(q_plain_partial3).get_matches(0,10)
    assert r_plain_partial3[0] == 2
    # partial matching at the start of the string
    # TODO: enable this as soon, as partial matching works at the beginning of text
    #q_plain_partial4 = new_db.make_query("*ar",
    #        analyzer=new_db.ANALYZER_EXACT)
    #        analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    #r_plain_partial4 = new_db.get_query_result(q_plain_partial4).get_matches(0,10)
    #assert r_plain_partial4[0] == 2
    # clean up
    clean_database()


def test_field_matching():
    """test if field specific searching works"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # do a field search with a tuple argument
    q_field1 = new_db.make_query(("fname1", "foo_field1"))
    r_field1 = new_db.get_query_result(q_field1).get_matches(0,10)
    assert r_field1[0] == 1
    # do a field search with a dict argument
    q_field2 = new_db.make_query({"fname1":"bar_field1"})
    r_field2 = new_db.get_query_result(q_field2).get_matches(0,10)
    assert r_field2[0] == 1
    # do an incomplete field search with a dict argument - should fail
    q_field3 = new_db.make_query({"fname2":"foo_field"})
    r_field3 = new_db.get_query_result(q_field3).get_matches(0,10)
    assert r_field3[0] == 0
    # do an AND field search with a dict argument
    q_field4 = new_db.make_query({"fname1":"foo_field1", "fname2":"foo_field2"}, require_all=True)
    r_field4 = new_db.get_query_result(q_field4).get_matches(0,10)
    assert r_field4[0] == 1
    # do an OR field search with a dict argument
    q_field5 = new_db.make_query({"fname1":"foo_field1", "fname2":"foo_field2"}, require_all=False)
    r_field5 = new_db.get_query_result(q_field5).get_matches(0,10)
    assert r_field5[0] == 2
    # do an incomplete field search with a partial field analyzer
    q_field6 = new_db.make_query({"fname1":"foo_field"}, analyzer=new_db.ANALYZER_PARTIAL)
    r_field6 = new_db.get_query_result(q_field6).get_matches(0,10)
    assert r_field6[0] == 1
    # clean up
    clean_database()

def test_field_analyzers():
    """test if we can change the analyzer of specific fields"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # do an incomplete field search with partial analyzer (configured for this field)
    q_field1 = new_db.make_query({"fname1":"bar_field"})
    r_field1 = new_db.get_query_result(q_field1).get_matches(0,10)
    assert r_field1[0] == 1
    # check the get/set field analyzer functions
    old_analyzer = new_db.get_field_analyzers("fname1")
    new_db.set_field_analyzers({"fname1":new_db.ANALYZER_EXACT})
    assert new_db.get_field_analyzers("fname1") == new_db.ANALYZER_EXACT
    new_db.set_field_analyzers({"fname1":new_db.ANALYZER_PARTIAL})
    assert new_db.get_field_analyzers("fname1") == new_db.ANALYZER_PARTIAL
    # restore previous setting
    new_db.set_field_analyzers({"fname1":old_analyzer})
    # check if ANALYZER_TOKENIZE is the default
    assert (new_db.get_field_analyzers("thisFieldDoesNotExist") & new_db.ANALYZER_TOKENIZE) > 0
    # do an incomplete field search - now we use the partial analyzer
    q_field2 = new_db.make_query({"fname1":"bar_field"}, analyzer=new_db.ANALYZER_PARTIAL)
    r_field2 = new_db.get_query_result(q_field2).get_matches(0,10)
    assert r_field2[0] == 1
    # clean up
    clean_database()

def test_and_queries():
    """test if AND queries work as expected"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # do an AND query (partial matching disabled)
    q_and1 = new_db.make_query("foo bar",
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_and1 = new_db.get_query_result(q_and1).get_matches(0,10)
    assert r_and1[0] == 2
    # do the same AND query in a different way
    q_and2 = new_db.make_query(["foo", "bar"],
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_and2 = new_db.get_query_result(q_and2).get_matches(0,10)
    assert r_and2[0] == 2
    # do an AND query without results
    q_and3 = new_db.make_query(["HELO", "bar", "med"],
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_and3 = new_db.get_query_result(q_and3).get_matches(0,10)
    assert r_and3[0] == 0
    # clean up
    clean_database()

def test_or_queries():
    """test if OR queries work as expected"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # do an OR query
    q_or1 = new_db.make_query("foo bar", require_all=False)
    r_or1 = new_db.get_query_result(q_or1).get_matches(0,10)
    assert r_or1[0] == 4
    # do the same or query in a different way
    q_or2 = new_db.make_query(["foo", "bar"], require_all=False)
    r_or2 = new_db.get_query_result(q_or2).get_matches(0,10)
    assert r_or2[0] == r_or1[0]
    # do an OR query with lots of results
    q_or3 = new_db.make_query(["HELO", "bar", "med"], require_all=False)
    r_or3 = new_db.get_query_result(q_or3).get_matches(0,10)
    assert r_or3[0] == 5
    # clean up
    clean_database()

def test_lower_upper_case():
    """test if case is ignored for queries and for indexed terms"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # use upper case search terms for lower case indexed terms
    q_case1 = new_db.make_query("BAR",
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_case1 = new_db.get_query_result(q_case1).get_matches(0,10)
    assert r_case1[0] == 2
    # use lower case search terms for upper case indexed terms
    q_case2 = new_db.make_query("helo")
    r_case2 = new_db.get_query_result(q_case2).get_matches(0,10)
    assert r_case2[0] == 3
    # use lower case search terms for lower case indexed terms
    q_case3 = new_db.make_query("bar",
            analyzer=(new_db.analyzer ^ new_db.ANALYZER_PARTIAL))
    r_case3 = new_db.get_query_result(q_case3).get_matches(0,10)
    assert r_case3[0] == 2
    # use upper case search terms for upper case indexed terms
    q_case4 = new_db.make_query("HELO")
    r_case4 = new_db.get_query_result(q_case4).get_matches(0,10)
    assert r_case4[0] == 3
    # clean up
    clean_database()

def test_tokenizing():
    """test if the TOKENIZE analyzer field setting is honoured"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # check if the plain term was tokenized
    q_token1 = new_db.make_query("rfv")
    r_token1 = new_db.get_query_result(q_token1).get_matches(0,10)
    assert r_token1[0] == 2
    # check if the field term was tokenized
    q_token2 = new_db.make_query({"fname1":"wsx"})
    r_token2 = new_db.get_query_result(q_token2).get_matches(0,10)
    assert r_token2[0] == 1
    # check that the other field term was not tokenized
    q_token3 = new_db.make_query({"fname2":"wsx"})
    r_token3 = new_db.get_query_result(q_token3).get_matches(0,10)
    assert r_token3[0] == 0
    # check that the other field term was not tokenized
    q_token4 = new_db.make_query({"fname2":"foo-bar.po"})
    #q_token4 = new_db.make_query("poo-foo.po")
    r_token4 = new_db.get_query_result(q_token4).get_matches(0,10)
    # problem can be fixed by adding "TOKENIZE" to the field before populating the database -> this essentially splits the document term into pieces
    assert r_token4[0] == 1
    # clean up
    clean_database()

def test_searching():
    """test if searching (retrieving specified field values) works"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    q_search1 = new_db.make_query({"fname1": "bar_field1"})
    r_search1 = new_db.search(q_search1, ["fname2", None])
    assert len(r_search1) == 1
    dict_search1 = r_search1[0]
    assert dict_search1.has_key("fname2") and \
            (dict_search1["fname2"] == ["foo_field2"])
    # a stupid way for checking, if the second field list is also correct
    # (without caring for the order of the list)
    assert dict_search1.has_key(None)
    # TODO: for now PyLucene cares for case, while xapian doesn't - FIXME
    list_search1_sorted = [item.lower() for item in dict_search1[None]]
    list_search1_sorted.sort()
    assert list_search1_sorted == ["foo", "helo"]
    # clean up
    clean_database()


def test_multiple_terms():
    """test if multiple terms can be added to a keyword"""
    # clean up everything first
    clean_database()
    # initialize the database with example content
    new_db = _get_indexer(DATABASE)
    create_example_content(new_db)
    # check for the first item ("foo")
    q_multiple1 = new_db.make_query({"multiple": "f"},
            analyzer=new_db.ANALYZER_PARTIAL)
    r_multiple1 = new_db.get_query_result(q_multiple1).get_matches(0,10)
    assert r_multiple1[0] == 1
    # check for the second item ("bar")
    q_multiple2 = new_db.make_query({"multiple": "bar"})
    r_multiple2 = new_db.get_query_result(q_multiple2).get_matches(0,10)
    assert r_multiple2[0] == 1
    # clean up
    clean_database()


def show_database(database):
    """print the complete database - for debugging purposes"""
    if hasattr(database, "database"):
        _show_database_xapian(database)
    else:
        _show_database_pylucene(database)


def _show_database_pylucene(database):
    database.flush()
    reader = database.reader
    for index in range(reader.maxDoc()):
        print reader.document(index).toString().encode("charmap")

def _show_database_xapian(database):
    import xapian
    doccount = database.database.get_doccount()
    max_doc_index = database.database.get_lastdocid()
    print "Database overview: %d items up to index %d" % (doccount, max_doc_index)
    for index in range(1, max_doc_index+1):
        try:
            document = database.database.get_document(index)
        except xapian.DocNotFoundError:
            continue
        # print the document's terms and their positions
        print "\tDocument [%d]: %s" % (index,
                str([(one_term.term, [posi for posi in one_term.positer])
                for one_term in document.termlist()]))


def _get_number_of_docs(database):
    if hasattr(database, "database"):
        # xapian
        return database.database.get_lastdocid()
    else:
        # pylucene
        database.flush()
        return database.reader.numDocs()

def get_engine_name(database):
    return database.__module__

def report_whitelisted_success(db, name):
    """ Output a warning message regarding a successful unittest, that was
    supposed to fail for a specific indexing engine.
    As this test works now for the engine, the whitelisting should be removed.
    """
    print "the test '%s' works again for '%s' - please remove the exception" \
            % (name, get_engine_name(db))

def report_whitelisted_failure(db, name):
    """ Output a warning message regarding a unittest, that was supposed to fail
    for a specific indexing engine.
    Since the test behaves as expected (it fails), this is just for reminding
    developers on these open issues of the indexing engine support.
    """
    print "the test '%s' fails - as expected for '%s'" % (name,
            get_engine_name(db))

def assert_whitelisted(db, assert_value, white_list_engines, name_of_check):
    """ Do an assertion, but ignoring failure for specific indexing engines.
    This can be used for almost-complete implementations, that just need
    a little bit of improvement for full compliance.
    """
    try:
        assert assert_value
        if get_engine_name(db) in white_list_engines:
            report_whitelisted_success(db, name_of_check)
    except AssertionError:
        if get_engine_name(db) in white_list_engines:
            report_whitelisted_failure(db, name_of_check)
        else:
            raise


if __name__ == "__main__":
    # if an argument is given: use it as a database directory and show it
    if len(sys.argv) > 1:
        db = _get_indexer(sys.argv[1])
        show_database(db)
        sys.exit(0)
    for engine in ORDER_OF_TESTS:
        default_engine = engine
        # cleanup the database after interrupted tests
        clean_database()
        engine_name = get_engine_name(_get_indexer(DATABASE))
        if engine_name == default_engine:
            print "************ running tests for '%s' *****************" \
                    % engine_name
        else:
            print "************ SKIPPING tests for '%s' *****************" \
                    % default_engine
            continue
        test_create_database()
        test_open_database()
        test_make_queries()
        test_partial_text_matching()
        test_field_matching()
        test_field_analyzers()
        test_and_queries()
        test_or_queries()
        test_lower_upper_case()
        test_tokenizing()
        test_searching()
        test_multiple_terms()
        # TODO: add test for document deletion
        # TODO: add test for transaction handling
        # TODO: add test for multiple engine/database handling in "get_indexer"
    clean_database()

