"""
kombu.transport.pika
====================

Pika transport.

:copyright: (c) 2009 - 2012 by Ask Solem.
:license: BSD, see LICENSE for more details.

"""
from __future__ import absolute_import

import socket

from operator import attrgetter

from kombu.exceptions import StdChannelError

from . import base

import pika
from pika import spec
from pika.adapters import blocking_connection as blocking
from pika import exceptions

DEFAULT_PORT = 5672
BASIC_PROPERTIES = ("content_type", "content_encoding",
                    "headers", "delivery_mode", "priority",
                    "correlation_id", "reply_to", "expiration",
                    "message_id", "timestamp", "type", "user_id",
                    "app_id", "cluster_id")


class Message(base.Message):

    def __init__(self, channel, amqp_message, **kwargs):
        channel_id, method, props, body = amqp_message
        propdict = dict(zip(BASIC_PROPERTIES,
                        attrgetter(*BASIC_PROPERTIES)(props)))

        kwargs.update({"body": body,
                       "delivery_tag": method.delivery_tag,
                       "content_type": props.content_type,
                       "content_encoding": props.content_encoding,
                       "headers": props.headers,
                       "properties": propdict,
                       "delivery_info": dict(
                            consumer_tag=getattr(method, "consumer_tag", None),
                            routing_key=method.routing_key,
                            delivery_tag=method.delivery_tag,
                            redelivered=method.redelivered,
                            exchange=method.exchange)})

        super(Message, self).__init__(channel, **kwargs)


class Channel(blocking.BlockingChannel, base.StdChannel):
    Message = Message

    def basic_get(self, queue, no_ack):
        method = super(Channel, self).basic_get(self, queue=queue,
                                                      no_ack=no_ack)
        # pika returns semi-predicates (GetEmpty/GetOk).
        if isinstance(method, spec.Basic.GetEmpty):
            return
        return None, method, method._properties, method._body

    def queue_purge(self, queue=None, nowait=False):
        return super(Channel, self).queue_purge(queue=queue,
                                                nowait=nowait).message_count

    def basic_publish(self, message, exchange, routing_key, mandatory=False,
            immediate=False):
        body, properties = message
        try:
            return super(Channel, self).basic_publish(exchange,
                                                      routing_key,
                                                      body,
                                                      properties,
                                                      mandatory,
                                                      immediate)
        finally:
            # Pika does not automatically flush the outbound buffer
            # TODO async: Needs to support `nowait`.
            self.connection._flush_outbound()

    def basic_consume(self, queue, no_ack=False, consumer_tag=None,
            callback=None, nowait=False):

        # Kombu callbacks only take a single `message` argument,
        # but pika applies with 4 arguments, so need to wrap
        # these into a single tuple.
        def _callback_decode(channel, method, header, body):
            return callback((channel, method, header, body))

        return super(Channel, self).basic_consume(
                _callback_decode, queue, no_ack, False, consumer_tag)

    def prepare_message(self, body, priority=None,
            content_type=None, content_encoding=None, headers=None,
            properties=None):
        properties = spec.BasicProperties(priority=priority,
                                          content_type=content_type,
                                          content_encoding=content_encoding,
                                          headers=headers,
                                          **properties)
        return body, properties

    def message_to_python(self, raw_message):
        return self.Message(channel=self, amqp_message=raw_message)

    def basic_qos(self, prefetch_size, prefetch_count, a_global=False):
        return super(Channel, self).basic_qos(prefetch_size=prefetch_size,
                                              prefetch_count=prefetch_count,
                                              global_=a_global)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self, *args):
        super(Channel, self).close(*args)
        self.connection = None
        if getattr(self, "handler", None):
            if getattr(self.handler, "connection", None):
                self.handler.connection.channels.pop(
                        self.handler.channel_number, None)
                self.handler.connection = None
            self.handler = None

    @property
    def channel_id(self):
        return self.channel_number


class Connection(blocking.BlockingConnection):
    Channel = Channel

    def __init__(self, client, *args, **kwargs):
        self.client = client
        super(Connection, self).__init__(*args, **kwargs)

    def channel(self):
        self._channel_open = False
        cid = self._next_channel_number()

        self.callbacks.add(cid, spec.Channel.CloseOk, self._on_channel_close)
        transport = blocking.BlockingChannelTransport(self, cid)
        channel = self._channels[cid] = self.Channel(self, cid, transport)
        channel.connection = self
        return channel

    def drain_events(self, timeout=None):
        if timeout:
            prev = self.socket.gettimeout()
            self.socket.settimeout(timeout)
        try:
            self._handle_read()
        finally:
            if timeout:
                self.socket.settimeout(prev)
            self._flush_outbound()

    def close(self, *args):
        self.client = None
        super(Connection, self).close(*args)


AuthenticationError = getattr(exceptions, "AuthenticationError",
                              getattr(exceptions, "LoginError"))


class Transport(base.Transport):
    default_port = DEFAULT_PORT

    connection_errors = (socket.error,
                         exceptions.ConnectionClosed,
                         exceptions.ChannelClosed,
                         AuthenticationError,
                         exceptions.NoFreeChannels,
                         exceptions.DuplicateConsumerTag,
                         exceptions.UnknownConsumerTag,
                         exceptions.RecursiveOperationDetected,
                         exceptions.ProtocolSyntaxError)

    channel_errors = (StdChannelError,
                      exceptions.ChannelClosed,
                      exceptions.DuplicateConsumerTag,
                      exceptions.UnknownConsumerTag,
                      exceptions.ProtocolSyntaxError)

    Message = Message
    Connection = Connection

    def __init__(self, client, **kwargs):
        self.client = client
        self.default_port = kwargs.get("default_port", self.default_port)

    def create_channel(self, connection):
        return connection.channel()

    def drain_events(self, connection, **kwargs):
        return connection.drain_events(**kwargs)

    def establish_connection(self):
        """Establish connection to the AMQP broker."""
        conninfo = self.client
        for name, default_value in self.default_connection_params.items():
            if not getattr(conninfo, name, None):
                setattr(conninfo, name, default_value)
        credentials = pika.PlainCredentials(conninfo.userid,
                                            conninfo.password)
        return self.Connection(self.client,
                               pika.ConnectionParameters(
                                    conninfo.hostname, port=conninfo.port,
                                    virtual_host=conninfo.virtual_host,
                                    credentials=credentials))

    def close_connection(self, connection):
        """Close the AMQP broker connection."""
        connection.close()

    @property
    def default_connection_params(self):
        return {"hostname": "localhost", "port": self.default_port,
                "userid": "guest", "password": "guest"}
