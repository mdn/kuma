"""

`amqplib`_ backend for carrot.

.. _`amqplib`: http://barryp.org/software/py-amqplib/

"""
import pylibrabbitmq as amqp
from pylibrabbitmq import ChannelError, ConnectionError
from carrot.backends.base import BaseMessage, BaseBackend
from itertools import count
import warnings
import weakref

DEFAULT_PORT = 5672


class Message(BaseMessage):
    """A message received by the broker.

    Usually you don't insantiate message objects yourself, but receive
    them using a :class:`carrot.messaging.Consumer`.

    :param backend: see :attr:`backend`.
    :param amqp_message: see :attr:`_amqp_message`.


    .. attribute:: body

        The message body.

    .. attribute:: delivery_tag

        The message delivery tag, uniquely identifying this message.

    .. attribute:: backend

        The message backend used.
        A subclass of :class:`carrot.backends.base.BaseBackend`.

    .. attribute:: _amqp_message

        A :class:`amqplib.client_0_8.basic_message.Message` instance.
        This is a private attribute and should not be accessed by
        production code.

    """

    def __init__(self, backend, amqp_message, **kwargs):
        self._amqp_message = amqp_message
        self.backend = backend
        kwargs["body"] = amqp_message.body
        properties = amqp_message.properties
        kwargs["content_type"] = properties["content_type"]
        kwargs["content_encoding"] = properties["content_encoding"]
        kwargs["delivery_info"] = amqp_message.delivery_info
        kwargs["delivery_tag"] = amqp_message.delivery_info["delivery_tag"]

        super(Message, self).__init__(backend, **kwargs)


class Backend(BaseBackend):
    """amqplib backend

    :param connection: see :attr:`connection`.


    .. attribute:: connection

    A :class:`carrot.connection.BrokerConnection` instance. An established
    connection to the broker.

    """
    default_port = DEFAULT_PORT

    Message = Message

    def __init__(self, connection, **kwargs):
        self.connection = connection
        self.default_port = kwargs.get("default_port", self.default_port)
        self._channel_ref = None

    @property
    def _channel(self):
        return callable(self._channel_ref) and self._channel_ref()

    @property
    def channel(self):
        """If no channel exists, a new one is requested."""
        if not self._channel:
            self._channel_ref = weakref.ref(self.connection.get_channel())
        return self._channel

    def establish_connection(self):
        """Establish connection to the AMQP broker."""
        conninfo = self.connection
        if not conninfo.hostname:
            raise KeyError("Missing hostname for AMQP connection.")
        if conninfo.userid is None:
            raise KeyError("Missing user id for AMQP connection.")
        if conninfo.password is None:
            raise KeyError("Missing password for AMQP connection.")
        if not conninfo.port:
            conninfo.port = self.default_port
        conn = amqp.Connection(host=conninfo.hostname,
                               port=conninfo.port,
                               userid=conninfo.userid,
                               password=conninfo.password,
                               virtual_host=conninfo.virtual_host)
        return conn

    def close_connection(self, connection):
        """Close the AMQP broker connection."""
        connection.close()

    def queue_exists(self, queue):
        return True

    def queue_delete(self, queue, if_unused=False, if_empty=False):
        """Delete queue by name."""
        pass

    def queue_purge(self, queue, **kwargs):
        """Discard all messages in the queue. This will delete the messages
        and results in an empty queue."""
        return self.channel.queue_purge(queue=queue)

    def queue_declare(self, queue, durable, exclusive, auto_delete,
            warn_if_exists=False):
        """Declare a named queue."""
        return self.channel.queue_declare(queue=queue,
                                          durable=durable,
                                          exclusive=exclusive,
                                          auto_delete=auto_delete)

    def exchange_declare(self, exchange, type, durable, auto_delete):
        """Declare an named exchange."""
        return self.channel.exchange_declare(exchange=exchange,
                                             type=type,
                                             durable=durable,
                                             auto_delete=auto_delete)

    def queue_bind(self, queue, exchange, routing_key, arguments=None):
        """Bind queue to an exchange using a routing key."""
        return self.channel.queue_bind(queue=queue,
                                       exchange=exchange,
                                       routing_key=routing_key,
                                       arguments=arguments)

    def message_to_python(self, raw_message):
        """Convert encoded message body back to a Python value."""
        return self.Message(backend=self, amqp_message=raw_message)

    def get(self, queue, no_ack=False):
        """Receive a message from a declared queue by name.

        :returns: A :class:`Message` object if a message was received,
            ``None`` otherwise. If ``None`` was returned, it probably means
            there was no messages waiting on the queue.

        """
        raw_message = self.channel.basic_get(queue, no_ack=no_ack)
        if not raw_message:
            return None
        return self.message_to_python(raw_message)

    def declare_consumer(self, queue, no_ack, callback, consumer_tag,
            nowait=False):
        """Declare a consumer."""
        return self.channel.basic_consume(queue=queue,
                                          no_ack=no_ack,
                                          callback=callback,
                                          consumer_tag=consumer_tag)

    def consume(self, limit=None):
        """Returns an iterator that waits for one message at a time."""
        for total_message_count in count():
            if limit and total_message_count >= limit:
                raise StopIteration

            if not self.channel.is_open:
                raise StopIteration

            self.channel.conn.drain_events()
            yield True

    def cancel(self, consumer_tag):
        """Cancel a channel by consumer tag."""
        if not self.channel.conn:
            return
        self.channel.basic_cancel(consumer_tag)

    def close(self):
        """Close the channel if open."""
        if self._channel and self._channel.is_open:
            self._channel.close()
        self._channel_ref = None

    def ack(self, delivery_tag):
        """Acknowledge a message by delivery tag."""
        return self.channel.basic_ack(delivery_tag)

    def reject(self, delivery_tag):
        """Reject a message by deliver tag."""
        return self.channel.basic_reject(delivery_tag, requeue=False)

    def requeue(self, delivery_tag):
        """Reject and requeue a message by delivery tag."""
        return self.channel.basic_reject(delivery_tag, requeue=True)

    def prepare_message(self, message_data, delivery_mode, priority=None,
                content_type=None, content_encoding=None):
        """Encapsulate data into a AMQP message."""
        return amqp.Message(message_data, properties={
                "delivery_mode": delivery_mode,
                "priority": priority,
                "content_type": content_type,
                "content_encoding": content_encoding})

    def publish(self, message, exchange, routing_key, mandatory=None,
            immediate=None, headers=None):
        """Publish a message to a named exchange."""

        if headers:
            message.properties["headers"] = headers

        ret = self.channel.basic_publish(message, exchange=exchange,
                                         routing_key=routing_key,
                                         mandatory=mandatory,
                                         immediate=immediate)
        if mandatory or immediate:
            self.close()

    def qos(self, prefetch_size, prefetch_count, apply_global=False):
        """Request specific Quality of Service."""
        pass
        #self.channel.basic_qos(prefetch_size, prefetch_count,
        #                        apply_global)

    def flow(self, active):
        """Enable/disable flow from peer."""
        pass
        #self.channel.flow(active)
