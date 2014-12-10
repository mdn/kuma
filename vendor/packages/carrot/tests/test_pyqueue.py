import os
import sys
import unittest
import uuid
sys.path.insert(0, os.pardir)
sys.path.append(os.getcwd())

from carrot.backends.queue import Message as PyQueueMessage
from carrot.backends.queue import Backend as PyQueueBackend
from carrot.connection import BrokerConnection
from carrot.messaging import Messaging, Consumer, Publisher


def create_backend():
    return PyQueueBackend(connection=BrokerConnection())


class TestPyQueueMessage(unittest.TestCase):

    def test_message(self):
        b = create_backend()
        self.assertTrue(b)

        message_body = "George Constanza"
        delivery_tag = str(uuid.uuid4())

        m1 = PyQueueMessage(backend=b,
                            body=message_body,
                            delivery_tag=delivery_tag)
        m2 = PyQueueMessage(backend=b,
                            body=message_body,
                            delivery_tag=delivery_tag)
        m3 = PyQueueMessage(backend=b,
                            body=message_body,
                            delivery_tag=delivery_tag)
        self.assertEquals(m1.body, message_body)
        self.assertEquals(m1.delivery_tag, delivery_tag)

        m1.ack()
        m2.reject()
        m3.requeue()


class TestPyQueueBackend(unittest.TestCase):

    def test_backend(self):
        b = create_backend()
        message_body = "Vandelay Industries"
        b.publish(b.prepare_message(message_body, "direct",
                                    content_type='text/plain',
                                    content_encoding="ascii"),
                  exchange="test",
                  routing_key="test")
        m_in_q = b.get()
        self.assertTrue(isinstance(m_in_q, PyQueueMessage))
        self.assertEquals(m_in_q.body, message_body)
    
    def test_consumer_interface(self):
        to_send = ['No', 'soup', 'for', 'you!']
        messages = []
        def cb(message_data, message):
            messages.append(message_data)
        conn = BrokerConnection(backend_cls='memory')
        consumer = Consumer(connection=conn, queue="test",
                            exchange="test", routing_key="test")
        consumer.register_callback(cb)
        publisher = Publisher(connection=conn, exchange="test",
                              routing_key="test")
        for i in to_send:
            publisher.send(i)
        it = consumer.iterconsume()
        for i in range(len(to_send)):
            it.next()
        self.assertEqual(messages, to_send)


class TMessaging(Messaging):
    exchange = "test"
    routing_key = "test"
    queue = "test"


class TestMessaging(unittest.TestCase):

    def test_messaging(self):
        m = TMessaging(connection=BrokerConnection(backend_cls=PyQueueBackend))
        self.assertTrue(m)

        self.assertEquals(m.fetch(), None)
        mdata = {"name": "Cosmo Kramer"}
        m.send(mdata)
        next_msg = m.fetch()
        next_msg_data = next_msg.decode()
        self.assertEquals(next_msg_data, mdata)
        self.assertEquals(m.fetch(), None)


if __name__ == '__main__':
    unittest.main()
