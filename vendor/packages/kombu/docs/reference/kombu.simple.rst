.. currentmodule:: kombu.simple

.. automodule:: kombu.simple

    .. contents::
        :local:

    Persistent
    ----------

    .. autoclass:: SimpleQueue

        .. attribute:: channel

            Current channel

        .. attribute:: producer

            :class:`~kombu.messaging.Producer` used to publish messages.

        .. attribute:: consumer

            :class:`~kombu.messaging.Consumer` used to receive messages.

        .. attribute:: no_ack

            flag to enable/disable acknowledgements.

        .. attribute:: queue

            :class:`~kombu.entity.Queue` to consume from (if consuming).

        .. attribute:: queue_opts

            Additional options for the queue declaration.

         .. attribute:: exchange_opts

            Additional options for the exchange declaration.

        .. automethod:: get
        .. automethod:: get_nowait
        .. automethod:: put
        .. automethod:: clear
        .. automethod:: __len__
        .. automethod:: qsize
        .. automethod:: close

    Buffer
    ------

    .. autoclass:: SimpleBuffer

        .. attribute:: channel

            Current channel

        .. attribute:: producer

            :class:`~kombu.messaging.Producer` used to publish messages.

        .. attribute:: consumer

            :class:`~kombu.messaging.Consumer` used to receive messages.

        .. attribute:: no_ack

            flag to enable/disable acknowledgements.

        .. attribute:: queue

            :class:`~kombu.entity.Queue` to consume from (if consuming).

        .. attribute:: queue_opts

            Additional options for the queue declaration.

         .. attribute:: exchange_opts

            Additional options for the exchange declaration.

        .. automethod:: get
        .. automethod:: get_nowait
        .. automethod:: put
        .. automethod:: clear
        .. automethod:: __len__
        .. automethod:: qsize
        .. automethod:: close

