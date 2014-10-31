#!/usr/bin/env python
"""
Test support for 'with' statements in Python >= 2.5

"""
# Copyright (C) 2009 Barry Pederson <bp@barryp.org>
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

from __future__ import with_statement
import unittest

import settings

from amqplib.client_0_8 import Connection, Message


class TestChannel(unittest.TestCase):

    def test_with(self):
        with Connection(**settings.connect_args) as conn:
            self.assertEqual(conn.transport is None, False)

            with conn.channel(1) as ch:
                self.assertEqual(1 in conn.channels, True)

                #
                # Do something with the channel
                #
                ch.access_request('/data', active=True, write=True)
                ch.exchange_declare('unittest.fanout', 'fanout', auto_delete=True)

                msg = Message('unittest message',
                    content_type='text/plain',
                    application_headers={'foo': 7, 'bar': 'baz'})

                ch.basic_publish(msg, 'unittest.fanout')

            #
            # check that the channel was closed
            #
            self.assertEqual(1 in conn.channels, False)
            self.assertEqual(ch.is_open, False)

        #
        # Check that the connection was closed
        #
        self.assertEqual(conn.transport, None)


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChannel)
    unittest.TextTestRunner(**settings.test_args).run(suite)


if __name__ == '__main__':
    main()
