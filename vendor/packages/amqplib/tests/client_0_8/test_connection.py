#!/usr/bin/env python
"""
Test amqplib.client_0_8.connection module

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

import gc
import sys
import time
import unittest

import settings


from amqplib.client_0_8 import Connection

class TestConnection(unittest.TestCase):
    def setUp(self):
        self.conn = Connection(**settings.connect_args)

    def tearDown(self):
        if self.conn:
            self.conn.close()

    def test_channel(self):
        ch = self.conn.channel(1)
        self.assertEqual(ch.channel_id, 1)

        ch2 = self.conn.channel()
        self.assertNotEqual(ch2.channel_id, 1)

        ch.close()
        ch2.close()


    def test_close(self):
        """
        Make sure we've broken various references when closing
        channels and connections, to help with GC.

        """
        #
        # Create a channel and make sure it's linked as we'd expect
        #
        ch = self.conn.channel()
        self.assertEqual(1 in self.conn.channels, True)
        self.assertEqual(ch.connection, self.conn)
        self.assertEqual(ch.is_open, True)

        #
        # Close the channel and make sure the references are broken
        # that we expect.
        #
        ch.close()
        self.assertEqual(ch.connection, None)
        self.assertEqual(1 in self.conn.channels, False)
        self.assertEqual(ch.callbacks, {})
        self.assertEqual(ch.is_open, False)

        #
        # Close the connection and make sure the references we expect
        # are gone.
        #
        self.conn.close()
        self.assertEqual(self.conn.connection, None)
        self.assertEqual(self.conn.channels, None)

    def test_gc_closed(self):
        """
        Make sure we've broken various references when closing
        channels and connections, to help with GC.

        gc.garbage: http://docs.python.org/library/gc.html#gc.garbage
            "A list of objects which the collector found to be
            unreachable but could not be freed (uncollectable objects)."
        """
        unreachable_before = len(gc.garbage)
        #
        # Create a channel and make sure it's linked as we'd expect
        #
        ch = self.conn.channel()
        self.assertEqual(1 in self.conn.channels, True)

        #
        # Close the connection and make sure the references we expect
        # are gone.
        #
        self.conn.close()

        gc.collect()
        gc.collect()
        gc.collect()
        self.assertEqual(unreachable_before, len(gc.garbage))

    def test_gc_forget(self):
        """
        Make sure the connection gets gc'ed when there is no more
        references to it.
        """
        unreachable_before = len(gc.garbage)

        ch = self.conn.channel()
        self.assertEqual(1 in self.conn.channels, True)

        # remove all the references
        self.conn = None
        ch = None

        gc.collect()
        gc.collect()
        gc.collect()
        self.assertEqual(unreachable_before, len(gc.garbage))


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConnection)
    unittest.TextTestRunner(**settings.test_args).run(suite)


if __name__ == '__main__':
    main()
