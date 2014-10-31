#!/usr/bin/python
# -*- coding: utf-8 -*-

import cPickle
import sys
import os
import unittest
import uuid
sys.path.insert(0, os.pardir)
sys.path.append(os.getcwd())


from carrot.serialization import registry

# For content_encoding tests
unicode_string = u'abcdé\u8463'
unicode_string_as_utf8 = unicode_string.encode('utf-8')
latin_string = u'abcdé'
latin_string_as_latin1 = latin_string.encode('latin-1')
latin_string_as_utf8 = latin_string.encode('utf-8')


# For serialization tests
py_data = {"string": "The quick brown fox jumps over the lazy dog",
        "int": 10,
        "float": 3.14159265,
        "unicode": u"Thé quick brown fox jumps over thé lazy dog",
        "list": ["george", "jerry", "elaine", "cosmo"],
}

# JSON serialization tests
json_data = ('{"int": 10, "float": 3.1415926500000002, '
             '"list": ["george", "jerry", "elaine", "cosmo"], '
             '"string": "The quick brown fox jumps over the lazy '
             'dog", "unicode": "Th\\u00e9 quick brown fox jumps over '
             'th\\u00e9 lazy dog"}')

# Pickle serialization tests
pickle_data = cPickle.dumps(py_data)

# YAML serialization tests
yaml_data = ('float: 3.1415926500000002\nint: 10\n'
             'list: [george, jerry, elaine, cosmo]\n'
             'string: The quick brown fox jumps over the lazy dog\n'
             'unicode: "Th\\xE9 quick brown fox '
             'jumps over th\\xE9 lazy dog"\n')


msgpack_py_data = dict(py_data)
# msgpack only supports tuples
msgpack_py_data["list"] = tuple(msgpack_py_data["list"])
# Unicode chars are lost in transmit :(
msgpack_py_data["unicode"] = 'Th quick brown fox jumps over th lazy dog'
msgpack_data = ('\x85\xa3int\n\xa5float\xcb@\t!\xfbS\xc8\xd4\xf1\xa4list'
                '\x94\xa6george\xa5jerry\xa6elaine\xa5cosmo\xa6string\xda'
                '\x00+The quick brown fox jumps over the lazy dog\xa7unicode'
                '\xda\x00)Th quick brown fox jumps over th lazy dog')


def say(m):
    sys.stderr.write("%s\n" % (m, ))


class TestSerialization(unittest.TestCase):

    def test_content_type_decoding(self):
        content_type = 'plain/text'

        self.assertEquals(unicode_string,
                          registry.decode(
                              unicode_string_as_utf8,
                              content_type='plain/text',
                              content_encoding='utf-8'))
        self.assertEquals(latin_string,
                          registry.decode(
                              latin_string_as_latin1,
                              content_type='application/data',
                              content_encoding='latin-1'))

    def test_content_type_binary(self):
        content_type = 'plain/text'

        self.assertNotEquals(unicode_string,
                             registry.decode(
                                 unicode_string_as_utf8,
                                 content_type='application/data',
                                 content_encoding='binary'))

        self.assertEquals(unicode_string_as_utf8,
                          registry.decode(
                              unicode_string_as_utf8,
                              content_type='application/data',
                              content_encoding='binary'))

    def test_content_type_encoding(self):
        # Using the "raw" serializer
        self.assertEquals(unicode_string_as_utf8,
                          registry.encode(
                              unicode_string, serializer="raw")[-1])
        self.assertEquals(latin_string_as_utf8,
                          registry.encode(
                              latin_string, serializer="raw")[-1])
        # And again w/o a specific serializer to check the
        # code where we force unicode objects into a string.
        self.assertEquals(unicode_string_as_utf8,
                            registry.encode(unicode_string)[-1])
        self.assertEquals(latin_string_as_utf8,
                            registry.encode(latin_string)[-1])

    def test_json_decode(self):
        self.assertEquals(py_data,
                          registry.decode(
                              json_data,
                              content_type='application/json',
                              content_encoding='utf-8'))

    def test_json_encode(self):
        self.assertEquals(registry.decode(
                              registry.encode(py_data, serializer="json")[-1],
                              content_type='application/json',
                              content_encoding='utf-8'),
                          registry.decode(
                              json_data,
                              content_type='application/json',
                              content_encoding='utf-8'))

    def test_msgpack_decode(self):
        try:
            import msgpack
        except ImportError:
            return say("* msgpack-python not installed, will not execute "
                       "related tests.")
        self.assertEquals(msgpack_py_data,
                          registry.decode(
                              msgpack_data,
                              content_type='application/x-msgpack',
                              content_encoding='binary'))

    def test_msgpack_encode(self):
        try:
            import msgpack
        except ImportError:
            return say("* msgpack-python not installed, will not execute "
                       "related tests.")
        self.assertEquals(registry.decode(
                registry.encode(msgpack_py_data, serializer="msgpack")[-1],
                content_type='application/x-msgpack',
                content_encoding='binary'),
                registry.decode(
                    msgpack_data,
                    content_type='application/x-msgpack',
                    content_encoding='binary'))


    def test_yaml_decode(self):
        try:
            import yaml
        except ImportError:
            return say("* PyYAML not installed, will not execute "
                       "related tests.")
        self.assertEquals(py_data,
                          registry.decode(
                              yaml_data,
                              content_type='application/x-yaml',
                              content_encoding='utf-8'))

    def test_yaml_encode(self):
        try:
            import yaml
        except ImportError:
            return say("* PyYAML not installed, will not execute "
                       "related tests.")
        self.assertEquals(registry.decode(
                              registry.encode(py_data, serializer="yaml")[-1],
                              content_type='application/x-yaml',
                              content_encoding='utf-8'),
                          registry.decode(
                              yaml_data,
                              content_type='application/x-yaml',
                              content_encoding='utf-8'))

    def test_pickle_decode(self):
        self.assertEquals(py_data,
                          registry.decode(
                              pickle_data,
                              content_type='application/x-python-serialize',
                              content_encoding='binary'))

    def test_pickle_encode(self):
        self.assertEquals(pickle_data,
                          registry.encode(py_data,
                              serializer="pickle")[-1])


if __name__ == '__main__':
    unittest.main()
