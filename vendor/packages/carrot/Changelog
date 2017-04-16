================
 Change history
================

0.10.7 [2010-10-07 03:20 P.M CEST]
----------------------------------

* ``ConsumerSet``: Now possible to add/cancel consumers at runtime

    * To add another consumer to an active set do::

        >>> cset.add_consumer(C)
        >>> # or
        >>> cset.add_consumer_from_dict(**declaration)

        >>> # ...
        >>> # consume() will declare new consumers
        >>> cset.consume()

    * To cancel an active consumer by queue name do::

        >>> cset.cancel_by_queue(queue_name)

0.10.6 [2010-09-03 10:16 A.M CEST]
----------------------------------

* ``Publisher.send``: Now supports an exchange argument used to override the
  exchange to send the message to (defaults to ``Publisher.exchange``).

    Note that this exchange must have been declared.

* STOMP backend: Now supports username and password authentication.

* pika backend called basic_get with incorrect arguments.

0.10.5 [2010-06-03 09:02 A.M CEST]
----------------------------------

* In-memory backend: discard_all() now works correctly.

* Added msgpack serialization support

    See http://msgpack.sourceforge.net for more information.

    To enable set::

        serializer="msgpack"

* Added dependency specification for building RPMs.

    $ python setup.py bdist_rpm

0.10.4 [2010-05-14 10:26 A.M CEST]
----------------------------------

* Added ``BrokerConnection.drain_events()`` (only works for amqplib/pika)

  `drain_events` waits for events on all active channels.

* amqplib: Added timeout support to ``drain_events``.

	Example usage:

		>>> c = Consumer()
		>>> it = c.iterconsume()
		>>> # wait for event on any channel
		>>> try:
		...    connection.drain_events(timeout=1)
		...	except socket.timeout:
				pass

* Added Consumer.consume / ConsumerSet.consume

  We're slowly moving away from ``iterconsume`` as this flow doesn't
  make sense. You often want to consume from several channels at once,
  so ``iterconsume`` will probably be deprecated at some point.

  "new-style" consume example::

    >>> connection = BrokerConnection(..)
    >>> consumer = Consumer(connection, ...)
    >>> consumer.register_callback(handle_message)
    >>> consumer.consume() # declares consumers
    >>> while True:
    ...     connection.drain_events()
    >>> consumer.cancel() # Cancel consumer.

  More elaborate example consuming from two channels,
  where the first channel consumes from multiple queues::

    >>> connection = BrokerConnection(..)

    # The first channel receives jobs from several
    # queues.
    >>> queues = {"video": {"exchange": "jobs",
    ...                     "queue": "video",
    ...                     "routing_key": "video"},
    ...           "image": {"exchange": "jobs",
    ...                     "queue": "image",
    ...                     "routing_key": "image"}}
    >>> job_consumer = ConsumerSet(connection, from_dict=queues)
    >>> job_consumer.register_callback(handle_job)
    >>> job_consumer.consume()

    # The second channel receives remote control commands.
    >>> remote_consumer = Consumer(connection, queue="control",
    ...                            exchange="control")
    >>> remote_consumer.register_callback(handle_remote_command)
    >>> remote_consumer.consume()

    # The eventloop.
    # Receives a single message a pass and calls the appropriate
    # callback.
    >>> try:
    ...     while True:
    ...         connection.drain_events()
    ... finally:
    ...     job_consumer.close()
    ...     remote_consumer.close()
    ...     connection.close()

* amqplib: now raises ``KeyError`` if hostname isn't set.

0.10.3 [2010-03-08 05:01 P.M CEST]
----------------------------------

* Consumer/Publisher: A kwarg option set to ``None`` should always
  mean "use the class default value". This was not always the case,
  but has been fixed in this release.

* DjangoBrokerConnection: Now accepts a custom ``settings`` object. E.g.:

		>>> conn = DjangoBrokerConnection(settings=mysettings)

* Consumer.iterconsume: Now raises :exc:`StopIteration` if the channel is
  closed. (http://github.com/ask/carrot/issues/issue/24)

* Fixed syntax error in the DjangoBrokerConnection which could be triggered
  if some conditions were met.

* setup.cfg: Disable --enable-coverage from nosetests section

* Consumer.iterconsume now works properly when using the Python Queue
  module based backend (http://github.com/ask/carrot/issues/issue/23).


0.10.2 [2010-02-03 11:43 A.M CEST]
----------------------------------
* Resolved a typo in the experimental Pika backend.

0.10.1 [2010-01-16 10:17 P.M CEST]
----------------------------------

* Fixed syntax error typo in the Pika backend.

0.10.0 [2010-01-15 12:08 A.M CEST]
----------------------------------

* Added experimental Pika backend for async support. See
  http://github.com/tonyg/pika

* Python 2.4 compatibility.

* Added intent revealing names for use with the delivery_mode attribute

* The amqplib internal connection now supports waiting for events on any
  channel, so as to not block the event loop on a single channel. Example:

		>>> from carrot.connection import BrokerConnection
		>>> from carrot.messaging import Consumer, Publisher
		>>> from functools import partial
		>>> connection = BrokerConnection(...)
		>>> consumer1 = Consumer(queue="foo", exchange="foo")
		>>> consumer2 = Consumer(queue="bar", exchange="bar")
		>>> def callback(channel, message_data, message):
		...     print(%s: %s" % (channel, message_data))
		>>> consumer1.register_callback(partial(callback, "channel1"))
		>>> consumer2.register_callback(partial(callback, "channel2"))

		>>> pub1 = Publisher(exchange="foo")
		>>> pub2 = Publisher(exchange="bar")
		>>> [(i % 2 and pub1 or pub2).send({"hello": "world"})
		...		for i in range(100)]

		>>> while True:
		... 	connection.connection.drain_events()

	But please be sure to note that this is an internal feature only,
	hopefully we will have a public interface for this for v1.0.

0.8.0 [2009-11-16 05:11 P.M CEST]
---------------------------------

**BACKWARD INCOMPATIBLE CHANGES**

* Django: ``AMQP_SERVER`` has been deprecated and renamed to ``BROKER_HOST``.
  ``AMQP_SERVER`` is still supported but will be removed in version 1.0.

* Django: All ``AMQP_*`` settings has been renamed to ``BROKER_*``,
  the old settings still work but gives a deprecation warning.
  ``AMQP_*`` is scheduled for removal in v1.0.

* You now have to include the class name in the
  CARROT_BACKEND string. E.g. where you before had "my.module.backends", you now
  need to include the class name: ``"my.module.backends.BackendClass"``.
  The aliases works like before.

*BUGFIXES*

* Cancel should delete the affected _consumer

* qos()/flow() now working properly.

* Fixed the bug in UUID4 which makes it return the same id over and over.

*OTHER*

* Sphinx docs: Remove django dependency when building docs. Thanks jetfar!

* You can now build the documentatin using ``python setup.py build_sphinx``
  (thanks jetfar!)



0.6.1 [2009-09-30 12:29 P.M CET]
------------------------------------------------------------------

* Forgot to implement qos/flow in the pyamqplib backend (doh).
	Big thanks to stevvooe! See issue `#18`_

* Renamed ConsumerSet._open_channels -> _open_consumers

* Channel is now a weak reference so it's collected on channel exception.
	See issue `#17`_. Thanks to ltucker.

* Publisher.auto_declare/Consumer.auto_declare: Can now disable the default
  behaviour of automatically declaring the queue, exchange and queue binding.

* Need to close the connection to receive mandatory/immediate errors
	(related to issue `#16`_). Thanks to ltucker.

* pyamqplib backend close didn't work properly, typo channel -> _channel

* Adds carrot.backends.pystomp to the reference documentation.

.. _`#18`: http://github.com/ask/carrot/issues#issue/18
.. _`#17`: http://github.com/ask/carrot/issues#issue/17
.. _`#16`: http://github.com/ask/carrot/issues#issue/16


0.6.0 [2009-09-17 16:41 P.M CET]
------------------------------------------------------------------

**BACKWARD INCOMPATIBLE CHANGES**

* AMQPConnection renamed to BrokerConnection with AMQPConnection remaining
	an alias for backwards compatability. Similarly DjangoAMQPConnection is
	renamed to DjangoBrokerConnection.

* AMQPConnection renamed to BrokerConnection
	DjangoAMQPConnection renamed to DjangoBrokerConnection
	(The previous names are still available but will be deprecated in 1.0)

* The connection is now lazy, requested only when it's needed.
	To explicitly connect you have to evaluate the BrokerConnections
	``connection`` attribute.

		>>> connection = BrokerConnection(...) # Not connected yet.
		>>> connection.connection; # Now it's connected

* A channel is now lazy, requested only when it's needed.

* pyamqplib.Message.amqp_message is now a private attribute

**NEW FEATURES**

* Basic support for STOMP using the stompy library.
	(Available at http://bitbucket.org/benjaminws/python-stomp/overview/)

* Implements :meth:`Consumer.qos` and :meth:`Consumer.flow` for setting
	quality of service and flow control.

**NEWS**

* The current Message class is now available as an attribute on the
	Backend.

* Default port is now handled by the backend and all AMQP_* settings to the
	DjangoBrokerConnection is now optional

* Backend is now initialized in the connection instead of Consumer/Publisher,
	so backend_cls now has to be sent to AMQPConnection if you want to
	explicitly set it.

* Specifying utf-8 as the content type when forcing unicode into a string.
	This removes the reference to the unbound content_type variable.


0.5.1 [2009-07-19 06:19 P.M CET]
------------------------------------------------------------------

	* Handle messages without content_encoding attribute set.

	* Make delivery_info available on the Message instance.

	* Use anyjson to detect best installed JSON module on the system.

0.5.0 [2009-06-25 08:16 P.M CET]
------------------------------------------------------------------

**BACKWARD-INCOMPATIBLE CHANGES**

	* Custom encoder/decoder support has been moved to a centralized 
		registry in ``carrot.serialization``. This means the 
		``encoder``/``decoder`` optional arguments to ``Publisher.send`` 
		`(and the similar attributes of  ``Publisher`` and ``Consumer`` 
		classes) no longer exist.   See ``README`` for details of the new 
		system.

	* Any ``Consumer`` and ``Publisher`` instances should be 
		upgraded at the same time since carrot now uses the AMQP
		``content-type`` field to know how to automatically de-serialize
		your data. If you use an old-style ``Publisher`` with a new-style
		``Consumer``, you will get a raw string back as ``message_data`` 
		instead of your de-serialized data. An old-style ``Consumer``
		will work with a new-style ``Publisher`` as long as you're using
		the default ``JSON`` serialization methods. 

	* Acknowledging/Rejecting/Requeuing a message twice now raises
		an exception.

*ENHANCEMENTS*

	* ``ConsumerSet``: Receive messages from several consumers.


0.4.5 [2009-06-15 01:58 P.M CET] 
------------------------------------------------------------------

**BACKWARD-INCOMPATIBLE CHANGES**

	* the exchange is now also declared in the ``Publisher``. This means
		the following attributes (if used) must be set on *both*
		the ``Publisher`` and the ``Consumer``:
		``exchange_type``, ``durable`` and ``auto_delete``.

**IMPORTANT BUGS**

	* No_ack was always set to ``True`` when using ``Consumer.iterconsume``.


0.4.4 [2009-06-15 01:58 P.M CET] 
------------------------------------------------------------------

	* __init__.pyc was included in the distribution by error.

0.4.3 [2009-06-13 09:26 P.M CET] 
------------------------------------------------------------------

	* Fix typo with long_description in ``setup.py``.

0.4.2 [2009-06-13 08:30 P.M CET] 
------------------------------------------------------------------

	* Make sure README exists before reading it for ``long_description``.
		Thanks to jcater.

	* ``discard_all``: Use ``AMQP.queue_purge`` if ``filterfunc`` is not
		specified

0.4.1 [2009-06-08 04:21 P.M CET] 
------------------------------------------------------------------

* Consumer/Publisher now correctly sets the encoder/decoder if they
	have been overriden by setting the class attribute.

0.4.0 [2009-06-06 01:39 P.M CET] 
------------------------------------------------------------------

**IMPORTANT** Please don't use ``Consumer.wait`` in production. Use either
of ``Consumer.iterconsume`` or ``Consumer.iterqueue``.

**IMPORTANT** The ``ack`` argument to ``Consumer.process_next`` has been
removed, use the instance-wide ``auto_ack`` argument/attribute instead.

**IMPORTANT** ``Consumer.message_to_python`` has been removed, use
``message.decode()`` on the returned message object instead.

**IMPORTANT** Consumer/Publisher/Messaging now no longer takes a backend
instance, but a backend class, so the ``backend`` argument is renamed to
``backend_cls``.

*WARNING* ``Consumer.process_next`` has been deprecated in favor of
``Consumer.fetch(enable_callbacks=True)`` and emits a ``DeprecationWarning``
if used.

	* ``Consumer.iterconsume``: New sane way to use basic_consume instead of ``Consumer.wait``:
		(Consmer.wait now uses this behind the scenes, just wrapped around
		a highly unsafe infinite loop.)

	* Consumer: New options: ``auto_ack`` and ``no_ack``. Auto ack means the
		consumer will automatically acknowledge new messages, and No-Ack
		means it will disable acknowledgement on the server alltogether
		(probably not what you want) 

	* ``Consumer.iterqueue``: Now supports infinite argument, which means the
		iterator doesn't raise ``StopIteration`` if there's no messages,
		but instead yields ``None`` (thus never ends)

	* message argument to consumer callbacks is now a
		``carrot.backends.pyamqplib.Message`` instance. See `[GH #4]`_.
		Thanks gregoirecachet!

.. _`[GH #4]`: http://github.com/ask/carrot/issues/closed/#issue/4
 
	* AMQPConnection, Consumer, Publisher and Messaging now supports
		the with statement. They automatically close when the with-statement
		block exists.

	* Consumer tags are now automatically generated for each class instance,
		so you should never get the "consumer tag already open" error anymore.

	* Loads of new unit tests.

0.4.0-pre7 [2009-06-03 05:08 P.M CET] 
------------------------------------------------------------------

	* Conform to pep8.py trying to raise our pypants score.

	* Documentation cleanup (thanks Rune Halvorsen)

0.4.0-pre6 [2009-06-03 04:55 P.M CET] 
------------------------------------------------------------------

	* exclusive implies auto_delete, not durable. Closes #2.
		Thanks gregoirecachet

	* Consumer tags are now automatically generated by the class module,
		name and a UUID.

	* New attribute ``Consumer.warn_if_exists:``
		If True, emits a warning if the queue has already been declared.
		If a queue already exists, and you try to redeclare the queue
		with new settings, the new settings will be silently ignored,
		so this can be useful if you've recently changed the
		`routing_key` attribute or other settings.

0.4.0-pre3 [2009-05-29 02:27 P.M CET] 
------------------------------------------------------------------

	* Publisher.send: Now supports message priorities (a number between ``0``
		and ``9``)

	* Publihser.send: Added ``routing_key`` keyword argument. Can override
		the routing key for a single message.

	* Publisher.send: Support for the ``immediate`` and ``mandatory`` flags.

0.4.0-pre2 [2009-05-29 02:27 P.M CET] 
------------------------------------------------------------------

	* AMQPConnection: Added ``connect_timeout`` timeout option, which is
		the timeout in seconds before we exhaust trying to establish a
		connection to the AMQP server.

0.4.0-pre1 [2009-05-27 04:27 P.M CET] 
------------------------------------------------------------------

	* This version introduces backends. The consumers and publishers
		all have an associated backend. Currently there are two backends
		available; ``pyamqlib`` and ``pyqueue``. The ``amqplib`` backend
		is for production use, while the ``Queue`` backend is for use while
		unit testing.

	* Consumer/Publisher operations no longer re-establishes the connection
	  if the connection has been closed.

	* ``Consumer.next`` has been deprecated for a while, and has now been
	  removed.

	* Message objects now have a ``decode`` method, to deserialize the
	  message body.

	* You can now use the Consumer class standalone, without subclassing,
	  by registering callbacks by using ``Consumer.register_callback``.

	* Ability to filter messages in ``Consumer.discard_all``.

	* carrot now includes a basic unit test suite, which hopefully will
		be more complete in later releases.

	* carrot now uses the Sphinx documentation system.

0.3.9 [2009-05-18 04:49 P.M CET] 
--------------------------------------------------------------

	* Consumer.wait() now works properly again. Thanks Alexander Solovyov!

0.3.8 [2009-05-11 02:14 P.M CET] 
--------------------------------------------------------------

	* Rearranged json module import order.
		New order is cjson > simplejson > json > django.util.somplejson

	* _Backwards incompatible change:
		Have to instantiate AMQPConnection object before passing
		it to consumers/publishers. e.g before when you did

			>>> consumer = Consumer(connection=DjangoAMQPConnection)

	you now have to do

			>>> consumer = Consumer(connection=DjangoAMQPConnection())

	or sometimes you might even want to share the same connection with
	publisher/consumer.


0.2.1 [2009-03-24 05:48 P.M CET] 
--------------------------------------------------------------

* Fix typo "package" -> "packages" in setup.py

0.2.0 [2009-03-24 05:23 P.M ]` 
--------------------------------------------------------------

* hasty bugfix release, fixed syntax errors.

0.1.0 [2009-03-24 05:16 P.M ]` 
--------------------------------------------------------------

 * Initial release
