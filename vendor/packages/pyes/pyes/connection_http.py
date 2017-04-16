#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'

"""
Work taken from pycassa
"""
import logging
import random
import threading
import time
import urllib
from pyes.exceptions import NoServerAvailable
import urllib3
import urllib
from httplib import HTTPConnection
from fakettypes import *
import socket
import sys
__all__ = ['connect', 'connect_thread_local']

DEFAULT_SERVER = '127.0.0.1:9200'
#API_VERSION = VERSION.split('.')

log = logging.getLogger('pyes')

class TimeoutHttpConnectionPool(urllib3.HTTPConnectionPool):
    def _new_conn(self):
        """
        Return a fresh HTTPConnection with timeout passed
        """
        self.num_connections += 1
        log.info("Starting new HTTP connection (%d): %s" % (self.num_connections, self.host))
        if sys.version_info < (2, 6):
            return HTTPConnection(host=self.host, port=int(self.port))
        return HTTPConnection(host=self.host, port=self.port, timeout=self.timeout)
        

class ClientTransport(object):
    """Encapsulation of a client session."""

    def __init__(self, server, framed_transport, timeout, recycle):
        host, port = server.split(":")
        self.client = TimeoutHttpConnectionPool(host, port, timeout)
        setattr(self.client, "execute", self.execute)
        if recycle:
            self.recycle = time.time() + recycle + random.uniform(0, recycle * 0.1)
        else:
            self.recycle = None

    def execute(self, request):
        """
        Execute a request and return a response
        """
        uri = request.uri
        if request.parameters:
            uri += '?' + urllib.urlencode(request.parameters)
        response = self.client.urlopen(Method._VALUES_TO_NAMES[request.method], uri, body=request.body, headers=request.headers)    
        return RestResponse(status=response.status, body=response.data, headers=response.headers)

def connect(servers=None, framed_transport=False, timeout=None,
            retry_time=60, recycle=None, round_robin=None, max_retries=3):
    """
    Constructs a single ElastiSearch connection. Connects to a randomly chosen
    server on the list.

    If the connection fails, it will attempt to connect to each server on the
    list in turn until one succeeds. If it is unable to find an active server,
    it will throw a NoServerAvailable exception.

    Failing servers are kept on a separate list and eventually retried, no
    sooner than `retry_time` seconds after failure.

    Parameters
    ----------
    servers : [server]
              List of ES servers with format: "hostname:port"

              Default: ['127.0.0.1:9200']
    framed_transport: bool
              If True, use a TFramedTransport instead of a TBufferedTransport
    timeout: float
              Timeout in seconds (e.g. 0.5)

              Default: None (it will stall forever)
    retry_time: float
              Minimum time in seconds until a failed server is reinstated. (e.g. 0.5)

              Default: 60
    recycle: float
              Max time in seconds before an open connection is closed and returned to the pool.

              Default: None (Never recycle)
    max_retries: int
              Max retry time on connection down              

    round_robin: bool
              *DEPRECATED*

    Returns
    -------
    ES client
    """

    if servers is None:
        servers = [DEFAULT_SERVER]
    return ThreadLocalConnection(servers, framed_transport, timeout,
                                 retry_time, recycle, max_retries=max_retries)

connect_thread_local = connect


class ServerSet(object):
    """Automatically balanced set of servers.
       Manages a separate stack of failed servers, and automatic
       retrial."""

    def __init__(self, servers, retry_time=10):
        self._lock = threading.RLock()
        self._servers = list(servers)
        self._retry_time = retry_time
        self._dead = []
        
    def get(self):
        self._lock.acquire()
        try:
            if self._dead:
                ts, revived = self._dead.pop()
                if ts > time.time():  # Not yet, put it back
                    self._dead.append((ts, revived))
                else:
                    self._servers.append(revived)
                    log.info('Server %r reinstated into working pool', revived)
            if not self._servers:
                log.critical('No servers available')
                raise NoServerAvailable()
            return random.choice(self._servers)
        finally:
            self._lock.release()

    def mark_dead(self, server):
        self._lock.acquire()
        try:
            self._servers.remove(server)
            self._dead.insert(0, (time.time() + self._retry_time, server))
        finally:
            self._lock.release()


class ThreadLocalConnection(object):
    def __init__(self, servers, framed_transport=False, timeout=None,
                 retry_time=10, recycle=None, max_retries=3):
        self._servers = ServerSet(servers, retry_time)
        self._framed_transport = framed_transport #not used in http
        self._timeout = timeout
        self._recycle = recycle
        self._max_retries = max_retries
        self._local = threading.local()

    def __getattr__(self, attr):
        def _client_call(*args, **kwargs):

            for retry in xrange(self._max_retries+1):
                try:
                    conn = self._ensure_connection()
                    return getattr(conn.client, attr)(*args, **kwargs)
                except (socket.timeout, socket.error), exc:
                    log.exception('Client error: %s', exc)
                    self.close()

                    if retry < self._max_retries:
                        continue

                    raise urllib3.MaxRetryError

        setattr(self, attr, _client_call)
        return getattr(self, attr)

    def _ensure_connection(self):
        """Make certain we have a valid connection and return it."""
        conn = self.connect()
        if conn.recycle and conn.recycle < time.time():
            log.debug('Client session expired after %is. Recycling.', self._recycle)
            self.close()
            conn = self.connect()
        return conn

    def connect(self):
        """Create new connection unless we already have one."""
        if not getattr(self._local, 'conn', None):
            try:
                server = self._servers.get()
                log.debug('Connecting to %s', server)
                self._local.conn = ClientTransport(server, self._framed_transport,
                                                   self._timeout, self._recycle)
            except (socket.timeout, socket.error):
                log.warning('Connection to %s failed.', server)
                self._servers.mark_dead(server)
                return self.connect()
        return self._local.conn

    def close(self):
        """If a connection is open, close it."""
#        if self._local.conn:
#            self._local.conn.transport.close()
        self._local.conn = None
