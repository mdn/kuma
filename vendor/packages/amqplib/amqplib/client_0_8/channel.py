"""
AMQP 0-8 Channels

"""
# Copyright (C) 2007-2008 Barry Pederson <bp@barryp.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301

import logging
from Queue import Queue

from abstract_channel import AbstractChannel
from exceptions import *
from serialization import AMQPWriter

__all__ =  [
            'Channel',      # here mainly so it shows in in pydoc
           ]

AMQP_LOGGER = logging.getLogger('amqplib')


class Channel(AbstractChannel):
    """
    work with channels

    The channel class provides methods for a client to establish a
    virtual connection - a channel - to a server and for both peers to
    operate the virtual connection thereafter.

    GRAMMAR:

        channel             = open-channel *use-channel close-channel
        open-channel        = C:OPEN S:OPEN-OK
        use-channel         = C:FLOW S:FLOW-OK
                            / S:FLOW C:FLOW-OK
                            / S:ALERT
                            / functional-class
        close-channel       = C:CLOSE S:CLOSE-OK
                            / S:CLOSE C:CLOSE-OK

    """
    def __init__(self, connection, channel_id=None, auto_decode=True):
        """
        Create a channel bound to a connection and using the specified
        numeric channel_id, and open on the server.

        The 'auto_decode' parameter (defaults to True), indicates
        whether the library should attempt to decode the body
        of Messages to a Unicode string if there's a 'content_encoding'
        property for the message.  If there's no 'content_encoding'
        property, or the decode raises an Exception, the plain string
        is left as the message body.

        """
        if channel_id is None:
            channel_id = connection._get_free_channel_id()
        AMQP_LOGGER.debug('using channel_id: %d' % channel_id)

        super(Channel, self).__init__(connection, channel_id)

        self.default_ticket = 0
        self.is_open = False
        self.active = True # Flow control
        self.alerts = Queue()
        self.returned_messages = Queue()
        self.callbacks = {}
        self.auto_decode = auto_decode

        self._x_open()


    def _do_close(self):
        """
        Tear down this object, after we've agreed to close with the server.

        """
        AMQP_LOGGER.debug('Closed channel #%d' % self.channel_id)
        self.is_open = False
        del self.connection.channels[self.channel_id]
        self.channel_id = self.connection = None
        self.callbacks = {}


    #################

    def _alert(self, args):
        """
        This method allows the server to send a non-fatal warning to
        the client.  This is used for methods that are normally
        asynchronous and thus do not have confirmations, and for which
        the server may detect errors that need to be reported.  Fatal
        errors are handled as channel or connection exceptions; non-
        fatal errors are sent through this method.

        PARAMETERS:
            reply_code: short

                The reply code. The AMQ reply codes are defined in AMQ
                RFC 011.

            reply_text: shortstr

                The localised reply text.  This text can be logged as an
                aid to resolving issues.

            details: table

                detailed information for warning

                A set of fields that provide more information about
                the problem.  The meaning of these fields are defined
                on a per-reply-code basis (TO BE DEFINED).

        """
        reply_code = args.read_short()
        reply_text = args.read_shortstr()
        details = args.read_table()

        self.alerts.put((reply_code, reply_text, details))


    def close(self, reply_code=0, reply_text='', method_sig=(0, 0)):
        """
        request a channel close

        This method indicates that the sender wants to close the
        channel. This may be due to internal conditions (e.g. a forced
        shut-down) or due to an error handling a specific method, i.e.
        an exception.  When a close is due to an exception, the sender
        provides the class and method id of the method which caused
        the exception.

        RULE:

            After sending this method any received method except
            Channel.Close-OK MUST be discarded.

        RULE:

            The peer sending this method MAY use a counter or timeout
            to detect failure of the other peer to respond correctly
            with Channel.Close-OK..

        PARAMETERS:
            reply_code: short

                The reply code. The AMQ reply codes are defined in AMQ
                RFC 011.

            reply_text: shortstr

                The localised reply text.  This text can be logged as an
                aid to resolving issues.

            class_id: short

                failing method class

                When the close is provoked by a method exception, this
                is the class of the method.

            method_id: short

                failing method ID

                When the close is provoked by a method exception, this
                is the ID of the method.

        """
        if not self.is_open:
            # already closed
            return

        args = AMQPWriter()
        args.write_short(reply_code)
        args.write_shortstr(reply_text)
        args.write_short(method_sig[0]) # class_id
        args.write_short(method_sig[1]) # method_id
        self._send_method((20, 40), args)
        return self.wait(allowed_methods=[
                          (20, 41),    # Channel.close_ok
                        ])


    def _close(self, args):
        """
        request a channel close

        This method indicates that the sender wants to close the
        channel. This may be due to internal conditions (e.g. a forced
        shut-down) or due to an error handling a specific method, i.e.
        an exception.  When a close is due to an exception, the sender
        provides the class and method id of the method which caused
        the exception.

        RULE:

            After sending this method any received method except
            Channel.Close-OK MUST be discarded.

        RULE:

            The peer sending this method MAY use a counter or timeout
            to detect failure of the other peer to respond correctly
            with Channel.Close-OK..

        PARAMETERS:
            reply_code: short

                The reply code. The AMQ reply codes are defined in AMQ
                RFC 011.

            reply_text: shortstr

                The localised reply text.  This text can be logged as an
                aid to resolving issues.

            class_id: short

                failing method class

                When the close is provoked by a method exception, this
                is the class of the method.

            method_id: short

                failing method ID

                When the close is provoked by a method exception, this
                is the ID of the method.

        """
        reply_code = args.read_short()
        reply_text = args.read_shortstr()
        class_id = args.read_short()
        method_id = args.read_short()

#        self.close_ok()


#    def close_ok(self):
#        """
#        confirm a channel close
#
#        This method confirms a Channel.Close method and tells the
#        recipient that it is safe to release resources for the channel
#        and close the socket.
#
#        RULE:
#
#            A peer that detects a socket closure without having
#            received a Channel.Close-Ok handshake method SHOULD log
#            the error.
#
#        """
        self._send_method((20, 41))
        self._do_close()

        raise AMQPChannelException(reply_code, reply_text,
            (class_id, method_id))


    def _close_ok(self, args):
        """
        confirm a channel close

        This method confirms a Channel.Close method and tells the
        recipient that it is safe to release resources for the channel
        and close the socket.

        RULE:

            A peer that detects a socket closure without having
            received a Channel.Close-Ok handshake method SHOULD log
            the error.

        """
        self._do_close()


    def flow(self, active):
        """
        enable/disable flow from peer

        This method asks the peer to pause or restart the flow of
        content data. This is a simple flow-control mechanism that a
        peer can use to avoid oveflowing its queues or otherwise
        finding itself receiving more messages than it can process.
        Note that this method is not intended for window control.  The
        peer that receives a request to stop sending content should
        finish sending the current content, if any, and then wait
        until it receives a Flow restart method.

        RULE:

            When a new channel is opened, it is active.  Some
            applications assume that channels are inactive until
            started.  To emulate this behaviour a client MAY open the
            channel, then pause it.

        RULE:

            When sending content data in multiple frames, a peer
            SHOULD monitor the channel for incoming methods and
            respond to a Channel.Flow as rapidly as possible.

        RULE:

            A peer MAY use the Channel.Flow method to throttle
            incoming content data for internal reasons, for example,
            when exchangeing data over a slower connection.

        RULE:

            The peer that requests a Channel.Flow method MAY
            disconnect and/or ban a peer that does not respect the
            request.

        PARAMETERS:
            active: boolean

                start/stop content frames

                If True, the peer starts sending content frames.  If
                False, the peer stops sending content frames.

        """
        args = AMQPWriter()
        args.write_bit(active)
        self._send_method((20, 20), args)
        return self.wait(allowed_methods=[
                          (20, 21),    # Channel.flow_ok
                        ])


    def _flow(self, args):
        """
        enable/disable flow from peer

        This method asks the peer to pause or restart the flow of
        content data. This is a simple flow-control mechanism that a
        peer can use to avoid oveflowing its queues or otherwise
        finding itself receiving more messages than it can process.
        Note that this method is not intended for window control.  The
        peer that receives a request to stop sending content should
        finish sending the current content, if any, and then wait
        until it receives a Flow restart method.

        RULE:

            When a new channel is opened, it is active.  Some
            applications assume that channels are inactive until
            started.  To emulate this behaviour a client MAY open the
            channel, then pause it.

        RULE:

            When sending content data in multiple frames, a peer
            SHOULD monitor the channel for incoming methods and
            respond to a Channel.Flow as rapidly as possible.

        RULE:

            A peer MAY use the Channel.Flow method to throttle
            incoming content data for internal reasons, for example,
            when exchangeing data over a slower connection.

        RULE:

            The peer that requests a Channel.Flow method MAY
            disconnect and/or ban a peer that does not respect the
            request.

        PARAMETERS:
            active: boolean

                start/stop content frames

                If True, the peer starts sending content frames.  If
                False, the peer stops sending content frames.

        """
        self.active = args.read_bit()

        self._x_flow_ok(self.active)


    def _x_flow_ok(self, active):
        """
        confirm a flow method

        Confirms to the peer that a flow command was received and
        processed.

        PARAMETERS:
            active: boolean

                current flow setting

                Confirms the setting of the processed flow method:
                True means the peer will start sending or continue
                to send content frames; False means it will not.

        """
        args = AMQPWriter()
        args.write_bit(active)
        self._send_method((20, 21), args)


    def _flow_ok(self, args):
        """
        confirm a flow method

        Confirms to the peer that a flow command was received and
        processed.

        PARAMETERS:
            active: boolean

                current flow setting

                Confirms the setting of the processed flow method:
                True means the peer will start sending or continue
                to send content frames; False means it will not.

        """
        return args.read_bit()


    def _x_open(self, out_of_band=''):
        """
        open a channel for use

        This method opens a virtual connection (a channel).

        RULE:

            This method MUST NOT be called when the channel is already
            open.

        PARAMETERS:
            out_of_band: shortstr

                out-of-band settings

                Configures out-of-band transfers on this channel.  The
                syntax and meaning of this field will be formally
                defined at a later date.

        """
        if self.is_open:
            return

        args = AMQPWriter()
        args.write_shortstr(out_of_band)
        self._send_method((20, 10), args)
        return self.wait(allowed_methods=[
                          (20, 11),    # Channel.open_ok
                        ])


    def _open_ok(self, args):
        """
        signal that the channel is ready

        This method signals to the client that the channel is ready
        for use.

        """
        self.is_open = True
        AMQP_LOGGER.debug('Channel open')


    #############
    #
    #  Access
    #
    #
    # work with access tickets
    #
    # The protocol control access to server resources using access
    # tickets. A client must explicitly request access tickets before
    # doing work. An access ticket grants a client the right to use a
    # specific set of resources - called a "realm" - in specific ways.
    #
    # GRAMMAR:
    #
    #     access              = C:REQUEST S:REQUEST-OK
    #
    #

    def access_request(self, realm, exclusive=False,
        passive=False, active=False, write=False, read=False):
        """
        request an access ticket

        This method requests an access ticket for an access realm. The
        server responds by granting the access ticket.  If the client
        does not have access rights to the requested realm this causes
        a connection exception.  Access tickets are a per-channel
        resource.

        RULE:

            The realm name MUST start with either "/data" (for
            application resources) or "/admin" (for server
            administration resources). If the realm starts with any
            other path, the server MUST raise a connection exception
            with reply code 403 (access refused).

        RULE:

            The server MUST implement the /data realm and MAY
            implement the /admin realm.  The mapping of resources to
            realms is not defined in the protocol - this is a server-
            side configuration issue.

        PARAMETERS:
            realm: shortstr

                name of requested realm

                RULE:

                    If the specified realm is not known to the server,
                    the server must raise a channel exception with
                    reply code 402 (invalid path).

            exclusive: boolean

                request exclusive access

                Request exclusive access to the realm. If the server
                cannot grant this - because there are other active
                tickets for the realm - it raises a channel exception.

            passive: boolean

                request passive access

                Request message passive access to the specified access
                realm. Passive access lets a client get information
                about resources in the realm but not to make any
                changes to them.

            active: boolean

                request active access

                Request message active access to the specified access
                realm. Acvtive access lets a client get create and
                delete resources in the realm.

            write: boolean

                request write access

                Request write access to the specified access realm.
                Write access lets a client publish messages to all
                exchanges in the realm.

            read: boolean

                request read access

                Request read access to the specified access realm.
                Read access lets a client consume messages from queues
                in the realm.

        The most recently requested ticket is used as the channel's
        default ticket for any method that requires a ticket.

        """
        args = AMQPWriter()
        args.write_shortstr(realm)
        args.write_bit(exclusive)
        args.write_bit(passive)
        args.write_bit(active)
        args.write_bit(write)
        args.write_bit(read)
        self._send_method((30, 10), args)
        return self.wait(allowed_methods=[
                          (30, 11),    # Channel.access_request_ok
                        ])


    def _access_request_ok(self, args):
        """
        grant access to server resources

        This method provides the client with an access ticket. The
        access ticket is valid within the current channel and for the
        lifespan of the channel.

        RULE:

            The client MUST NOT use access tickets except within the
            same channel as originally granted.

        RULE:

            The server MUST isolate access tickets per channel and
            treat an attempt by a client to mix these as a connection
            exception.

        PARAMETERS:
            ticket: short

        """
        self.default_ticket = args.read_short()
        return self.default_ticket


    #############
    #
    #  Exchange
    #
    #
    # work with exchanges
    #
    # Exchanges match and distribute messages across queues.
    # Exchanges can be configured in the server or created at runtime.
    #
    # GRAMMAR:
    #
    #     exchange            = C:DECLARE  S:DECLARE-OK
    #                         / C:DELETE   S:DELETE-OK
    #
    # RULE:
    #
    #     The server MUST implement the direct and fanout exchange
    #     types, and predeclare the corresponding exchanges named
    #     amq.direct and amq.fanout in each virtual host. The server
    #     MUST also predeclare a direct exchange to act as the default
    #     exchange for content Publish methods and for default queue
    #     bindings.
    #
    # RULE:
    #
    #     The server SHOULD implement the topic exchange type, and
    #     predeclare the corresponding exchange named amq.topic in
    #     each virtual host.
    #
    # RULE:
    #
    #     The server MAY implement the system exchange type, and
    #     predeclare the corresponding exchanges named amq.system in
    #     each virtual host. If the client attempts to bind a queue to
    #     the system exchange, the server MUST raise a connection
    #     exception with reply code 507 (not allowed).
    #
    # RULE:
    #
    #     The default exchange MUST be defined as internal, and be
    #     inaccessible to the client except by specifying an empty
    #     exchange name in a content Publish method. That is, the
    #     server MUST NOT let clients make explicit bindings to this
    #     exchange.
    #
    #

    def exchange_declare(self, exchange, type, passive=False, durable=False,
        auto_delete=True, internal=False, nowait=False,
        arguments=None, ticket=None):
        """
        declare exchange, create if needed

        This method creates an exchange if it does not already exist,
        and if the exchange exists, verifies that it is of the correct
        and expected class.

        RULE:

            The server SHOULD support a minimum of 16 exchanges per
            virtual host and ideally, impose no limit except as
            defined by available resources.

        PARAMETERS:
            exchange: shortstr

                RULE:

                    Exchange names starting with "amq." are reserved
                    for predeclared and standardised exchanges.  If
                    the client attempts to create an exchange starting
                    with "amq.", the server MUST raise a channel
                    exception with reply code 403 (access refused).

            type: shortstr

                exchange type

                Each exchange belongs to one of a set of exchange
                types implemented by the server.  The exchange types
                define the functionality of the exchange - i.e. how
                messages are routed through it.  It is not valid or
                meaningful to attempt to change the type of an
                existing exchange.

                RULE:

                    If the exchange already exists with a different
                    type, the server MUST raise a connection exception
                    with a reply code 507 (not allowed).

                RULE:

                    If the server does not support the requested
                    exchange type it MUST raise a connection exception
                    with a reply code 503 (command invalid).

            passive: boolean

                do not create exchange

                If set, the server will not create the exchange.  The
                client can use this to check whether an exchange
                exists without modifying the server state.

                RULE:

                    If set, and the exchange does not already exist,
                    the server MUST raise a channel exception with
                    reply code 404 (not found).

            durable: boolean

                request a durable exchange

                If set when creating a new exchange, the exchange will
                be marked as durable.  Durable exchanges remain active
                when a server restarts. Non-durable exchanges
                (transient exchanges) are purged if/when a server
                restarts.

                RULE:

                    The server MUST support both durable and transient
                    exchanges.

                RULE:

                    The server MUST ignore the durable field if the
                    exchange already exists.

            auto_delete: boolean

                auto-delete when unused

                If set, the exchange is deleted when all queues have
                finished using it.

                RULE:

                    The server SHOULD allow for a reasonable delay
                    between the point when it determines that an
                    exchange is not being used (or no longer used),
                    and the point when it deletes the exchange.  At
                    the least it must allow a client to create an
                    exchange and then bind a queue to it, with a small
                    but non-zero delay between these two actions.

                RULE:

                    The server MUST ignore the auto-delete field if
                    the exchange already exists.

            internal: boolean

                create internal exchange

                If set, the exchange may not be used directly by
                publishers, but only when bound to other exchanges.
                Internal exchanges are used to construct wiring that
                is not visible to applications.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            arguments: table

                arguments for declaration

                A set of arguments for the declaration. The syntax and
                semantics of these arguments depends on the server
                implementation.  This field is ignored if passive is
                True.

            ticket: short

                When a client defines a new exchange, this belongs to
                the access realm of the ticket used.  All further work
                done with that exchange must be done with an access
                ticket for the same realm.

                RULE:

                    The client MUST provide a valid access ticket
                    giving "active" access to the realm in which the
                    exchange exists or will be created, or "passive"
                    access if the if-exists flag is set.

        """
        if arguments is None:
            arguments = {}

        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(exchange)
        args.write_shortstr(type)
        args.write_bit(passive)
        args.write_bit(durable)
        args.write_bit(auto_delete)
        args.write_bit(internal)
        args.write_bit(nowait)
        args.write_table(arguments)
        self._send_method((40, 10), args)

        if not nowait:
            return self.wait(allowed_methods=[
                              (40, 11),    # Channel.exchange_declare_ok
                            ])


    def _exchange_declare_ok(self, args):
        """
        confirms an exchange declaration

        This method confirms a Declare method and confirms the name of
        the exchange, essential for automatically-named exchanges.

        """
        pass


    def exchange_delete(self, exchange, if_unused=False,
        nowait=False, ticket=None):
        """
        delete an exchange

        This method deletes an exchange.  When an exchange is deleted
        all queue bindings on the exchange are cancelled.

        PARAMETERS:
            exchange: shortstr

                RULE:

                    The exchange MUST exist. Attempting to delete a
                    non-existing exchange causes a channel exception.

            if_unused: boolean

                delete only if unused

                If set, the server will only delete the exchange if it
                has no queue bindings. If the exchange has queue
                bindings the server does not delete it but raises a
                channel exception instead.

                RULE:

                    If set, the server SHOULD delete the exchange but
                    only if it has no queue bindings.

                RULE:

                    If set, the server SHOULD raise a channel
                    exception if the exchange is in use.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            ticket: short

                RULE:

                    The client MUST provide a valid access ticket
                    giving "active" access rights to the exchange's
                    access realm.

        """
        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(exchange)
        args.write_bit(if_unused)
        args.write_bit(nowait)
        self._send_method((40, 20), args)

        if not nowait:
            return self.wait(allowed_methods=[
                              (40, 21),    # Channel.exchange_delete_ok
                            ])


    def _exchange_delete_ok(self, args):
        """
        confirm deletion of an exchange

        This method confirms the deletion of an exchange.

        """
        pass


    #############
    #
    #  Queue
    #
    #
    # work with queues
    #
    # Queues store and forward messages.  Queues can be configured in
    # the server or created at runtime.  Queues must be attached to at
    # least one exchange in order to receive messages from publishers.
    #
    # GRAMMAR:
    #
    #     queue               = C:DECLARE  S:DECLARE-OK
    #                         / C:BIND     S:BIND-OK
    #                         / C:PURGE    S:PURGE-OK
    #                         / C:DELETE   S:DELETE-OK
    #
    # RULE:
    #
    #     A server MUST allow any content class to be sent to any
    #     queue, in any mix, and queue and delivery these content
    #     classes independently. Note that all methods that fetch
    #     content off queues are specific to a given content class.
    #
    #

    def queue_bind(self, queue, exchange, routing_key='',
        nowait=False, arguments=None, ticket=None):
        """
        bind queue to an exchange

        This method binds a queue to an exchange.  Until a queue is
        bound it will not receive any messages.  In a classic
        messaging model, store-and-forward queues are bound to a dest
        exchange and subscription queues are bound to a dest_wild
        exchange.

        RULE:

            A server MUST allow ignore duplicate bindings - that is,
            two or more bind methods for a specific queue, with
            identical arguments - without treating these as an error.

        RULE:

            If a bind fails, the server MUST raise a connection
            exception.

        RULE:

            The server MUST NOT allow a durable queue to bind to a
            transient exchange. If the client attempts this the server
            MUST raise a channel exception.

        RULE:

            Bindings for durable queues are automatically durable and
            the server SHOULD restore such bindings after a server
            restart.

        RULE:

            If the client attempts to an exchange that was declared as
            internal, the server MUST raise a connection exception
            with reply code 530 (not allowed).

        RULE:

            The server SHOULD support at least 4 bindings per queue,
            and ideally, impose no limit except as defined by
            available resources.

        PARAMETERS:
            queue: shortstr

                Specifies the name of the queue to bind.  If the queue
                name is empty, refers to the current queue for the
                channel, which is the last declared queue.

                RULE:

                    If the client did not previously declare a queue,
                    and the queue name in this method is empty, the
                    server MUST raise a connection exception with
                    reply code 530 (not allowed).

                RULE:

                    If the queue does not exist the server MUST raise
                    a channel exception with reply code 404 (not
                    found).

            exchange: shortstr

                The name of the exchange to bind to.

                RULE:

                    If the exchange does not exist the server MUST
                    raise a channel exception with reply code 404 (not
                    found).

            routing_key: shortstr

                message routing key

                Specifies the routing key for the binding.  The
                routing key is used for routing messages depending on
                the exchange configuration. Not all exchanges use a
                routing key - refer to the specific exchange
                documentation.  If the routing key is empty and the
                queue name is empty, the routing key will be the
                current queue for the channel, which is the last
                declared queue.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            arguments: table

                arguments for binding

                A set of arguments for the binding.  The syntax and
                semantics of these arguments depends on the exchange
                class.

            ticket: short

                The client provides a valid access ticket giving
                "active" access rights to the queue's access realm.

        """
        if arguments is None:
            arguments = {}

        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(queue)
        args.write_shortstr(exchange)
        args.write_shortstr(routing_key)
        args.write_bit(nowait)
        args.write_table(arguments)
        self._send_method((50, 20), args)

        if not nowait:
            return self.wait(allowed_methods=[
                              (50, 21),    # Channel.queue_bind_ok
                            ])


    def _queue_bind_ok(self, args):
        """
        confirm bind successful

        This method confirms that the bind was successful.

        """
        pass


    def queue_declare(self, queue='', passive=False, durable=False,
        exclusive=False, auto_delete=True, nowait=False,
        arguments=None, ticket=None):
        """
        declare queue, create if needed

        This method creates or checks a queue.  When creating a new
        queue the client can specify various properties that control
        the durability of the queue and its contents, and the level of
        sharing for the queue.

        RULE:

            The server MUST create a default binding for a newly-
            created queue to the default exchange, which is an
            exchange of type 'direct'.

        RULE:

            The server SHOULD support a minimum of 256 queues per
            virtual host and ideally, impose no limit except as
            defined by available resources.

        PARAMETERS:
            queue: shortstr

                RULE:

                    The queue name MAY be empty, in which case the
                    server MUST create a new queue with a unique
                    generated name and return this to the client in
                    the Declare-Ok method.

                RULE:

                    Queue names starting with "amq." are reserved for
                    predeclared and standardised server queues.  If
                    the queue name starts with "amq." and the passive
                    option is False, the server MUST raise a connection
                    exception with reply code 403 (access refused).

            passive: boolean

                do not create queue

                If set, the server will not create the queue.  The
                client can use this to check whether a queue exists
                without modifying the server state.

                RULE:

                    If set, and the queue does not already exist, the
                    server MUST respond with a reply code 404 (not
                    found) and raise a channel exception.

            durable: boolean

                request a durable queue

                If set when creating a new queue, the queue will be
                marked as durable.  Durable queues remain active when
                a server restarts. Non-durable queues (transient
                queues) are purged if/when a server restarts.  Note
                that durable queues do not necessarily hold persistent
                messages, although it does not make sense to send
                persistent messages to a transient queue.

                RULE:

                    The server MUST recreate the durable queue after a
                    restart.

                RULE:

                    The server MUST support both durable and transient
                    queues.

                RULE:

                    The server MUST ignore the durable field if the
                    queue already exists.

            exclusive: boolean

                request an exclusive queue

                Exclusive queues may only be consumed from by the
                current connection. Setting the 'exclusive' flag
                always implies 'auto-delete'.

                RULE:

                    The server MUST support both exclusive (private)
                    and non-exclusive (shared) queues.

                RULE:

                    The server MUST raise a channel exception if
                    'exclusive' is specified and the queue already
                    exists and is owned by a different connection.

            auto_delete: boolean

                auto-delete queue when unused

                If set, the queue is deleted when all consumers have
                finished using it. Last consumer can be cancelled
                either explicitly or because its channel is closed. If
                there was no consumer ever on the queue, it won't be
                deleted.

                RULE:

                    The server SHOULD allow for a reasonable delay
                    between the point when it determines that a queue
                    is not being used (or no longer used), and the
                    point when it deletes the queue.  At the least it
                    must allow a client to create a queue and then
                    create a consumer to read from it, with a small
                    but non-zero delay between these two actions.  The
                    server should equally allow for clients that may
                    be disconnected prematurely, and wish to re-
                    consume from the same queue without losing
                    messages.  We would recommend a configurable
                    timeout, with a suitable default value being one
                    minute.

                RULE:

                    The server MUST ignore the auto-delete field if
                    the queue already exists.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            arguments: table

                arguments for declaration

                A set of arguments for the declaration. The syntax and
                semantics of these arguments depends on the server
                implementation.  This field is ignored if passive is
                True.

            ticket: short

                When a client defines a new queue, this belongs to the
                access realm of the ticket used.  All further work
                done with that queue must be done with an access
                ticket for the same realm.

                The client provides a valid access ticket giving
                "active" access to the realm in which the queue exists
                or will be created, or "passive" access if the if-
                exists flag is set.

        Returns a tuple containing 3 items:
            the name of the queue (essential for automatically-named queues)
            message count
            consumer count

        """
        if arguments is None:
            arguments = {}

        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(queue)
        args.write_bit(passive)
        args.write_bit(durable)
        args.write_bit(exclusive)
        args.write_bit(auto_delete)
        args.write_bit(nowait)
        args.write_table(arguments)
        self._send_method((50, 10), args)

        if not nowait:
            return self.wait(allowed_methods=[
                              (50, 11),    # Channel.queue_declare_ok
                            ])


    def _queue_declare_ok(self, args):
        """
        confirms a queue definition

        This method confirms a Declare method and confirms the name of
        the queue, essential for automatically-named queues.

        PARAMETERS:
            queue: shortstr

                Reports the name of the queue. If the server generated
                a queue name, this field contains that name.

            message_count: long

                number of messages in queue

                Reports the number of messages in the queue, which
                will be zero for newly-created queues.

            consumer_count: long

                number of consumers

                Reports the number of active consumers for the queue.
                Note that consumers can suspend activity
                (Channel.Flow) in which case they do not appear in
                this count.

        """
        queue = args.read_shortstr()
        message_count = args.read_long()
        consumer_count = args.read_long()

        return queue, message_count, consumer_count


    def queue_delete(self, queue='', if_unused=False, if_empty=False,
        nowait=False, ticket=None):
        """
        delete a queue

        This method deletes a queue.  When a queue is deleted any
        pending messages are sent to a dead-letter queue if this is
        defined in the server configuration, and all consumers on the
        queue are cancelled.

        RULE:

            The server SHOULD use a dead-letter queue to hold messages
            that were pending on a deleted queue, and MAY provide
            facilities for a system administrator to move these
            messages back to an active queue.

        PARAMETERS:
            queue: shortstr

                Specifies the name of the queue to delete. If the
                queue name is empty, refers to the current queue for
                the channel, which is the last declared queue.

                RULE:

                    If the client did not previously declare a queue,
                    and the queue name in this method is empty, the
                    server MUST raise a connection exception with
                    reply code 530 (not allowed).

                RULE:

                    The queue must exist. Attempting to delete a non-
                    existing queue causes a channel exception.

            if_unused: boolean

                delete only if unused

                If set, the server will only delete the queue if it
                has no consumers. If the queue has consumers the
                server does does not delete it but raises a channel
                exception instead.

                RULE:

                    The server MUST respect the if-unused flag when
                    deleting a queue.

            if_empty: boolean

                delete only if empty

                If set, the server will only delete the queue if it
                has no messages. If the queue is not empty the server
                raises a channel exception.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            ticket: short

                The client provides a valid access ticket giving
                "active" access rights to the queue's access realm.

        """
        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)

        args.write_shortstr(queue)
        args.write_bit(if_unused)
        args.write_bit(if_empty)
        args.write_bit(nowait)
        self._send_method((50, 40), args)

        if not nowait:
            return self.wait(allowed_methods=[
                              (50, 41),    # Channel.queue_delete_ok
                            ])


    def _queue_delete_ok(self, args):
        """
        confirm deletion of a queue

        This method confirms the deletion of a queue.

        PARAMETERS:
            message_count: long

                number of messages purged

                Reports the number of messages purged.

        """
        return args.read_long()


    def queue_purge(self, queue='', nowait=False, ticket=None):
        """
        purge a queue

        This method removes all messages from a queue.  It does not
        cancel consumers.  Purged messages are deleted without any
        formal "undo" mechanism.

        RULE:

            A call to purge MUST result in an empty queue.

        RULE:

            On transacted channels the server MUST not purge messages
            that have already been sent to a client but not yet
            acknowledged.

        RULE:

            The server MAY implement a purge queue or log that allows
            system administrators to recover accidentally-purged
            messages.  The server SHOULD NOT keep purged messages in
            the same storage spaces as the live messages since the
            volumes of purged messages may get very large.

        PARAMETERS:
            queue: shortstr

                Specifies the name of the queue to purge.  If the
                queue name is empty, refers to the current queue for
                the channel, which is the last declared queue.

                RULE:

                    If the client did not previously declare a queue,
                    and the queue name in this method is empty, the
                    server MUST raise a connection exception with
                    reply code 530 (not allowed).

                RULE:

                    The queue must exist. Attempting to purge a non-
                    existing queue causes a channel exception.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            ticket: short

                The access ticket must be for the access realm that
                holds the queue.

                RULE:

                    The client MUST provide a valid access ticket
                    giving "read" access rights to the queue's access
                    realm.  Note that purging a queue is equivalent to
                    reading all messages and discarding them.

        if nowait is False, returns a message_count

        """
        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(queue)
        args.write_bit(nowait)
        self._send_method((50, 30), args)

        if not nowait:
            return self.wait(allowed_methods=[
                              (50, 31),    # Channel.queue_purge_ok
                            ])


    def _queue_purge_ok(self, args):
        """
        confirms a queue purge

        This method confirms the purge of a queue.

        PARAMETERS:
            message_count: long

                number of messages purged

                Reports the number of messages purged.

        """
        return args.read_long()


    #############
    #
    #  Basic
    #
    #
    # work with basic content
    #
    # The Basic class provides methods that support an industry-
    # standard messaging model.
    #
    # GRAMMAR:
    #
    #     basic               = C:QOS S:QOS-OK
    #                         / C:CONSUME S:CONSUME-OK
    #                         / C:CANCEL S:CANCEL-OK
    #                         / C:PUBLISH content
    #                         / S:RETURN content
    #                         / S:DELIVER content
    #                         / C:GET ( S:GET-OK content / S:GET-EMPTY )
    #                         / C:ACK
    #                         / C:REJECT
    #
    # RULE:
    #
    #     The server SHOULD respect the persistent property of basic
    #     messages and SHOULD make a best-effort to hold persistent
    #     basic messages on a reliable storage mechanism.
    #
    # RULE:
    #
    #     The server MUST NOT discard a persistent basic message in
    #     case of a queue overflow. The server MAY use the
    #     Channel.Flow method to slow or stop a basic message
    #     publisher when necessary.
    #
    # RULE:
    #
    #     The server MAY overflow non-persistent basic messages to
    #     persistent storage and MAY discard or dead-letter non-
    #     persistent basic messages on a priority basis if the queue
    #     size exceeds some configured limit.
    #
    # RULE:
    #
    #     The server MUST implement at least 2 priority levels for
    #     basic messages, where priorities 0-4 and 5-9 are treated as
    #     two distinct levels. The server MAY implement up to 10
    #     priority levels.
    #
    # RULE:
    #
    #     The server MUST deliver messages of the same priority in
    #     order irrespective of their individual persistence.
    #
    # RULE:
    #
    #     The server MUST support both automatic and explicit
    #     acknowledgements on Basic content.
    #

    def basic_ack(self, delivery_tag, multiple=False):
        """
        acknowledge one or more messages

        This method acknowledges one or more messages delivered via
        the Deliver or Get-Ok methods.  The client can ask to confirm
        a single message or a set of messages up to and including a
        specific message.

        PARAMETERS:
            delivery_tag: longlong

                server-assigned delivery tag

                The server-assigned and channel-specific delivery tag

                RULE:

                    The delivery tag is valid only within the channel
                    from which the message was received.  I.e. a client
                    MUST NOT receive a message on one channel and then
                    acknowledge it on another.

                RULE:

                    The server MUST NOT use a zero value for delivery
                    tags.  Zero is reserved for client use, meaning "all
                    messages so far received".

            multiple: boolean

                acknowledge multiple messages

                If set to True, the delivery tag is treated as "up to
                and including", so that the client can acknowledge
                multiple messages with a single method.  If set to
                False, the delivery tag refers to a single message.
                If the multiple field is True, and the delivery tag
                is zero, tells the server to acknowledge all
                outstanding mesages.

                RULE:

                    The server MUST validate that a non-zero delivery-
                    tag refers to an delivered message, and raise a
                    channel exception if this is not the case.

        """
        args = AMQPWriter()
        args.write_longlong(delivery_tag)
        args.write_bit(multiple)
        self._send_method((60, 80), args)


    def basic_cancel(self, consumer_tag, nowait=False):
        """
        end a queue consumer

        This method cancels a consumer. This does not affect already
        delivered messages, but it does mean the server will not send
        any more messages for that consumer.  The client may receive
        an abitrary number of messages in between sending the cancel
        method and receiving the cancel-ok reply.

        RULE:

            If the queue no longer exists when the client sends a
            cancel command, or the consumer has been cancelled for
            other reasons, this command has no effect.

        PARAMETERS:
            consumer_tag: shortstr

                consumer tag

                Identifier for the consumer, valid within the current
                connection.

                RULE:

                    The consumer tag is valid only within the channel
                    from which the consumer was created. I.e. a client
                    MUST NOT create a consumer in one channel and then
                    use it in another.

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

        """
        args = AMQPWriter()
        args.write_shortstr(consumer_tag)
        args.write_bit(nowait)
        self._send_method((60, 30), args)
        return self.wait(allowed_methods=[
                          (60, 31),    # Channel.basic_cancel_ok
                        ])


    def _basic_cancel_ok(self, args):
        """
        confirm a cancelled consumer

        This method confirms that the cancellation was completed.

        PARAMETERS:
            consumer_tag: shortstr

                consumer tag

                Identifier for the consumer, valid within the current
                connection.

                RULE:

                    The consumer tag is valid only within the channel
                    from which the consumer was created. I.e. a client
                    MUST NOT create a consumer in one channel and then
                    use it in another.

        """
        consumer_tag = args.read_shortstr()
        del self.callbacks[consumer_tag]


    def basic_consume(self, queue='', consumer_tag='', no_local=False,
        no_ack=False, exclusive=False, nowait=False,
        callback=None, ticket=None):
        """
        start a queue consumer

        This method asks the server to start a "consumer", which is a
        transient request for messages from a specific queue.
        Consumers last as long as the channel they were created on, or
        until the client cancels them.

        RULE:

            The server SHOULD support at least 16 consumers per queue,
            unless the queue was declared as private, and ideally,
            impose no limit except as defined by available resources.

        PARAMETERS:
            queue: shortstr

                Specifies the name of the queue to consume from.  If
                the queue name is null, refers to the current queue
                for the channel, which is the last declared queue.

                RULE:

                    If the client did not previously declare a queue,
                    and the queue name in this method is empty, the
                    server MUST raise a connection exception with
                    reply code 530 (not allowed).

            consumer_tag: shortstr

                Specifies the identifier for the consumer. The
                consumer tag is local to a connection, so two clients
                can use the same consumer tags. If this field is empty
                the server will generate a unique tag.

                RULE:

                    The tag MUST NOT refer to an existing consumer. If
                    the client attempts to create two consumers with
                    the same non-empty tag the server MUST raise a
                    connection exception with reply code 530 (not
                    allowed).

            no_local: boolean

                do not deliver own messages

                If the no-local field is set the server will not send
                messages to the client that published them.

            no_ack: boolean

                no acknowledgement needed

                If this field is set the server does not expect
                acknowledgments for messages.  That is, when a message
                is delivered to the client the server automatically and
                silently acknowledges it on behalf of the client.  This
                functionality increases performance but at the cost of
                reliability.  Messages can get lost if a client dies
                before it can deliver them to the application.

            exclusive: boolean

                request exclusive access

                Request exclusive consumer access, meaning only this
                consumer can access the queue.

                RULE:

                    If the server cannot grant exclusive access to the
                    queue when asked, - because there are other
                    consumers active - it MUST raise a channel
                    exception with return code 403 (access refused).

            nowait: boolean

                do not send a reply method

                If set, the server will not respond to the method. The
                client should not wait for a reply method.  If the
                server could not complete the method it will raise a
                channel or connection exception.

            callback: Python callable

                function/method called with each delivered message

                For each message delivered by the broker, the
                callable will be called with a Message object
                as the single argument.  If no callable is specified,
                messages are quietly discarded, no_ack should probably
                be set to True in that case.

            ticket: short

                RULE:

                    The client MUST provide a valid access ticket
                    giving "read" access rights to the realm for the
                    queue.

        """
        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(queue)
        args.write_shortstr(consumer_tag)
        args.write_bit(no_local)
        args.write_bit(no_ack)
        args.write_bit(exclusive)
        args.write_bit(nowait)
        self._send_method((60, 20), args)

        if not nowait:
            consumer_tag = self.wait(allowed_methods=[
                              (60, 21),    # Channel.basic_consume_ok
                            ])

        self.callbacks[consumer_tag] = callback

        return consumer_tag


    def _basic_consume_ok(self, args):
        """
        confirm a new consumer

        The server provides the client with a consumer tag, which is
        used by the client for methods called on the consumer at a
        later stage.

        PARAMETERS:
            consumer_tag: shortstr

                Holds the consumer tag specified by the client or
                provided by the server.

        """
        return args.read_shortstr()


    def _basic_deliver(self, args, msg):
        """
        notify the client of a consumer message

        This method delivers a message to the client, via a consumer.
        In the asynchronous message delivery model, the client starts
        a consumer using the Consume method, then the server responds
        with Deliver methods as and when messages arrive for that
        consumer.

        RULE:

            The server SHOULD track the number of times a message has
            been delivered to clients and when a message is
            redelivered a certain number of times - e.g. 5 times -
            without being acknowledged, the server SHOULD consider the
            message to be unprocessable (possibly causing client
            applications to abort), and move the message to a dead
            letter queue.

        PARAMETERS:
            consumer_tag: shortstr

                consumer tag

                Identifier for the consumer, valid within the current
                connection.

                RULE:

                    The consumer tag is valid only within the channel
                    from which the consumer was created. I.e. a client
                    MUST NOT create a consumer in one channel and then
                    use it in another.

            delivery_tag: longlong

                server-assigned delivery tag

                The server-assigned and channel-specific delivery tag

                RULE:

                    The delivery tag is valid only within the channel
                    from which the message was received.  I.e. a client
                    MUST NOT receive a message on one channel and then
                    acknowledge it on another.

                RULE:

                    The server MUST NOT use a zero value for delivery
                    tags.  Zero is reserved for client use, meaning "all
                    messages so far received".

            redelivered: boolean

                message is being redelivered

                This indicates that the message has been previously
                delivered to this or another client.

            exchange: shortstr

                Specifies the name of the exchange that the message
                was originally published to.

            routing_key: shortstr

                Message routing key

                Specifies the routing key name specified when the
                message was published.

        """
        consumer_tag = args.read_shortstr()
        delivery_tag = args.read_longlong()
        redelivered = args.read_bit()
        exchange = args.read_shortstr()
        routing_key = args.read_shortstr()

        msg.delivery_info = {
            'channel': self,
            'consumer_tag': consumer_tag,
            'delivery_tag': delivery_tag,
            'redelivered': redelivered,
            'exchange': exchange,
            'routing_key': routing_key,
            }

        func = self.callbacks.get(consumer_tag, None)
        if func is not None:
            func(msg)


    def basic_get(self, queue='', no_ack=False, ticket=None):
        """
        direct access to a queue

        This method provides a direct access to the messages in a
        queue using a synchronous dialogue that is designed for
        specific types of application where synchronous functionality
        is more important than performance.

        PARAMETERS:
            queue: shortstr

                Specifies the name of the queue to consume from.  If
                the queue name is null, refers to the current queue
                for the channel, which is the last declared queue.

                RULE:

                    If the client did not previously declare a queue,
                    and the queue name in this method is empty, the
                    server MUST raise a connection exception with
                    reply code 530 (not allowed).

            no_ack: boolean

                no acknowledgement needed

                If this field is set the server does not expect
                acknowledgments for messages.  That is, when a message
                is delivered to the client the server automatically and
                silently acknowledges it on behalf of the client.  This
                functionality increases performance but at the cost of
                reliability.  Messages can get lost if a client dies
                before it can deliver them to the application.

            ticket: short

                RULE:

                    The client MUST provide a valid access ticket
                    giving "read" access rights to the realm for the
                    queue.

        Non-blocking, returns a message object, or None.

        """
        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(queue)
        args.write_bit(no_ack)
        self._send_method((60, 70), args)
        return self.wait(allowed_methods=[
                          (60, 71),    # Channel.basic_get_ok
                          (60, 72),    # Channel.basic_get_empty
                        ])


    def _basic_get_empty(self, args):
        """
        indicate no messages available

        This method tells the client that the queue has no messages
        available for the client.

        PARAMETERS:
            cluster_id: shortstr

                Cluster id

                For use by cluster applications, should not be used by
                client applications.

        """
        cluster_id = args.read_shortstr()


    def _basic_get_ok(self, args, msg):
        """
        provide client with a message

        This method delivers a message to the client following a get
        method.  A message delivered by 'get-ok' must be acknowledged
        unless the no-ack option was set in the get method.

        PARAMETERS:
            delivery_tag: longlong

                server-assigned delivery tag

                The server-assigned and channel-specific delivery tag

                RULE:

                    The delivery tag is valid only within the channel
                    from which the message was received.  I.e. a client
                    MUST NOT receive a message on one channel and then
                    acknowledge it on another.

                RULE:

                    The server MUST NOT use a zero value for delivery
                    tags.  Zero is reserved for client use, meaning "all
                    messages so far received".

            redelivered: boolean

                message is being redelivered

                This indicates that the message has been previously
                delivered to this or another client.

            exchange: shortstr

                Specifies the name of the exchange that the message
                was originally published to.  If empty, the message
                was published to the default exchange.

            routing_key: shortstr

                Message routing key

                Specifies the routing key name specified when the
                message was published.

            message_count: long

                number of messages pending

                This field reports the number of messages pending on
                the queue, excluding the message being delivered.
                Note that this figure is indicative, not reliable, and
                can change arbitrarily as messages are added to the
                queue and removed by other clients.

        """
        delivery_tag = args.read_longlong()
        redelivered = args.read_bit()
        exchange = args.read_shortstr()
        routing_key = args.read_shortstr()
        message_count = args.read_long()

        msg.delivery_info = {
            'delivery_tag': delivery_tag,
            'redelivered': redelivered,
            'exchange': exchange,
            'routing_key': routing_key,
            'message_count': message_count
            }

        return msg


    def basic_publish(self, msg, exchange='', routing_key='',
        mandatory=False, immediate=False, ticket=None):
        """
        publish a message

        This method publishes a message to a specific exchange. The
        message will be routed to queues as defined by the exchange
        configuration and distributed to any active consumers when the
        transaction, if any, is committed.

        PARAMETERS:
            exchange: shortstr

                Specifies the name of the exchange to publish to.  The
                exchange name can be empty, meaning the default
                exchange.  If the exchange name is specified, and that
                exchange does not exist, the server will raise a
                channel exception.

                RULE:

                    The server MUST accept a blank exchange name to
                    mean the default exchange.

                RULE:

                    If the exchange was declared as an internal
                    exchange, the server MUST raise a channel
                    exception with a reply code 403 (access refused).

                RULE:

                    The exchange MAY refuse basic content in which
                    case it MUST raise a channel exception with reply
                    code 540 (not implemented).

            routing_key: shortstr

                Message routing key

                Specifies the routing key for the message.  The
                routing key is used for routing messages depending on
                the exchange configuration.

            mandatory: boolean

                indicate mandatory routing

                This flag tells the server how to react if the message
                cannot be routed to a queue.  If this flag is True, the
                server will return an unroutable message with a Return
                method.  If this flag is False, the server silently
                drops the message.

                RULE:

                    The server SHOULD implement the mandatory flag.

            immediate: boolean

                request immediate delivery

                This flag tells the server how to react if the message
                cannot be routed to a queue consumer immediately.  If
                this flag is set, the server will return an
                undeliverable message with a Return method. If this
                flag is zero, the server will queue the message, but
                with no guarantee that it will ever be consumed.

                RULE:

                    The server SHOULD implement the immediate flag.

            ticket: short

                RULE:

                    The client MUST provide a valid access ticket
                    giving "write" access rights to the access realm
                    for the exchange.

        """
        args = AMQPWriter()
        if ticket is not None:
            args.write_short(ticket)
        else:
            args.write_short(self.default_ticket)
        args.write_shortstr(exchange)
        args.write_shortstr(routing_key)
        args.write_bit(mandatory)
        args.write_bit(immediate)

        self._send_method((60, 40), args, msg)


    def basic_qos(self, prefetch_size, prefetch_count, a_global):
        """
        specify quality of service

        This method requests a specific quality of service.  The QoS
        can be specified for the current channel or for all channels
        on the connection.  The particular properties and semantics of
        a qos method always depend on the content class semantics.
        Though the qos method could in principle apply to both peers,
        it is currently meaningful only for the server.

        PARAMETERS:
            prefetch_size: long

                prefetch window in octets

                The client can request that messages be sent in
                advance so that when the client finishes processing a
                message, the following message is already held
                locally, rather than needing to be sent down the
                channel.  Prefetching gives a performance improvement.
                This field specifies the prefetch window size in
                octets.  The server will send a message in advance if
                it is equal to or smaller in size than the available
                prefetch size (and also falls into other prefetch
                limits). May be set to zero, meaning "no specific
                limit", although other prefetch limits may still
                apply. The prefetch-size is ignored if the no-ack
                option is set.

                RULE:

                    The server MUST ignore this setting when the
                    client is not processing any messages - i.e. the
                    prefetch size does not limit the transfer of
                    single messages to a client, only the sending in
                    advance of more messages while the client still
                    has one or more unacknowledged messages.

            prefetch_count: short

                prefetch window in messages

                Specifies a prefetch window in terms of whole
                messages.  This field may be used in combination with
                the prefetch-size field; a message will only be sent
                in advance if both prefetch windows (and those at the
                channel and connection level) allow it. The prefetch-
                count is ignored if the no-ack option is set.

                RULE:

                    The server MAY send less data in advance than
                    allowed by the client's specified prefetch windows
                    but it MUST NOT send more.

            a_global: boolean

                apply to entire connection

                By default the QoS settings apply to the current
                channel only.  If this field is set, they are applied
                to the entire connection.

        """
        args = AMQPWriter()
        args.write_long(prefetch_size)
        args.write_short(prefetch_count)
        args.write_bit(a_global)
        self._send_method((60, 10), args)
        return self.wait(allowed_methods=[
                          (60, 11),    # Channel.basic_qos_ok
                        ])


    def _basic_qos_ok(self, args):
        """
        confirm the requested qos

        This method tells the client that the requested QoS levels
        could be handled by the server.  The requested QoS applies to
        all active consumers until a new QoS is defined.

        """
        pass


    def basic_recover(self, requeue=False):
        """
        redeliver unacknowledged messages

        This method asks the broker to redeliver all unacknowledged
        messages on a specified channel. Zero or more messages may be
        redelivered.  This method is only allowed on non-transacted
        channels.

        RULE:

            The server MUST set the redelivered flag on all messages
            that are resent.

        RULE:

            The server MUST raise a channel exception if this is
            called on a transacted channel.

        PARAMETERS:
            requeue: boolean

                requeue the message

                If this field is False, the message will be redelivered
                to the original recipient.  If this field is True, the
                server will attempt to requeue the message,
                potentially then delivering it to an alternative
                subscriber.

        """
        args = AMQPWriter()
        args.write_bit(requeue)
        self._send_method((60, 100), args)


    def basic_reject(self, delivery_tag, requeue):
        """
        reject an incoming message

        This method allows a client to reject a message.  It can be
        used to interrupt and cancel large incoming messages, or
        return untreatable messages to their original queue.

        RULE:

            The server SHOULD be capable of accepting and process the
            Reject method while sending message content with a Deliver
            or Get-Ok method.  I.e. the server should read and process
            incoming methods while sending output frames.  To cancel a
            partially-send content, the server sends a content body
            frame of size 1 (i.e. with no data except the frame-end
            octet).

        RULE:

            The server SHOULD interpret this method as meaning that
            the client is unable to process the message at this time.

        RULE:

            A client MUST NOT use this method as a means of selecting
            messages to process.  A rejected message MAY be discarded
            or dead-lettered, not necessarily passed to another
            client.

        PARAMETERS:
            delivery_tag: longlong

                server-assigned delivery tag

                The server-assigned and channel-specific delivery tag

                RULE:

                    The delivery tag is valid only within the channel
                    from which the message was received.  I.e. a client
                    MUST NOT receive a message on one channel and then
                    acknowledge it on another.

                RULE:

                    The server MUST NOT use a zero value for delivery
                    tags.  Zero is reserved for client use, meaning "all
                    messages so far received".

            requeue: boolean

                requeue the message

                If this field is False, the message will be discarded.
                If this field is True, the server will attempt to
                requeue the message.

                RULE:

                    The server MUST NOT deliver the message to the
                    same client within the context of the current
                    channel.  The recommended strategy is to attempt
                    to deliver the message to an alternative consumer,
                    and if that is not possible, to move the message
                    to a dead-letter queue.  The server MAY use more
                    sophisticated tracking to hold the message on the
                    queue and redeliver it to the same client at a
                    later stage.

        """
        args = AMQPWriter()
        args.write_longlong(delivery_tag)
        args.write_bit(requeue)
        self._send_method((60, 90), args)


    def _basic_return(self, args, msg):
        """
        return a failed message

        This method returns an undeliverable message that was
        published with the "immediate" flag set, or an unroutable
        message published with the "mandatory" flag set. The reply
        code and text provide information about the reason that the
        message was undeliverable.

        PARAMETERS:
            reply_code: short

                The reply code. The AMQ reply codes are defined in AMQ
                RFC 011.

            reply_text: shortstr

                The localised reply text.  This text can be logged as an
                aid to resolving issues.

            exchange: shortstr

                Specifies the name of the exchange that the message
                was originally published to.

            routing_key: shortstr

                Message routing key

                Specifies the routing key name specified when the
                message was published.

        """
        reply_code = args.read_short()
        reply_text = args.read_shortstr()
        exchange = args.read_shortstr()
        routing_key = args.read_shortstr()

        self.returned_messages.put(
            (reply_code, reply_text, exchange, routing_key, msg)
            )


    #############
    #
    #  Tx
    #
    #
    # work with standard transactions
    #
    # Standard transactions provide so-called "1.5 phase commit".  We
    # can ensure that work is never lost, but there is a chance of
    # confirmations being lost, so that messages may be resent.
    # Applications that use standard transactions must be able to
    # detect and ignore duplicate messages.
    #
    # GRAMMAR:
    #
    #     tx                  = C:SELECT S:SELECT-OK
    #                         / C:COMMIT S:COMMIT-OK
    #                         / C:ROLLBACK S:ROLLBACK-OK
    #
    # RULE:
    #
    #     An client using standard transactions SHOULD be able to
    #     track all messages received within a reasonable period, and
    #     thus detect and reject duplicates of the same message. It
    #     SHOULD NOT pass these to the application layer.
    #
    #

    def tx_commit(self):
        """
        commit the current transaction

        This method commits all messages published and acknowledged in
        the current transaction.  A new transaction starts immediately
        after a commit.

        """
        self._send_method((90, 20))
        return self.wait(allowed_methods=[
                          (90, 21),    # Channel.tx_commit_ok
                        ])


    def _tx_commit_ok(self, args):
        """
        confirm a successful commit

        This method confirms to the client that the commit succeeded.
        Note that if a commit fails, the server raises a channel
        exception.

        """
        pass


    def tx_rollback(self):
        """
        abandon the current transaction

        This method abandons all messages published and acknowledged
        in the current transaction.  A new transaction starts
        immediately after a rollback.

        """
        self._send_method((90, 30))
        return self.wait(allowed_methods=[
                          (90, 31),    # Channel.tx_rollback_ok
                        ])


    def _tx_rollback_ok(self, args):
        """
        confirm a successful rollback

        This method confirms to the client that the rollback
        succeeded. Note that if an rollback fails, the server raises a
        channel exception.

        """
        pass


    def tx_select(self):
        """
        select standard transaction mode

        This method sets the channel to use standard transactions.
        The client must use this method at least once on a channel
        before using the Commit or Rollback methods.

        """
        self._send_method((90, 10))
        return self.wait(allowed_methods=[
                          (90, 11),    # Channel.tx_select_ok
                        ])


    def _tx_select_ok(self, args):
        """
        confirm transaction mode

        This method confirms to the client that the channel was
        successfully set to use standard transactions.

        """
        pass


    _METHOD_MAP = {
        (20, 11): _open_ok,
        (20, 20): _flow,
        (20, 21): _flow_ok,
        (20, 30): _alert,
        (20, 40): _close,
        (20, 41): _close_ok,
        (30, 11): _access_request_ok,
        (40, 11): _exchange_declare_ok,
        (40, 21): _exchange_delete_ok,
        (50, 11): _queue_declare_ok,
        (50, 21): _queue_bind_ok,
        (50, 31): _queue_purge_ok,
        (50, 41): _queue_delete_ok,
        (60, 11): _basic_qos_ok,
        (60, 21): _basic_consume_ok,
        (60, 31): _basic_cancel_ok,
        (60, 50): _basic_return,
        (60, 60): _basic_deliver,
        (60, 71): _basic_get_ok,
        (60, 72): _basic_get_empty,
        (90, 11): _tx_select_ok,
        (90, 21): _tx_commit_ok,
        (90, 31): _tx_rollback_ok,
        }
