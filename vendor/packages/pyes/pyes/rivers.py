#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'

import logging

try:
    # For Python >= 2.6
    import json
except ImportError:
    # For Python < 2.6 or people using a newer version of simplejson
    import simplejson as json

from es import ESJsonEncoder

log = logging.getLogger('pyes')

class River(object):
    def __init__(self, index_name=None, index_type=None, bulk_size=100, bulk_timeout=None):
        self.name = index_name
        self.index_name = index_name
        self.index_type = index_type
        self.bulk_size = bulk_size
        self.bulk_timeout = bulk_timeout

    @property
    def q(self):
        res = self.serialize()
        index = {}
        if self.name:
            index['name'] = self.name
        if self.index_name:
            index['index'] = self.index_name
        if self.index_type:
            index['type'] = self.index_type
        if self.bulk_size:
            index['bulk_size'] = self.bulk_size
        if self.bulk_timeout:
            index['bulk_timeout'] = self.bulk_timeout
        if index:
            res['index'] = index
        return res

    def __repr__(self):
        return str(self.q)

    def to_json(self):
        return json.dumps(self.q, cls=ESJsonEncoder)

class RabbitMQRiver(River):
    type = "rabbitmq"

    def __init__(self, host="localhost", port=5672, user="guest",
                 password="guest", vhost="/", queue="es", exchange="es",
                 routing_key="es", **kwargs):
        super(RabbitMQRiver, self).__init__(**kwargs)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key

    def serialize(self):
        return {
                "type" : self.type,
                self.type : {
                    "host" : self.host,
                    "port" : self.port,
                    "user" : self.user,
                    "pass" : self.password,
                    "vhost" : self.vhost,
                    "queue" : self.queue,
                    "exchange" : self.exchange,
                    "routing_key" : self.routing_key
                }
            }


class TwitterRiver(River):
    type = "twitter"

    def __init__(self, user, password, **kwargs):
        super(TwitterRiver, self).__init__(**kwargs)
        self.user = user
        self.password = password


    def serialize(self):
        return {
                "type" : self.type,
                self.type : {
                    "user" : self.user,
                    "password" : self.password,
                }
            }

class CouchDBRiver(River):
    type = "couchdb"

    def __init__(self, host="localhost", port=5984, db="mydb", filter=None, **kwargs):
        super(CouchDBRiver, self).__init__(**kwargs)
        self.host = host
        self.port = port
        self.db = db
        self.filter = filter

    def serialize(self):
        return {
                "type" : self.type,
                self.type : {
                    "host" : self.host,
                    "port" : self.port,
                    "db" : self.db,
                    "filter" : self.filter,
                }
            }
