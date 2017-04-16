#!/usr/bin/env python
"""
Test amqplib.client_0_8.exceptions module

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

import unittest

import settings

from amqplib.client_0_8.exceptions import *


class TestException(unittest.TestCase):
    def test_exception(self):
        exc = AMQPException(7, 'My Error', (10, 10))
        self.assertEqual(exc.amqp_reply_code, 7)
        self.assertEqual(exc.amqp_reply_text, 'My Error')
        self.assertEqual(exc.amqp_method_sig, (10, 10))
        self.assertEqual(exc.args,
            (7, 'My Error', (10, 10), 'Connection.start'))


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestException)
    unittest.TextTestRunner(**settings.test_args).run(suite)


if __name__ == '__main__':
    main()
