import os

from carrot.connection import BrokerConnection


BROKER_HOST = os.environ.get('BROKER_HOST', "localhost")
BROKER_PORT = os.environ.get('BROKER_PORT', 5672)
BROKER_VHOST = os.environ.get('BROKER_VHOST', "/")
BROKER_USER = os.environ.get('BROKER_USER', "guest")
BROKER_PASSWORD = os.environ.get('BROKER_PASSWORD', "guest")

STOMP_HOST = os.environ.get('STOMP_HOST', 'localhost')
STOMP_PORT = os.environ.get('STOMP_PORT', 61613)
STOMP_QUEUE = os.environ.get('STOMP_QUEUE', '/queue/testcarrot')


def test_connection_args():
    return {"hostname": BROKER_HOST, "port": BROKER_PORT,
            "virtual_host": BROKER_VHOST, "userid": BROKER_USER,
            "password": BROKER_PASSWORD}


def test_stomp_connection_args():
    return {"hostname": STOMP_HOST, "port": STOMP_PORT}


def establish_test_connection():
    return BrokerConnection(**test_connection_args())
