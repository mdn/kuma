import os
import sys
import unittest
sys.path.insert(0, os.pardir)
sys.path.append(os.getcwd())

from tests.utils import establish_test_connection
from carrot.connection import BrokerConnection
from carrot.backends.pyamqplib import Message

README_QUEUE = "feed"
README_EXCHANGE = "feed"
README_ROUTING_KEY = "feed"


class TimeoutError(Exception):
    """The operation timed out."""


def receive_a_message(consumer):
    while True:
        message = consumer.fetch()
        if message:
            return message


def emulate_wait(consumer):
    message = receive_a_message(consumer)
    consumer._receive_callback(message)


class CallbacksTestable(object):
    last_feed = None
    last_status = None
    last_body = None
    last_delivery_tag = None

    def import_feed(self, message_data, message):
        feed_url = message_data.get("import_feed")
        self.last_feed = feed_url
        if not feed_url:
            self.last_status = "REJECT"
            message.reject()
        else:
            self.last_status = "ACK"
            message.ack()

    def dump_message(self, message_data, message):
        self.last_body = message.body
        self.last_delivery_tag = message.delivery_tag


def create_README_consumer(amqpconn):
    from carrot.messaging import Consumer
    consumer = Consumer(connection=amqpconn,
                        queue=README_QUEUE, exchange=README_EXCHANGE,
                        routing_key=README_ROUTING_KEY)
    tcallbacks = CallbacksTestable()
    consumer.register_callback(tcallbacks.import_feed)
    consumer.register_callback(tcallbacks.dump_message)
    return consumer, tcallbacks


def create_README_publisher(amqpconn):
    from carrot.messaging import Publisher
    publisher = Publisher(connection=amqpconn, exchange=README_EXCHANGE,
                          routing_key=README_ROUTING_KEY)
    return publisher


class TestExamples(unittest.TestCase):

    def setUp(self):
        self.conn = establish_test_connection()
        self.consumer, self.tcallbacks = create_README_consumer(self.conn)
        self.consumer.discard_all()

    def test_connection(self):
        self.assertTrue(self.conn)
        self.assertTrue(self.conn.connection.channel())

    def test_README_consumer(self):
        consumer = self.consumer
        tcallbacks = self.tcallbacks
        self.assertTrue(consumer.connection)
        self.assertTrue(isinstance(consumer.connection, BrokerConnection))
        self.assertEquals(consumer.queue, README_QUEUE)
        self.assertEquals(consumer.exchange, README_EXCHANGE)
        self.assertEquals(consumer.routing_key, README_ROUTING_KEY)
        self.assertTrue(len(consumer.callbacks), 2)

    def test_README_publisher(self):
        publisher = create_README_publisher(self.conn)
        self.assertTrue(publisher.connection)
        self.assertTrue(isinstance(publisher.connection, BrokerConnection))
        self.assertEquals(publisher.exchange, README_EXCHANGE)
        self.assertEquals(publisher.routing_key, README_ROUTING_KEY)

    def test_README_together(self):
        consumer = self.consumer
        tcallbacks = self.tcallbacks

        publisher = create_README_publisher(self.conn)
        feed_url = "http://cnn.com/rss/edition.rss"
        body = {"import_feed": feed_url}
        publisher.send(body)
        publisher.close()
        emulate_wait(consumer)

        self.assertEquals(tcallbacks.last_feed, feed_url)
        self.assertTrue(tcallbacks.last_delivery_tag)
        self.assertEquals(tcallbacks.last_status, "ACK")

        publisher = create_README_publisher(self.conn)
        body = {"foo": "FOO"}
        publisher.send(body)
        publisher.close()
        emulate_wait(consumer)

        self.assertFalse(tcallbacks.last_feed)
        self.assertTrue(tcallbacks.last_delivery_tag)
        self.assertEquals(tcallbacks.last_status, "REJECT")

    def test_subclassing(self):
        from carrot.messaging import Consumer, Publisher
        feed_url = "http://cnn.com/rss/edition.rss"
        testself = self

        class TConsumer(Consumer):
            queue = README_QUEUE
            exchange = README_EXCHANGE
            routing_key = README_ROUTING_KEY

            def receive(self, message_data, message):
                testself.assertTrue(isinstance(message, Message))
                testself.assertTrue("import_feed" in message_data)
                testself.assertEquals(message_data.get("import_feed"),
                        feed_url)

        class TPublisher(Publisher):
            exchange = README_EXCHANGE
            routing_key = README_ROUTING_KEY

        consumer = TConsumer(connection=self.conn)
        publisher = TPublisher(connection=self.conn)

        consumer.discard_all()
        publisher.send({"import_feed": feed_url})
        publisher.close()
        emulate_wait(consumer)

        consumer.close()


if __name__ == '__main__':
    unittest.main()
