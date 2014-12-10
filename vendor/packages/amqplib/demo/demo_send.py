#!/usr/bin/env python
"""
Test AMQP library.

Send a message to the corresponding demo_receive.py script, any
arguments to this program are joined together and sent as a message
body.

2007-11-11 Barry Pederson <bp@barryp.org>

"""
import sys
import time
from optparse import OptionParser

import amqplib.client_0_8 as amqp

def main():
    parser = OptionParser(usage='usage: %prog [options] message\nexample: %prog hello world')
    parser.add_option('--host', dest='host',
                        help='AMQP server to connect to (default: %default)',
                        default='localhost')
    parser.add_option('-u', '--userid', dest='userid',
                        help='userid to authenticate as (default: %default)',
                        default='guest')
    parser.add_option('-p', '--password', dest='password',
                        help='password to authenticate with (default: %default)',
                        default='guest')
    parser.add_option('--ssl', dest='ssl', action='store_true',
                        help='Enable SSL (default: not enabled)',
                        default=False)

    options, args = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    msg_body = ' '.join(args)

    conn = amqp.Connection(options.host, userid=options.userid, password=options.password, ssl=options.ssl)

    ch = conn.channel()
    ch.access_request('/data', active=True, write=True)

    ch.exchange_declare('myfan', 'fanout', auto_delete=True)

    msg = amqp.Message(msg_body, content_type='text/plain', application_headers={'foo': 7, 'bar': 'baz'})

    ch.basic_publish(msg, 'myfan')

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()
