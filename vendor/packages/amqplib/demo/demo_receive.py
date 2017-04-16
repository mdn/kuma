#!/usr/bin/env python
"""
Test AMQP library.

Repeatedly receive messages from the demo_send.py
script, until it receives a message with 'quit' as the body.

2007-11-11 Barry Pederson <bp@barryp.org>

"""
from optparse import OptionParser

import amqplib.client_0_8 as amqp


def callback(msg):
    for key, val in msg.properties.items():
        print '%s: %s' % (key, str(val))
    for key, val in msg.delivery_info.items():
        print '> %s: %s' % (key, str(val))

    print ''
    print msg.body
    print '-------'
    msg.channel.basic_ack(msg.delivery_tag)

    #
    # Cancel this callback
    #
    if msg.body == 'quit':
        msg.channel.basic_cancel(msg.consumer_tag)


def main():
    parser = OptionParser()
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

    conn = amqp.Connection(options.host, userid=options.userid, password=options.password, ssl=options.ssl)

    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)

    ch.exchange_declare('myfan', 'fanout', auto_delete=True)
    qname, _, _ = ch.queue_declare()
    ch.queue_bind(qname, 'myfan')
    ch.basic_consume(qname, callback=callback)

    #
    # Loop as long as the channel has callbacks registered
    #
    while ch.callbacks:
        ch.wait()

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()
