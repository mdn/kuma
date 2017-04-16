#!/usr/bin/env python
"""
Test amqplib.client_0_8.serialization, checking conversions
between byte streams and higher level objects.

"""
# Copyright (C) 2007-2008 Barry Pederson <bp@barryp.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301

from datetime import datetime
from decimal import Decimal
from random import randint
import unittest

import settings

from amqplib.client_0_8.serialization import AMQPReader, AMQPWriter

class TestSerialization(unittest.TestCase):
    def test_empty_writer(self):
        w = AMQPWriter()
        self.assertEqual(w.getvalue(), '')

    #
    # Bits
    #
    def test_single_bit(self):
        for val, check in [(True, '\x01'), (False, '\x00')]:
            w = AMQPWriter()
            w.write_bit(val)
            s = w.getvalue()

            self.assertEqual(s, check)

            r = AMQPReader(s)
            self.assertEqual(r.read_bit(), val)

    def test_multiple_bits(self):
        w = AMQPWriter()
        w.write_bit(True)
        w.write_bit(True)
        w.write_bit(False)
        w.write_bit(True)
        s = w.getvalue()

        self.assertEqual(s, '\x0b')

        r = AMQPReader(s)
        self.assertEqual(r.read_bit(), True)
        self.assertEqual(r.read_bit(), True)
        self.assertEqual(r.read_bit(), False)
        self.assertEqual(r.read_bit(), True)


    def test_multiple_bits2(self):
        """
        Check bits mixed with non-bits
        """
        w = AMQPWriter()
        w.write_bit(True)
        w.write_bit(True)
        w.write_bit(False)
        w.write_octet(10)
        w.write_bit(True)
        s = w.getvalue()

        self.assertEqual(s, '\x03\x0a\x01')

        r = AMQPReader(s)
        self.assertEqual(r.read_bit(), True)
        self.assertEqual(r.read_bit(), True)
        self.assertEqual(r.read_bit(), False)
        self.assertEqual(r.read_octet(), 10)
        self.assertEqual(r.read_bit(), True)

    def test_multiple_bits3(self):
        """
        Check bit groups that span multiple bytes
        """
        w = AMQPWriter()

        # Spit out 20 bits
        for i in range(10):
            w.write_bit(True)
            w.write_bit(False)

        s = w.getvalue()

        self.assertEquals(s, '\x55\x55\x05')

        r = AMQPReader(s)
        for i in range(10):
            self.assertEqual(r.read_bit(), True)
            self.assertEqual(r.read_bit(), False)

    #
    # Octets
    #
    def test_octet(self):
        for val in range(256):
            w = AMQPWriter()
            w.write_octet(val)
            s = w.getvalue()
            self.assertEqual(s, chr(val))

            r = AMQPReader(s)
            self.assertEqual(r.read_octet(), val)

    def test_octet_invalid(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_octet, -1)

    def test_octet_invalid2(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_octet, 256)

    #
    # Shorts
    #
    def test_short(self):
        for i in range(256):
            val = randint(0, 65535)
            w = AMQPWriter()
            w.write_short(val)
            s = w.getvalue()

            r = AMQPReader(s)
            self.assertEqual(r.read_short(), val)

    def test_short_invalid(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_short, -1)

    def test_short_invalid2(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_short, 65536)

    #
    # Longs
    #
    def test_long(self):
        for i in range(256):
            val = randint(0, (2**32) - 1)
            w = AMQPWriter()
            w.write_long(val)
            s = w.getvalue()

            r = AMQPReader(s)
            self.assertEqual(r.read_long(), val)

    def test_long_invalid(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_long, -1)

    def test_long_invalid2(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_long, 2**32)

    #
    # LongLongs
    #
    def test_longlong(self):
        for i in range(256):
            val = randint(0, (2**64) - 1)
            w = AMQPWriter()
            w.write_longlong(val)
            s = w.getvalue()

            r = AMQPReader(s)
            self.assertEqual(r.read_longlong(), val)

    def test_longlong_invalid(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_longlong, -1)

    def test_longlong_invalid2(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_longlong, 2**64)

    #
    # Shortstr
    #
    def test_empty_shortstr(self):
        w = AMQPWriter()
        w.write_shortstr('')
        s = w.getvalue()

        self.assertEqual(s, '\x00')

        r = AMQPReader(s)
        self.assertEqual(r.read_shortstr(), '')

    def test_shortstr(self):
        w = AMQPWriter()
        w.write_shortstr('hello')
        s = w.getvalue()
        self.assertEqual(s, '\x05hello')

        r = AMQPReader(s)
        self.assertEqual(r.read_shortstr(), 'hello')

    def test_shortstr_unicode(self):
        w = AMQPWriter()
        w.write_shortstr(u'hello')
        s = w.getvalue()
        self.assertEqual(s, '\x05hello')

        r = AMQPReader(s)
        self.assertEqual(r.read_shortstr(), u'hello')

    def test_long_shortstr(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_shortstr, 'x' * 256)

    def test_long_shortstr_unicode(self):
        w = AMQPWriter()
        self.assertRaises(ValueError, w.write_shortstr, u'\u0100' * 128)


    #
    # Longstr
    #
    def test_empty_longstr(self):
        w = AMQPWriter()
        w.write_longstr('')
        s = w.getvalue()

        self.assertEqual(s, '\x00\x00\x00\x00')

        r = AMQPReader(s)
        self.assertEqual(r.read_longstr(), '')

    def test_longstr(self):
        val = 'a' * 512
        w = AMQPWriter()
        w.write_longstr(val)
        s = w.getvalue()

        self.assertEqual(s, '\x00\x00\x02\x00' + ('a' * 512))

        r = AMQPReader(s)
        self.assertEqual(r.read_longstr(), val)

    def test_longstr_unicode(self):
        val = u'a' * 512
        w = AMQPWriter()
        w.write_longstr(val)
        s = w.getvalue()

        self.assertEqual(s, '\x00\x00\x02\x00' + ('a' * 512))

        r = AMQPReader(s)
        self.assertEqual(r.read_longstr(), val)

    #
    # Table
    #
    def test_table_empty(self):
        val = {}
        w = AMQPWriter()
        w.write_table(val)
        s = w.getvalue()

        self.assertEqual(s, '\x00\x00\x00\x00')

        r = AMQPReader(s)
        self.assertEqual(r.read_table(), val)

    def test_table(self):
        val = {'foo': 7}
        w = AMQPWriter()
        w.write_table(val)
        s = w.getvalue()

        self.assertEqual(s, '\x00\x00\x00\x09\x03fooI\x00\x00\x00\x07')

        r = AMQPReader(s)
        self.assertEqual(r.read_table(), val)


    def test_table_multi(self):
        val = {
            'foo': 7,
            'bar': Decimal('123345.1234'),
            'baz': 'this is some random string I typed',
            'ubaz': u'And something in unicode',
            'dday_aniv': datetime(1994, 6, 6),
            'more': {
                        'abc': -123,
                        'def': 'hello world',
                        'now': datetime(2007, 11, 11, 21, 14, 31),
                        'qty': Decimal('-123.45'),
                        'blank': {},
                        'extra':
                            {
                            'deeper': 'more strings',
                            'nums': -12345678,
                            },
                    }
            }

        w = AMQPWriter()
        w.write_table(val)
        s = w.getvalue()

        r = AMQPReader(s)
        self.assertEqual(r.read_table(), val)


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSerialization)
    unittest.TextTestRunner(**settings.test_args).run(suite)


if __name__ == '__main__':
    main()
