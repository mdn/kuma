import os
import sys
import unittest
import pickle
import time

from itertools import count

sys.path.insert(0, os.pardir)
sys.path.append(os.getcwd())

from carrot.messaging import Consumer, Publisher, ConsumerSet
from carrot import serialization
from tests.utils import establish_test_connection


class AdvancedDataType(object):

    def __init__(self, something):
        self.data = something


def fetch_next_message(consumer):
    while True:
        message = consumer.fetch()
        if message:
            return message


class BackendMessagingCase(unittest.TestCase):
    nextq = count(1).next

    def setUp(self):
        self.conn = establish_test_connection()
        self.queue = TEST_QUEUE
        self.exchange = TEST_EXCHANGE
        self.routing_key = TEST_ROUTING_KEY

    def create_consumer(self, **options):
        queue = "%s%s" % (self.queue, self.nextq())
        return Consumer(connection=self.conn,
                        queue=queue, exchange=self.exchange,
                        routing_key=self.routing_key, **options)

    def create_consumerset(self, queues={}, consumers=[], **options):
        return ConsumerSet(connection=self.conn,
                           from_dict=queues, consumers=consumers, **options)

    def create_publisher(self, exchange=None, routing_key=None, **options):
        exchange = exchange or self.exchange
        routing_key = routing_key or self.routing_key
        return Publisher(connection=self.conn,
                        exchange=exchange, routing_key=routing_key,
                        **options)

    def test_regression_implied_auto_delete(self):
        consumer = self.create_consumer(exclusive=True, auto_declare=False)
        self.assertTrue(consumer.auto_delete, "exclusive implies auto_delete")
        consumer.close()

        consumer = self.create_consumer(durable=True, auto_delete=False,
                                        auto_declare=False)
        self.assertFalse(consumer.auto_delete,
            """durable does *not* imply auto_delete.
            regression: http://github.com/ask/carrot/issues/closed#issue/2""")
        consumer.close()

    def test_consumer_options(self):
        opposite_defaults = {
                "queue": "xyxyxyxy",
                "exchange": "xyxyxyxy",
                "routing_key": "xyxyxyxy",
                "durable": False,
                "exclusive": True,
                "auto_delete": True,
                "exchange_type": "topic",
        }
        consumer = Consumer(connection=self.conn, **opposite_defaults)
        for opt_name, opt_value in opposite_defaults.items():
            self.assertEquals(getattr(consumer, opt_name), opt_value)
        consumer.close()

    def test_consumer_backend(self):
        consumer = self.create_consumer()
        self.assertTrue(consumer.backend.connection is self.conn)
        consumer.close()

    def test_consumer_queue_declared(self):
        consumer = self.create_consumer()
        self.assertTrue(consumer.backend.queue_exists(consumer.queue))
        consumer.close()

    def test_consumer_callbacks(self):
        consumer = self.create_consumer()
        publisher = self.create_publisher()

        # raises on no callbacks
        self.assertRaises(NotImplementedError, consumer.receive, {}, {})

        callback1_scratchpad = {}

        def callback1(message_data, message):
            callback1_scratchpad["message_data"] = message_data

        callback2_scratchpad = {}

        def callback2(message_data, message):
            callback2_scratchpad.update({"delivery_tag": message.delivery_tag,
                                         "message_body": message.body})

        self.assertFalse(consumer.callbacks, "no default callbacks")
        consumer.register_callback(callback1)
        consumer.register_callback(callback2)
        self.assertEquals(len(consumer.callbacks), 2, "callbacks registered")

        self.assertTrue(consumer.callbacks[0] is callback1,
                "callbacks are ordered")
        self.assertTrue(consumer.callbacks[1] is callback2,
                "callbacks are ordered")

        body = {"foo": "bar"}

        message = self.create_raw_message(publisher, body, "Elaine was here")
        consumer._receive_callback(message)

        self.assertEquals(callback1_scratchpad.get("message_data"), body,
                "callback1 was called")
        self.assertEquals(callback2_scratchpad.get("delivery_tag"),
                "Elaine was here")

        consumer.close()
        publisher.close()

    def create_raw_message(self, publisher, body, delivery_tag):
        raw_message = publisher.create_message(body)
        raw_message.delivery_tag = delivery_tag
        return raw_message

    def test_empty_queue_returns_None(self):
        consumer = self.create_consumer()
        consumer.discard_all()
        self.assertFalse(consumer.fetch())
        consumer.close()

    def test_custom_serialization_scheme(self):
        serialization.registry.register('custom_test',
                pickle.dumps, pickle.loads,
                content_type='application/x-custom-test',
                content_encoding='binary')

        consumer = self.create_consumer()
        publisher = self.create_publisher()
        consumer.discard_all()

        data = {"string": "The quick brown fox jumps over the lazy dog",
                "int": 10,
                "float": 3.14159265,
                "unicode": u"The quick brown fox jumps over the lazy dog",
                "advanced": AdvancedDataType("something"),
                "set": set(["george", "jerry", "elaine", "cosmo"]),
                "exception": Exception("There was an error"),
        }

        publisher.send(data, serializer='custom_test')
        message = fetch_next_message(consumer)
        backend = self.conn.create_backend()
        self.assertTrue(isinstance(message, backend.Message))
        self.assertEquals(message.payload.get("int"), 10)
        self.assertEquals(message.content_type, 'application/x-custom-test')
        self.assertEquals(message.content_encoding, 'binary')

        decoded_data = message.decode()

        self.assertEquals(decoded_data.get("string"),
                "The quick brown fox jumps over the lazy dog")
        self.assertEquals(decoded_data.get("int"), 10)
        self.assertEquals(decoded_data.get("float"), 3.14159265)
        self.assertEquals(decoded_data.get("unicode"),
                u"The quick brown fox jumps over the lazy dog")
        self.assertEquals(decoded_data.get("set"),
            set(["george", "jerry", "elaine", "cosmo"]))
        self.assertTrue(isinstance(decoded_data.get("exception"), Exception))
        self.assertEquals(decoded_data.get("exception").args[0],
            "There was an error")
        self.assertTrue(isinstance(decoded_data.get("advanced"),
            AdvancedDataType))
        self.assertEquals(decoded_data["advanced"].data, "something")

        consumer.close()
        publisher.close()

    def test_consumer_fetch(self):
        consumer = self.create_consumer()
        publisher = self.create_publisher()
        consumer.discard_all()

        data = {"string": "The quick brown fox jumps over the lazy dog",
                "int": 10,
                "float": 3.14159265,
                "unicode": u"The quick brown fox jumps over the lazy dog",
        }

        publisher.send(data)
        message = fetch_next_message(consumer)
        backend = self.conn.create_backend()
        self.assertTrue(isinstance(message, backend.Message))

        self.assertEquals(message.decode(), data)

        consumer.close()
        publisher.close()

    def test_consumer_process_next(self):
        consumer = self.create_consumer()
        publisher = self.create_publisher()
        consumer.discard_all()

        scratchpad = {}

        def callback(message_data, message):
            scratchpad["delivery_tag"] = message.delivery_tag
        consumer.register_callback(callback)

        publisher.send({"name_discovered": {
                            "first_name": "Cosmo",
                            "last_name": "Kramer"}})

        while True:
            message = consumer.fetch(enable_callbacks=True)
            if message:
                break

        self.assertEquals(scratchpad.get("delivery_tag"),
                message.delivery_tag)

        consumer.close()
        publisher.close()

    def test_consumer_discard_all(self):
        consumer = self.create_consumer()
        publisher = self.create_publisher()
        consumer.discard_all()

        for i in xrange(100):
            publisher.send({"foo": "bar"})
        time.sleep(0.5)

        self.assertEquals(consumer.discard_all(), 100)

        consumer.close()
        publisher.close()

    def test_iterqueue(self):
        consumer = self.create_consumer()
        publisher = self.create_publisher()
        num = consumer.discard_all()

        it = consumer.iterqueue(limit=100)
        consumer.register_callback(lambda *args: args)

        for i in xrange(100):
            publisher.send({"foo%d" % i: "bar%d" % i})
        time.sleep(0.5)

        for i in xrange(100):
            try:
                message = it.next()
                data = message.decode()
                self.assertTrue("foo%d" % i in data, "foo%d not in data" % i)
                self.assertEquals(data.get("foo%d" % i), "bar%d" % i)
            except StopIteration:
                self.assertTrue(False, "iterqueue fails StopIteration")

        self.assertRaises(StopIteration, it.next)

        # no messages on queue raises StopIteration if infinite=False
        it = consumer.iterqueue()
        self.assertRaises(StopIteration, it.next)

        it = consumer.iterqueue(infinite=True)
        self.assertTrue(it.next() is None,
                "returns None if no messages and inifite=True")

        consumer.close()
        publisher.close()

    def test_publisher_message_priority(self):
        consumer = self.create_consumer()
        publisher = self.create_publisher()
        consumer.discard_all()

        m = publisher.create_message("foo", priority=9)

        publisher.send({"foo": "bar"}, routing_key="nowhere", priority=9,
                mandatory=False, immediate=False)

        consumer.discard_all()

        consumer.close()
        publisher.close()

    def test_backend_survives_channel_close_regr17(self):
        """
        test that a backend instance is still functional after
        a method that results in a channel closure.
        """
        backend = self.create_publisher().backend
        assert not backend.queue_exists('notaqueue')
        # after calling this once, the channel seems to close, but the
        # backend may be holding a reference to it...
        assert not backend.queue_exists('notaqueue')

    def disabled_publisher_mandatory_flag_regr16(self):
        """
        Test that the publisher "mandatory" flag
        raises exceptions at appropriate times.
        """
        routing_key = 'black_hole'

        assert self.conn.connection is not None

        message = {'foo': 'mandatory'}

        # sanity check cleanup from last test
        assert not self.create_consumer().backend.queue_exists(routing_key)

        publisher = self.create_publisher()

        # this should just get discarded silently, it's not mandatory
        publisher.send(message, routing_key=routing_key, mandatory=False)

        # This raises an unspecified exception because there is no queue to
        # deliver to
        self.assertRaises(Exception, publisher.send, message,
                          routing_key=routing_key, mandatory=True)

        # now bind a queue to it
        consumer = Consumer(connection=self.conn,
                            queue=routing_key, exchange=self.exchange,
                            routing_key=routing_key, durable=False,
                            exclusive=True)

        # check that it exists
        assert self.create_consumer().backend.queue_exists(routing_key)

        # this should now get routed to our consumer with no exception
        publisher.send(message, routing_key=routing_key, mandatory=True)

    def test_consumer_auto_ack(self):
        consumer = self.create_consumer(auto_ack=True)
        publisher = self.create_publisher()
        consumer.discard_all()

        publisher.send({"foo": "Baz"})
        message = fetch_next_message(consumer)
        self.assertEquals(message._state, "ACK")
        consumer.close()
        publisher.close()

        publisher = self.create_publisher()
        consumer = self.create_consumer(auto_ack=False)
        publisher.send({"foo": "Baz"})
        message = fetch_next_message(consumer)
        self.assertEquals(message._state, "RECEIVED")

        consumer.close()
        publisher.close()

    def test_consumer_consume(self):
        consumer = self.create_consumer(auto_ack=True)
        publisher = self.create_publisher()
        consumer.discard_all()

        data = {"foo": "Baz"}
        publisher.send(data)
        try:
            data2 = {"company": "Vandelay Industries"}
            publisher.send(data2)
            scratchpad = {}

            def callback(message_data, message):
                scratchpad["data"] = message_data
            consumer.register_callback(callback)

            it = consumer.iterconsume()
            it.next()
            self.assertEquals(scratchpad.get("data"), data)
            it.next()
            self.assertEquals(scratchpad.get("data"), data2)

            # Cancel consumer/close and restart.
            consumer.close()
            consumer = self.create_consumer(auto_ack=True)
            consumer.register_callback(callback)
            consumer.discard_all()
            scratchpad = {}

            # Test limits
            it = consumer.iterconsume(limit=4)
            publisher.send(data)
            publisher.send(data2)
            publisher.send(data)
            publisher.send(data2)
            publisher.send(data)

            it.next()
            self.assertEquals(scratchpad.get("data"), data)
            it.next()
            self.assertEquals(scratchpad.get("data"), data2)
            it.next()
            self.assertEquals(scratchpad.get("data"), data)
            it.next()
            self.assertEquals(scratchpad.get("data"), data2)
            self.assertRaises(StopIteration, it.next)


        finally:
            consumer.close()
            publisher.close()

    def test_consumerset_iterconsume(self):
        consumerset = self.create_consumerset(queues={
            "bar": {
                "exchange": "foo",
                "exchange_type": "direct",
                "routing_key": "foo.bar",
            },
            "baz": {
                "exchange": "foo",
                "exchange_type": "direct",
                "routing_key": "foo.baz",
            },
            "bam": {
                "exchange": "foo",
                "exchange_type": "direct",
                "routing_key": "foo.bam",
            },
            "xuzzy": {
                "exchange": "foo",
                "exchange_type": "direct",
                "routing_key": "foo.xuzzy",
            }})
        publisher = self.create_publisher(exchange="foo")
        consumerset.discard_all()

        scratchpad = {}

        def callback(message_data, message):
            scratchpad["data"] = message_data

        def assertDataIs(what):
            self.assertEquals(scratchpad.get("data"), what)

        try:
            consumerset.register_callback(callback)
            it = consumerset.iterconsume()
            publisher.send({"rkey": "foo.xuzzy"}, routing_key="foo.xuzzy")
            it.next()
            assertDataIs({"rkey": "foo.xuzzy"})

            publisher.send({"rkey": "foo.xuzzy"}, routing_key="foo.xuzzy")
            publisher.send({"rkey": "foo.bar"}, routing_key="foo.bar")
            publisher.send({"rkey": "foo.baz"}, routing_key="foo.baz")
            publisher.send({"rkey": "foo.bam"}, routing_key="foo.bam")

            it.next()
            assertDataIs({"rkey": "foo.xuzzy"})
            it.next()
            assertDataIs({"rkey": "foo.bar"})
            it.next()
            assertDataIs({"rkey": "foo.baz"})
            it.next()
            assertDataIs({"rkey": "foo.bam"})

        finally:
            consumerset.close()
            publisher.close()
