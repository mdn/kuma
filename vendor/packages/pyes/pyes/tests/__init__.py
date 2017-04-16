#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
from pyestest import ESTestCase, get_conn

def setUp():
    """Package level setup.

    For tests which don't modify the index, we don't want to have the overhead
    of setting up a test index, so we just set up test-pindex once, and use it
    for all tests.

    """
    mapping = {
        u'parsedtext': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'string',
            "term_vector" : "with_positions_offsets"},
        u'name': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'string',
            "term_vector" : "with_positions_offsets"},
        u'title': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'string',
            "term_vector" : "with_positions_offsets"},
        u'pos': {
            'store': 'yes',
            'type': u'integer'},
        u'doubles': {
            'store': 'yes',
            'type': u'double'},
        u'uuid': {
            'boost': 1.0,
            'index': 'not_analyzed',
            'store': 'yes',
            'type': u'string'}}
        
    conn = get_conn()
    conn.delete_index_if_exists("test-pindex")
    conn.create_index("test-pindex")
    conn.put_mapping("test-type", {'properties':mapping}, ["test-pindex"])
    conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "uuid":"11111", "position":1, "doubles":[1.0, 2.0, 3.0]}, "test-pindex", "test-type", 1)
    conn.index({"name":"Bill Baloney", "parsedtext":"Joe Testere nice guy", "uuid":"22222", "position":2, "doubles":[0.1, 0.2, 0.3]}, "test-pindex", "test-type", 2)
    conn.refresh(["test-pindex"])

def tearDown():
    """Remove the package level index.

    """
    conn = get_conn()
    conn.delete_index_if_exists("test-pindex")
