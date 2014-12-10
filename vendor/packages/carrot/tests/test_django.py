import os
import sys
import unittest
import pickle
import time
sys.path.insert(0, os.pardir)
sys.path.append(os.getcwd())

from tests.utils import BROKER_HOST, BROKER_PORT, BROKER_VHOST, \
                        BROKER_USER, BROKER_PASSWORD
from carrot.connection import DjangoBrokerConnection, BrokerConnection
from UserDict import UserDict

CARROT_BACKEND = "amqp"


class DictWrapper(UserDict):

    def __init__(self, data):
        self.data = data

    def __getattr__(self, key):
        try:
            return self.data[key]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, key))


def configured_or_configure(settings, **conf):
    if settings.configured:
        for conf_name, conf_value in conf.items():
            setattr(settings, conf_name, conf_value)
    else:
        settings.configure(default_settings=DictWrapper(conf))


class TestDjangoSpecific(unittest.TestCase):

    def test_DjangoBrokerConnection(self):
        try:
            from django.conf import settings
        except ImportError:
            sys.stderr.write(
                "Django is not installed. \
                Not testing django specific features.\n")
            return
        configured_or_configure(settings,
                CARROT_BACKEND=CARROT_BACKEND,
                BROKER_HOST=BROKER_HOST,
                BROKER_PORT=BROKER_PORT,
                BROKER_VHOST=BROKER_VHOST,
                BROKER_USER=BROKER_USER,
                BROKER_PASSWORD=BROKER_PASSWORD)

        expected_values = {
            "backend_cls": CARROT_BACKEND,
            "hostname": BROKER_HOST,
            "port": BROKER_PORT,
            "virtual_host": BROKER_VHOST,
            "userid": BROKER_USER,
            "password": BROKER_PASSWORD}

        conn = DjangoBrokerConnection()
        self.assertTrue(isinstance(conn, BrokerConnection))

        for val_name, val_value in expected_values.items():
            self.assertEquals(getattr(conn, val_name, None), val_value)


if __name__ == '__main__':
    unittest.main()
