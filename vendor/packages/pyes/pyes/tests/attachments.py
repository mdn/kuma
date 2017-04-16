#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import os
from pyestest import ESTestCase
from pyes import TermQuery, file_to_attachment

class TestFileSaveTestCase(ESTestCase):
    def test_filesave(self):
        mapping = {
                   "my_attachment" : { "type" : "attachment",
                                      'fields':{
                                        "file" : {'store' : "yes"},
                                        "date" : {'store' : "yes"},
                                        "author" : {'store': "yes"},
                                        "title" : {'store': "yes"}, }
                                      }
                   }
        self.conn.create_index("test-index")
        self.conn.put_mapping("test-type", {"test-type":{'properties':mapping}}, ["test-index"])
        self.conn.refresh(["test-index"])
        self.conn.get_mapping("test-type", ["test-index"])
        name = "__init__.py"
        content = open(name, "rb").read()
        self.conn.put_file(name, "test-index", "test-type", 1)
        self.conn.refresh(["test-index"])
        _ = self.conn.get_mapping("test-type", ["test-index"])
        nname, ncontent = self.conn.get_file("test-index", "test-type", 1)
        self.assertEquals(name, nname)
        self.assertEquals(content, ncontent)

class QueryAttachmentTestCase(ESTestCase):
    def setUp(self):
        super(QueryAttachmentTestCase, self).setUp()
        mapping = {
                   "attachment" : { "type" : "attachment",
                                      'fields':{
                                        "file" : {'store' : "yes"},
                                        "date" : {'store' : "yes"},
                                        "author" : {'store': "yes"},
                                        "title" : {'store': "yes", "term_vector" : "with_positions_offsets"},
                                        "attachment" : {'store': "yes"},
                                        }
                                      },
                   'uuid': {'boost': 1.0,
                           'index': 'not_analyzed',
                           'store': 'yes',
                           'type': u'string'}
                   }
#        mapping = {
#            "test-type": {
#                "_index": {"enabled": "yes"},
#                "_id": {"store": "yes"},
#                "properties": {
#                    "attachment": {
#                        "type": "attachment",
#                        "fields": {
#                            "title": {"store": "yes", "term_vector" : "with_positions_offsets"},
#                            "attachment": {"store":"yes", "term_vector" : "with_positions_offsets"}
#                        },
#                        "store":"yes"
#                        
#                    },
#                    "uuid": {"type": "string", "store": "yes", "index": "not_analyzed"}
#                },
#                "_all": {"store": "yes", "term_vector": "with_positions_offsets"}
#            }
#        }
        self.conn.debug_dump = True
        self.conn.create_index("test-index")
        self.conn.put_mapping("test-type", {"test-type":{'properties':mapping}}, ["test-index"])
        self.conn.refresh(["test-index"])
        self.conn.get_mapping("test-type", ["test-index"])
        self.conn.index({"attachment":file_to_attachment(os.path.join("data", "testXHTML.html")), "uuid":"1" }, "test-index", "test-type", 1)
        self.conn.refresh(["test-index"])

    def test_TermQuery(self):
        q = TermQuery("uuid", "1").search(fields=['attachment', 'attachment.author', 'attachment.title', 'attachment.date'])
#        q = TermQuery("uuid", "1", fields=['*'])
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)
        self.assertEquals(result['hits']['hits'][0]['fields']['attachment.author'], u'Tika Developers')
