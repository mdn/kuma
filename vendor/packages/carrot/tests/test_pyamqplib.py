import os
import sys
import unittest
import pickle
import time
sys.path.insert(0, os.pardir)
sys.path.append(os.getcwd())

from tests.utils import establish_test_connection
from carrot.connection import BrokerConnection
from carrot.messaging import Consumer, Publisher, ConsumerSet
from carrot.backends.pyamqplib import Backend as AMQPLibBackend
from carrot.backends.pyamqplib import Message as AMQPLibMessage
from carrot import serialization
from tests.backend import BackendMessagingCase

TEST_QUEUE = "carrot.unittest"
TEST_EXCHANGE = "carrot.unittest"
TEST_ROUTING_KEY = "carrot.unittest"

TEST_QUEUE_TWO = "carrot.unittest.two"
TEST_EXCHANGE_TWO = "carrot.unittest.two"
TEST_ROUTING_KEY_TWO = "carrot.unittest.two"

TEST_CELERY_QUEUE = {
            TEST_QUEUE: {
                "exchange": TEST_EXCHANGE,
                "exchange_type": "direct",
                "routing_key": TEST_ROUTING_KEY,
            },
            TEST_QUEUE_TWO: {
                "exchange": TEST_EXCHANGE_TWO,
                "exchange_type": "direct",
                "routing_key": TEST_ROUTING_KEY_TWO,
            },
        }


class TestAMQPlibMessaging(BackendMessagingCase):

    def setUp(self):
        self.conn = establish_test_connection()
        self.queue = TEST_QUEUE
        self.exchange = TEST_EXCHANGE
        self.routing_key = TEST_ROUTING_KEY
BackendMessagingCase = None

if __name__ == '__main__':
    unittest.main()
