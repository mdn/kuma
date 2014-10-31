from __future__ import absolute_import
from __future__ import with_statement

import socket

from kombu.connection import BrokerConnection
from kombu.entity import Exchange, Queue
from kombu.messaging import Consumer, Producer

from kombu.tests.utils import TestCase


class test_MemoryTransport(TestCase):

    def setUp(self):
        self.c = BrokerConnection(transport="memory")
        self.e = Exchange("test_transport_memory")
        self.q = Queue("test_transport_memory",
                       exchange=self.e,
                       routing_key="test_transport_memory")
        self.q2 = Queue("test_transport_memory2",
                        exchange=self.e,
                        routing_key="test_transport_memory2")

    def test_produce_consume_noack(self):
        channel = self.c.channel()
        producer = Producer(channel, self.e)
        consumer = Consumer(channel, self.q, no_ack=True)

        for i in range(10):
            producer.publish({"foo": i}, routing_key="test_transport_memory")

        _received = []

        def callback(message_data, message):
            _received.append(message)

        consumer.register_callback(callback)
        consumer.consume()

        while 1:
            if len(_received) == 10:
                break
            self.c.drain_events()

        self.assertEqual(len(_received), 10)

    def test_produce_consume(self):
        channel = self.c.channel()
        producer = Producer(channel, self.e)
        consumer1 = Consumer(channel, self.q)
        consumer2 = Consumer(channel, self.q2)
        self.q2(channel).declare()

        for i in range(10):
            producer.publish({"foo": i}, routing_key="test_transport_memory")
        for i in range(10):
            producer.publish({"foo": i}, routing_key="test_transport_memory2")

        _received1 = []
        _received2 = []

        def callback1(message_data, message):
            _received1.append(message)
            message.ack()

        def callback2(message_data, message):
            _received2.append(message)
            message.ack()

        consumer1.register_callback(callback1)
        consumer2.register_callback(callback2)

        consumer1.consume()
        consumer2.consume()

        while 1:
            if len(_received1) + len(_received2) == 20:
                break
            self.c.drain_events()

        self.assertEqual(len(_received1) + len(_received2), 20)

        # compression
        producer.publish({"compressed": True},
                         routing_key="test_transport_memory",
                         compression="zlib")
        m = self.q(channel).get()
        self.assertDictEqual(m.payload, {"compressed": True})

        # queue.delete
        for i in range(10):
            producer.publish({"foo": i}, routing_key="test_transport_memory")
        self.assertTrue(self.q(channel).get())
        self.q(channel).delete()
        self.q(channel).declare()
        self.assertIsNone(self.q(channel).get())

        # queue.purge
        for i in range(10):
            producer.publish({"foo": i}, routing_key="test_transport_memory2")
        self.assertTrue(self.q2(channel).get())
        self.q2(channel).purge()
        self.assertIsNone(self.q2(channel).get())

    def test_drain_events(self):
        with self.assertRaises(socket.timeout):
            self.c.drain_events(timeout=0.1)

        c1 = self.c.channel()
        c2 = self.c.channel()

        with self.assertRaises(socket.timeout):
            self.c.drain_events(timeout=0.1)

        del(c1)  # so pyflakes doesn't complain.
        del(c2)

    def test_drain_events_unregistered_queue(self):
        c1 = self.c.channel()

        class Cycle(object):

            def get(self, timeout=None):
                return ("foo", "foo"), c1

        self.c.transport.cycle = Cycle()
        with self.assertRaises(KeyError):
            self.c.drain_events()

    def test_queue_for(self):
        chan = self.c.channel()
        chan.queues.clear()

        x = chan._queue_for("foo")
        self.assertTrue(x)
        self.assertIs(chan._queue_for("foo"), x)
