#!/usr/bin/env python
"""
AMQP Clock

Fires off simple messages at one-minute intervals to a topic
exchange named 'clock', with the topic of the message being
the local time as 'year.month.date.dow.hour.minute',
for example: '2007.11.26.1.12.33', where the dow (day of week)
is 0 for Sunday, 1 for Monday, and so on (similar to Unix crontab).

A consumer could then bind a queue to the routing key '#.0'
for example to get a message at the beginning of each hour.

2007-11-26 Barry Pederson <bp@barryp.org>

"""
from datetime import datetime
from optparse import OptionParser
from time import sleep

import amqplib.client_0_8 as amqp
Message = amqp.Message

EXCHANGE_NAME = 'clock'
TOPIC_PATTERN = '%Y.%m.%d.%w.%H.%M' # Python datetime.strftime() pattern

def main():
    parser = OptionParser()
    parser.add_option('--host', dest='host',
                        help='AMQP server to connect to (default: %default)',
                        default='localhost')
    parser.add_option('-u', '--userid', dest='userid',
                        help='AMQP userid to authenticate as (default: %default)',
                        default='guest')
    parser.add_option('-p', '--password', dest='password',
                        help='AMQP password to authenticate with (default: %default)',
                        default='guest')
    parser.add_option('--ssl', dest='ssl', action='store_true',
                        help='Enable SSL with AMQP server (default: not enabled)',
                        default=False)

    options, args = parser.parse_args()

    conn = amqp.Connection(options.host, options.userid, options.password)
    ch = conn.channel()
    ch.access_request('/data', write=True, active=True)
    ch.exchange_declare(EXCHANGE_NAME, type='topic')

    # Make sure our first message is close to the beginning
    # of a minute
    now = datetime.now()
    if now.second > 0:
        sleep(60 - now.second)

    while True:
        now = datetime.now()
        msg = Message(timestamp=now)
        msg_topic = now.strftime(TOPIC_PATTERN)
        ch.basic_publish(msg, EXCHANGE_NAME, routing_key=msg_topic)

        # Don't know how long the basic_publish took, so
        # grab the time again.
        now = datetime.now()
        sleep(60 - now.second)

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()
