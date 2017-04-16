# pool.py - Connection pooling for SQLAlchemy
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010 Michael Bayer
# mike_mp@zzzcomputing.com
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php


"""Connection pooling for DB-API connections.

Provides a number of connection pool implementations for a variety of
usage scenarios and thread behavior requirements imposed by the
application, DB-API or database itself.

Also provides a DB-API 2.0 connection proxying mechanism allowing
regular DB-API connect() methods to be transparently managed by a
SQLAlchemy connection pool.
"""

import weakref, time, threading

from sqlalchemy import exc, log
from sqlalchemy import queue as sqla_queue
from sqlalchemy.util import threading, pickle, as_interface, memoized_property

proxies = {}

def manage(module, **params):
    """Return a proxy for a DB-API module that automatically 
    pools connections.

    Given a DB-API 2.0 module and pool management parameters, returns
    a proxy for the module that will automatically pool connections,
    creating new connection pools for each distinct set of connection
    arguments sent to the decorated module's connect() function.

    :param module: a DB-API 2.0 database module

    :param poolclass: the class used by the pool module to provide
      pooling.  Defaults to :class:`QueuePool`.

    :param \*\*params: will be passed through to *poolclass*

    """
    try:
        return proxies[module]
    except KeyError:
        return proxies.setdefault(module, _DBProxy(module, **params))

def clear_managers():
    """Remove all current DB-API 2.0 managers.

    All pools and connections are disposed.
    """

    for manager in proxies.itervalues():
        manager.close()
    proxies.clear()

class Pool(log.Identified):
    """Abstract base class for connection pools."""

    def __init__(self, 
                    creator, recycle=-1, echo=None, 
                    use_threadlocal=False,
                    logging_name=None,
                    reset_on_return=True, listeners=None):
        """
        Construct a Pool.

        :param creator: a callable function that returns a DB-API
          connection object.  The function will be called with
          parameters.

        :param recycle: If set to non -1, number of seconds between
          connection recycling, which means upon checkout, if this
          timeout is surpassed the connection will be closed and
          replaced with a newly opened connection. Defaults to -1.

        :param logging_name:  String identifier which will be used within
          the "name" field of logging records generated within the 
          "sqlalchemy.pool" logger. Defaults to a hexstring of the object's 
          id.

        :param echo: If True, connections being pulled and retrieved
          from the pool will be logged to the standard output, as well
          as pool sizing information.  Echoing can also be achieved by
          enabling logging for the "sqlalchemy.pool"
          namespace. Defaults to False.

        :param use_threadlocal: If set to True, repeated calls to
          :meth:`connect` within the same application thread will be
          guaranteed to return the same connection object, if one has
          already been retrieved from the pool and has not been
          returned yet.  Offers a slight performance advantage at the
          cost of individual transactions by default.  The
          :meth:`unique_connection` method is provided to bypass the
          threadlocal behavior installed into :meth:`connect`.

        :param reset_on_return: If true, reset the database state of
          connections returned to the pool.  This is typically a
          ROLLBACK to release locks and transaction resources.
          Disable at your own peril.  Defaults to True.

        :param listeners: A list of
          :class:`~sqlalchemy.interfaces.PoolListener`-like objects or
          dictionaries of callables that receive events when DB-API
          connections are created, checked out and checked in to the
          pool.

        """
        if logging_name:
            self.logging_name = self._orig_logging_name = logging_name
        else:
            self._orig_logging_name = None
            
        self.logger = log.instance_logger(self, echoflag=echo)
        self._threadconns = threading.local()
        self._creator = creator
        self._recycle = recycle
        self._use_threadlocal = use_threadlocal
        self._reset_on_return = reset_on_return
        self.echo = echo
        self.listeners = []
        self._on_connect = []
        self._on_first_connect = []
        self._on_checkout = []
        self._on_checkin = []

        if listeners:
            for l in listeners:
                self.add_listener(l)

    def unique_connection(self):
        """Produce a DBAPI connection that is not referenced by any
        thread-local context.
        
        This method is different from :meth:`.Pool.connect` only if the
        ``use_threadlocal`` flag has been set to ``True``.
        
        """
        
        return _ConnectionFairy(self).checkout()

    def create_connection(self):
        """Called by subclasses to create a new ConnectionRecord."""
        
        return _ConnectionRecord(self)

    def recreate(self):
        """Return a new :class:`.Pool`, of the same class as this one
        and configured with identical creation arguments.
        
        This method is used in conjunection with :meth:`dispose` 
        to close out an entire :class:`.Pool` and create a new one in 
        its place.
        
        """

        raise NotImplementedError()

    def dispose(self):
        """Dispose of this pool.

        This method leaves the possibility of checked-out connections
        remaining open, It is advised to not reuse the pool once dispose()
        is called, and to instead use a new pool constructed by the
        recreate() method.
        
        """

        raise NotImplementedError()

    def connect(self):
        """Return a DBAPI connection from the pool.
        
        The connection is instrumented such that when its 
        ``close()`` method is called, the connection will be returned to 
        the pool.
        
        """
        if not self._use_threadlocal:
            return _ConnectionFairy(self).checkout()

        try:
            rec = self._threadconns.current()
            if rec:
                return rec.checkout()
        except AttributeError:
            pass

        agent = _ConnectionFairy(self)
        self._threadconns.current = weakref.ref(agent)
        return agent.checkout()

    def return_conn(self, record):
        """Given a _ConnectionRecord, return it to the :class:`.Pool`.
        
        This method is called when an instrumented DBAPI connection
        has its ``close()`` method called.
        
        """
        if self._use_threadlocal and hasattr(self._threadconns, "current"):
            del self._threadconns.current
        self.do_return_conn(record)

    def get(self):
        """Return a non-instrumented DBAPI connection from this :class:`.Pool`.
        
        This is called by ConnectionRecord in order to get its DBAPI 
        resource.
        
        """
        return self.do_get()

    def do_get(self):
        """Implementation for :meth:`get`, supplied by subclasses."""
        
        raise NotImplementedError()

    def do_return_conn(self, conn):
        """Implementation for :meth:`return_conn`, supplied by subclasses."""
        
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def add_listener(self, listener):
        """Add a ``PoolListener``-like object to this pool.

        ``listener`` may be an object that implements some or all of
        PoolListener, or a dictionary of callables containing implementations
        of some or all of the named methods in PoolListener.

        """

        listener = as_interface(listener,
            methods=('connect', 'first_connect', 'checkout', 'checkin'))

        self.listeners.append(listener)
        if hasattr(listener, 'connect'):
            self._on_connect.append(listener)
        if hasattr(listener, 'first_connect'):
            self._on_first_connect.append(listener)
        if hasattr(listener, 'checkout'):
            self._on_checkout.append(listener)
        if hasattr(listener, 'checkin'):
            self._on_checkin.append(listener)

class _ConnectionRecord(object):
    def __init__(self, pool):
        self.__pool = pool
        self.connection = self.__connect()
        self.info = {}
        ls = pool.__dict__.pop('_on_first_connect', None)
        if ls is not None:
            for l in ls:
                l.first_connect(self.connection, self)
        if pool._on_connect:
            for l in pool._on_connect:
                l.connect(self.connection, self)

    def close(self):
        if self.connection is not None:
            self.__pool.logger.debug("Closing connection %r", self.connection)
            try:
                self.connection.close()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.__pool.logger.debug("Exception closing connection %r",
                                self.connection)

    def invalidate(self, e=None):
        if e is not None:
            self.__pool.logger.info(
                "Invalidate connection %r (reason: %s:%s)",
                self.connection, e.__class__.__name__, e)
        else:
            self.__pool.logger.info(
                "Invalidate connection %r", self.connection)
        self.__close()
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = self.__connect()
            self.info.clear()
            if self.__pool._on_connect:
                for l in self.__pool._on_connect:
                    l.connect(self.connection, self)
        elif self.__pool._recycle > -1 and \
                time.time() - self.starttime > self.__pool._recycle:
            self.__pool.logger.info(
                    "Connection %r exceeded timeout; recycling",
                    self.connection)
            self.__close()
            self.connection = self.__connect()
            self.info.clear()
            if self.__pool._on_connect:
                for l in self.__pool._on_connect:
                    l.connect(self.connection, self)
        return self.connection

    def __close(self):
        try:
            self.__pool.logger.debug("Closing connection %r", self.connection)
            self.connection.close()
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.__pool.logger.debug(
                        "Connection %r threw an error on close: %s",
                        self.connection, e)

    def __connect(self):
        try:
            self.starttime = time.time()
            connection = self.__pool._creator()
            self.__pool.logger.debug("Created new connection %r", connection)
            return connection
        except Exception, e:
            self.__pool.logger.debug("Error on connect(): %s", e)
            raise


def _finalize_fairy(connection, connection_record, pool, ref=None):
    _refs.discard(connection_record)
        
    if ref is not None and \
                (connection_record.fairy is not ref or 
                isinstance(pool, AssertionPool)):
        return

    if connection is not None:
        try:
            if pool._reset_on_return:
                connection.rollback()
            # Immediately close detached instances
            if connection_record is None:
                connection.close()
        except Exception, e:
            if connection_record is not None:
                connection_record.invalidate(e=e)
            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise
                
    if connection_record is not None:
        connection_record.fairy = None
        pool.logger.debug("Connection %r being returned to pool", connection)
        if pool._on_checkin:
            for l in pool._on_checkin:
                l.checkin(connection, connection_record)
        pool.return_conn(connection_record)

_refs = set()

class _ConnectionFairy(object):
    """Proxies a DB-API connection and provides return-on-dereference
    support."""

    __slots__ = '_pool', '__counter', 'connection', \
                '_connection_record', '__weakref__', '_detached_info'
    
    def __init__(self, pool):
        self._pool = pool
        self.__counter = 0
        try:
            rec = self._connection_record = pool.get()
            conn = self.connection = self._connection_record.get_connection()
            rec.fairy = weakref.ref(
                            self, 
                            lambda ref:_finalize_fairy(conn, rec, pool, ref)
                        )
            _refs.add(rec)
        except:
            # helps with endless __getattr__ loops later on
            self.connection = None 
            self._connection_record = None
            raise
        self._pool.logger.debug("Connection %r checked out from pool" %
                       self.connection)

    @property
    def _logger(self):
        return self._pool.logger

    @property
    def is_valid(self):
        return self.connection is not None

    @property
    def info(self):
        """An info collection unique to this DB-API connection."""

        try:
            return self._connection_record.info
        except AttributeError:
            if self.connection is None:
                raise exc.InvalidRequestError("This connection is closed")
            try:
                return self._detached_info
            except AttributeError:
                self._detached_info = value = {}
                return value

    def invalidate(self, e=None):
        """Mark this connection as invalidated.

        The connection will be immediately closed.  The containing
        ConnectionRecord will create a new connection when next used.
        """

        if self.connection is None:
            raise exc.InvalidRequestError("This connection is closed")
        if self._connection_record is not None:
            self._connection_record.invalidate(e=e)
        self.connection = None
        self._close()

    def cursor(self, *args, **kwargs):
        try:
            c = self.connection.cursor(*args, **kwargs)
            return _CursorFairy(self, c)
        except Exception, e:
            self.invalidate(e=e)
            raise

    def __getattr__(self, key):
        return getattr(self.connection, key)

    def checkout(self):
        if self.connection is None:
            raise exc.InvalidRequestError("This connection is closed")
        self.__counter += 1

        if not self._pool._on_checkout or self.__counter != 1:
            return self

        # Pool listeners can trigger a reconnection on checkout
        attempts = 2
        while attempts > 0:
            try:
                for l in self._pool._on_checkout:
                    l.checkout(self.connection, self._connection_record, self)
                return self
            except exc.DisconnectionError, e:
                self._pool.logger.info(
                "Disconnection detected on checkout: %s", e)
                self._connection_record.invalidate(e)
                self.connection = self._connection_record.get_connection()
                attempts -= 1

        self._pool.logger.info("Reconnection attempts exhausted on checkout")
        self.invalidate()
        raise exc.InvalidRequestError("This connection is closed")

    def detach(self):
        """Separate this connection from its Pool.

        This means that the connection will no longer be returned to the
        pool when closed, and will instead be literally closed.  The
        containing ConnectionRecord is separated from the DB-API connection,
        and will create a new connection when next used.

        Note that any overall connection limiting constraints imposed by a
        Pool implementation may be violated after a detach, as the detached
        connection is removed from the pool's knowledge and control.
        """

        if self._connection_record is not None:
            _refs.remove(self._connection_record)
            self._connection_record.fairy = None
            self._connection_record.connection = None
            self._pool.do_return_conn(self._connection_record)
            self._detached_info = \
              self._connection_record.info.copy()
            self._connection_record = None

    def close(self):
        self.__counter -= 1
        if self.__counter == 0:
            self._close()

    def _close(self):
        _finalize_fairy(self.connection, self._connection_record, self._pool)
        self.connection = None
        self._connection_record = None

class _CursorFairy(object):
    __slots__ = '_parent', 'cursor', 'execute'

    def __init__(self, parent, cursor):
        self._parent = parent
        self.cursor = cursor
        self.execute = cursor.execute
        
    def invalidate(self, e=None):
        self._parent.invalidate(e=e)
    
    def __iter__(self):
        return iter(self.cursor)
        
    def close(self):
        try:
            self.cursor.close()
        except Exception, e:
            try:
                ex_text = str(e)
            except TypeError:
                ex_text = repr(e)
            self._parent._logger.warn("Error closing cursor: %s", ex_text)

            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise
    
    def __setattr__(self, key, value):
        if key in self.__slots__:
            object.__setattr__(self, key, value)
        else:
            setattr(self.cursor, key, value)
            
    def __getattr__(self, key):
        return getattr(self.cursor, key)

class SingletonThreadPool(Pool):
    """A Pool that maintains one connection per thread.

    Maintains one connection per each thread, never moving a connection to a
    thread other than the one which it was created in.

    This is used for SQLite, which both does not handle multithreading by
    default, and also requires a singleton connection if a :memory: database
    is being used.

    Options are the same as those of :class:`Pool`, as well as:

    :param pool_size: The number of threads in which to maintain connections 
        at once.  Defaults to five.
      
    """

    def __init__(self, creator, pool_size=5, **kw):
        kw['use_threadlocal'] = True
        Pool.__init__(self, creator, **kw)
        self._conn = threading.local()
        self._all_conns = set()
        self.size = pool_size

    def recreate(self):
        self.logger.info("Pool recreating")
        return SingletonThreadPool(self._creator, 
            pool_size=self.size, 
            recycle=self._recycle, 
            echo=self.echo, 
            logging_name=self._orig_logging_name,
            use_threadlocal=self._use_threadlocal, 
            listeners=self.listeners)

    def dispose(self):
        """Dispose of this pool."""

        for conn in self._all_conns:
            try:
                conn.close()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                # pysqlite won't even let you close a conn from a thread
                # that didn't create it
                pass
        
        self._all_conns.clear()
            
    def dispose_local(self):
        if hasattr(self._conn, 'current'):
            conn = self._conn.current()
            self._all_conns.discard(conn)
            del self._conn.current

    def cleanup(self):
        while len(self._all_conns) > self.size:
            self._all_conns.pop()

    def status(self):
        return "SingletonThreadPool id:%d size: %d" % \
                            (id(self), len(self._all_conns))

    def do_return_conn(self, conn):
        pass

    def do_get(self):
        try:
            c = self._conn.current()
            if c:
                return c
        except AttributeError:
            pass
        c = self.create_connection()
        self._conn.current = weakref.ref(c)
        self._all_conns.add(c)
        if len(self._all_conns) > self.size:
            self.cleanup()
        return c

class QueuePool(Pool):
    """A Pool that imposes a limit on the number of open connections."""

    def __init__(self, creator, pool_size=5, max_overflow=10, timeout=30,
                 **kw):
        """
        Construct a QueuePool.

        :param creator: a callable function that returns a DB-API
          connection object.  The function will be called with
          parameters.

        :param pool_size: The size of the pool to be maintained,
          defaults to 5. This is the largest number of connections that
          will be kept persistently in the pool. Note that the pool
          begins with no connections; once this number of connections
          is requested, that number of connections will remain.
          ``pool_size`` can be set to 0 to indicate no size limit; to
          disable pooling, use a :class:`~sqlalchemy.pool.NullPool`
          instead.

        :param max_overflow: The maximum overflow size of the
          pool. When the number of checked-out connections reaches the
          size set in pool_size, additional connections will be
          returned up to this limit. When those additional connections
          are returned to the pool, they are disconnected and
          discarded. It follows then that the total number of
          simultaneous connections the pool will allow is pool_size +
          `max_overflow`, and the total number of "sleeping"
          connections the pool will allow is pool_size. `max_overflow`
          can be set to -1 to indicate no overflow limit; no limit
          will be placed on the total number of concurrent
          connections. Defaults to 10.

        :param timeout: The number of seconds to wait before giving up
          on returning a connection. Defaults to 30.

        :param recycle: If set to non -1, number of seconds between
          connection recycling, which means upon checkout, if this
          timeout is surpassed the connection will be closed and
          replaced with a newly opened connection. Defaults to -1.

        :param echo: If True, connections being pulled and retrieved
          from the pool will be logged to the standard output, as well
          as pool sizing information.  Echoing can also be achieved by
          enabling logging for the "sqlalchemy.pool"
          namespace. Defaults to False.

        :param use_threadlocal: If set to True, repeated calls to
          :meth:`connect` within the same application thread will be
          guaranteed to return the same connection object, if one has
          already been retrieved from the pool and has not been
          returned yet.  Offers a slight performance advantage at the
          cost of individual transactions by default.  The
          :meth:`unique_connection` method is provided to bypass the
          threadlocal behavior installed into :meth:`connect`.

        :param reset_on_return: If true, reset the database state of
          connections returned to the pool.  This is typically a
          ROLLBACK to release locks and transaction resources.
          Disable at your own peril.  Defaults to True.

        :param listeners: A list of
          :class:`~sqlalchemy.interfaces.PoolListener`-like objects or
          dictionaries of callables that receive events when DB-API
          connections are created, checked out and checked in to the
          pool.

        """
        Pool.__init__(self, creator, **kw)
        self._pool = sqla_queue.Queue(pool_size)
        self._overflow = 0 - pool_size
        self._max_overflow = max_overflow
        self._timeout = timeout
        self._overflow_lock = self._max_overflow > -1 and \
                                    threading.Lock() or None

    def recreate(self):
        self.logger.info("Pool recreating")
        return QueuePool(self._creator, pool_size=self._pool.maxsize, 
                          max_overflow=self._max_overflow,
                          timeout=self._timeout, 
                          recycle=self._recycle, echo=self.echo, 
                          logging_name=self._orig_logging_name,
                          use_threadlocal=self._use_threadlocal,
                          listeners=self.listeners)

    def do_return_conn(self, conn):
        try:
            self._pool.put(conn, False)
        except sqla_queue.Full:
            if self._overflow_lock is None:
                self._overflow -= 1
            else:
                self._overflow_lock.acquire()
                try:
                    self._overflow -= 1
                finally:
                    self._overflow_lock.release()

    def do_get(self):
        try:
            wait = self._max_overflow > -1 and \
                        self._overflow >= self._max_overflow
            return self._pool.get(wait, self._timeout)
        except sqla_queue.Empty:
            if self._max_overflow > -1 and \
                        self._overflow >= self._max_overflow:
                if not wait:
                    return self.do_get()
                else:
                    raise exc.TimeoutError(
                            "QueuePool limit of size %d overflow %d reached, "
                            "connection timed out, timeout %d" % 
                            (self.size(), self.overflow(), self._timeout))

            if self._overflow_lock is not None:
                self._overflow_lock.acquire()

            if self._max_overflow > -1 and \
                        self._overflow >= self._max_overflow:
                if self._overflow_lock is not None:
                    self._overflow_lock.release()
                return self.do_get()

            try:
                con = self.create_connection()
                self._overflow += 1
            finally:
                if self._overflow_lock is not None:
                    self._overflow_lock.release()
            return con

    def dispose(self):
        while True:
            try:
                conn = self._pool.get(False)
                conn.close()
            except sqla_queue.Empty:
                break

        self._overflow = 0 - self.size()
        self.logger.info("Pool disposed. %s", self.status())

    def status(self):
        return "Pool size: %d  Connections in pool: %d "\
                "Current Overflow: %d Current Checked out "\
                "connections: %d" % (self.size(), 
                                    self.checkedin(), 
                                    self.overflow(), 
                                    self.checkedout())

    def size(self):
        return self._pool.maxsize

    def checkedin(self):
        return self._pool.qsize()

    def overflow(self):
        return self._overflow

    def checkedout(self):
        return self._pool.maxsize - self._pool.qsize() + self._overflow

class NullPool(Pool):
    """A Pool which does not pool connections.

    Instead it literally opens and closes the underlying DB-API connection
    per each connection open/close.

    Reconnect-related functions such as ``recycle`` and connection
    invalidation are not supported by this Pool implementation, since
    no connections are held persistently.

    """

    def status(self):
        return "NullPool"

    def do_return_conn(self, conn):
        conn.close()

    def do_return_invalid(self, conn):
        pass

    def do_get(self):
        return self.create_connection()

    def recreate(self):
        self.logger.info("Pool recreating")

        return NullPool(self._creator, 
            recycle=self._recycle, 
            echo=self.echo, 
            logging_name=self._orig_logging_name,
            use_threadlocal=self._use_threadlocal, 
            listeners=self.listeners)

    def dispose(self):
        pass


class StaticPool(Pool):
    """A Pool of exactly one connection, used for all requests.

    Reconnect-related functions such as ``recycle`` and connection
    invalidation (which is also used to support auto-reconnect) are not
    currently supported by this Pool implementation but may be implemented
    in a future release.

    """

    @memoized_property
    def _conn(self):
        return self._creator()

    @memoized_property
    def connection(self):
        return _ConnectionRecord(self)
        
    def status(self):
        return "StaticPool"

    def dispose(self):
        if '_conn' in self.__dict__:
            self._conn.close()
            self._conn = None

    def recreate(self):
        self.logger.info("Pool recreating")
        return self.__class__(creator=self._creator,
                              recycle=self._recycle,
                              use_threadlocal=self._use_threadlocal,
                              reset_on_return=self._reset_on_return,
                              echo=self.echo,
                              logging_name=self._orig_logging_name,
                              listeners=self.listeners)

    def create_connection(self):
        return self._conn

    def do_return_conn(self, conn):
        pass

    def do_return_invalid(self, conn):
        pass

    def do_get(self):
        return self.connection

class AssertionPool(Pool):
    """A Pool that allows at most one checked out connection at any given
    time.

    This will raise an exception if more than one connection is checked out
    at a time.  Useful for debugging code that is using more connections
    than desired.

    """

    def __init__(self, *args, **kw):
        self._conn = None
        self._checked_out = False
        Pool.__init__(self, *args, **kw)
        
    def status(self):
        return "AssertionPool"

    def do_return_conn(self, conn):
        if not self._checked_out:
            raise AssertionError("connection is not checked out")
        self._checked_out = False
        assert conn is self._conn

    def do_return_invalid(self, conn):
        self._conn = None
        self._checked_out = False
    
    def dispose(self):
        self._checked_out = False
        if self._conn:
            self._conn.close()

    def recreate(self):
        self.logger.info("Pool recreating")
        return AssertionPool(self._creator, echo=self.echo, 
                            logging_name=self._orig_logging_name,
                            listeners=self.listeners)
        
    def do_get(self):
        if self._checked_out:
            raise AssertionError("connection is already checked out")
            
        if not self._conn:
            self._conn = self.create_connection()
        
        self._checked_out = True
        return self._conn

class _DBProxy(object):
    """Layers connection pooling behavior on top of a standard DB-API module.

    Proxies a DB-API 2.0 connect() call to a connection pool keyed to the
    specific connect parameters. Other functions and attributes are delegated
    to the underlying DB-API module.
    """

    def __init__(self, module, poolclass=QueuePool, **kw):
        """Initializes a new proxy.

        module
          a DB-API 2.0 module

        poolclass
          a Pool class, defaulting to QueuePool

        Other parameters are sent to the Pool object's constructor.
        
        """

        self.module = module
        self.kw = kw
        self.poolclass = poolclass
        self.pools = {}
        self._create_pool_mutex = threading.Lock()
        
    def close(self):
        for key in self.pools.keys():
            del self.pools[key]

    def __del__(self):
        self.close()

    def __getattr__(self, key):
        return getattr(self.module, key)

    def get_pool(self, *args, **kw):
        key = self._serialize(*args, **kw)
        try:
            return self.pools[key]
        except KeyError:
            self._create_pool_mutex.acquire()
            try:
                if key not in self.pools:
                    pool = self.poolclass(lambda: 
                                self.module.connect(*args, **kw), **self.kw)
                    self.pools[key] = pool
                    return pool
                else:
                    return self.pools[key]
            finally:
                self._create_pool_mutex.release()
                
    def connect(self, *args, **kw):
        """Activate a connection to the database.

        Connect to the database using this DBProxy's module and the given
        connect arguments.  If the arguments match an existing pool, the
        connection will be returned from the pool's current thread-local
        connection instance, or if there is no thread-local connection
        instance it will be checked out from the set of pooled connections.

        If the pool has no available connections and allows new connections
        to be created, a new database connection will be made.
        
        """

        return self.get_pool(*args, **kw).connect()

    def dispose(self, *args, **kw):
        """Dispose the pool referenced by the given connect arguments."""

        key = self._serialize(*args, **kw)
        try:
            del self.pools[key]
        except KeyError:
            pass

    def _serialize(self, *args, **kw):
        return pickle.dumps([args, kw])
