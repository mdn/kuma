"""Strategies for creating new instances of Engine types.

These are semi-private implementation classes which provide the
underlying behavior for the "strategy" keyword argument available on
:func:`~sqlalchemy.engine.create_engine`.  Current available options are
``plain``, ``threadlocal``, and ``mock``.

New strategies can be added via new ``EngineStrategy`` classes.
"""

from operator import attrgetter

from sqlalchemy.engine import base, threadlocal, url
from sqlalchemy import util, exc
from sqlalchemy import pool as poollib

strategies = {}


class EngineStrategy(object):
    """An adaptor that processes input arguements and produces an Engine.

    Provides a ``create`` method that receives input arguments and
    produces an instance of base.Engine or a subclass.
    
    """

    def __init__(self):
        strategies[self.name] = self

    def create(self, *args, **kwargs):
        """Given arguments, returns a new Engine instance."""

        raise NotImplementedError()


class DefaultEngineStrategy(EngineStrategy):
    """Base class for built-in stratgies."""

    pool_threadlocal = False
    
    def create(self, name_or_url, **kwargs):
        # create url.URL object
        u = url.make_url(name_or_url)

        dialect_cls = u.get_dialect()

        dialect_args = {}
        # consume dialect arguments from kwargs
        for k in util.get_cls_kwargs(dialect_cls):
            if k in kwargs:
                dialect_args[k] = kwargs.pop(k)

        dbapi = kwargs.pop('module', None)
        if dbapi is None:
            dbapi_args = {}
            for k in util.get_func_kwargs(dialect_cls.dbapi):
                if k in kwargs:
                    dbapi_args[k] = kwargs.pop(k)
            dbapi = dialect_cls.dbapi(**dbapi_args)

        dialect_args['dbapi'] = dbapi

        # create dialect
        dialect = dialect_cls(**dialect_args)

        # assemble connection arguments
        (cargs, cparams) = dialect.create_connect_args(u)
        cparams.update(kwargs.pop('connect_args', {}))

        # look for existing pool or create
        pool = kwargs.pop('pool', None)
        if pool is None:
            def connect():
                try:
                    return dialect.connect(*cargs, **cparams)
                except Exception, e:
                    # Py3K
                    #raise exc.DBAPIError.instance(None, None, e) from e
                    # Py2K
                    import sys
                    raise exc.DBAPIError.instance(None, None, e), None, sys.exc_info()[2]
                    # end Py2K
                    
            creator = kwargs.pop('creator', connect)

            poolclass = (kwargs.pop('poolclass', None) or
                         getattr(dialect_cls, 'poolclass', poollib.QueuePool))
            pool_args = {}

            # consume pool arguments from kwargs, translating a few of
            # the arguments
            translate = {'logging_name': 'pool_logging_name',
                         'echo': 'echo_pool',
                         'timeout': 'pool_timeout',
                         'recycle': 'pool_recycle',
                         'use_threadlocal':'pool_threadlocal'}
            for k in util.get_cls_kwargs(poolclass):
                tk = translate.get(k, k)
                if tk in kwargs:
                    pool_args[k] = kwargs.pop(tk)
            pool_args.setdefault('use_threadlocal', self.pool_threadlocal)
            pool = poolclass(creator, **pool_args)
        else:
            if isinstance(pool, poollib._DBProxy):
                pool = pool.get_pool(*cargs, **cparams)
            else:
                pool = pool

        # create engine.
        engineclass = self.engine_cls
        engine_args = {}
        for k in util.get_cls_kwargs(engineclass):
            if k in kwargs:
                engine_args[k] = kwargs.pop(k)

        _initialize = kwargs.pop('_initialize', True)
        
        # all kwargs should be consumed
        if kwargs:
            raise TypeError(
                "Invalid argument(s) %s sent to create_engine(), "
                "using configuration %s/%s/%s.  Please check that the "
                "keyword arguments are appropriate for this combination "
                "of components." % (','.join("'%s'" % k for k in kwargs),
                                    dialect.__class__.__name__,
                                    pool.__class__.__name__,
                                    engineclass.__name__))
                                    
        engine = engineclass(pool, dialect, u, **engine_args)

        if _initialize:
            do_on_connect = dialect.on_connect()
            if do_on_connect:
                def on_connect(conn, rec):
                    conn = getattr(conn, '_sqla_unwrap', conn)
                    if conn is None:
                        return
                    do_on_connect(conn)
                    
                pool.add_listener({'first_connect': on_connect, 'connect':on_connect})
                    
            def first_connect(conn, rec):
                c = base.Connection(engine, connection=conn)
                dialect.initialize(c)
            pool.add_listener({'first_connect':first_connect})

        return engine


class PlainEngineStrategy(DefaultEngineStrategy):
    """Strategy for configuring a regular Engine."""

    name = 'plain'
    engine_cls = base.Engine
    
PlainEngineStrategy()


class ThreadLocalEngineStrategy(DefaultEngineStrategy):
    """Strategy for configuring an Engine with thredlocal behavior."""
    
    name = 'threadlocal'
    pool_threadlocal = True
    engine_cls = threadlocal.TLEngine

ThreadLocalEngineStrategy()


class MockEngineStrategy(EngineStrategy):
    """Strategy for configuring an Engine-like object with mocked execution.

    Produces a single mock Connectable object which dispatches
    statement execution to a passed-in function.
    
    """

    name = 'mock'
    
    def create(self, name_or_url, executor, **kwargs):
        # create url.URL object
        u = url.make_url(name_or_url)

        dialect_cls = u.get_dialect()

        dialect_args = {}
        # consume dialect arguments from kwargs
        for k in util.get_cls_kwargs(dialect_cls):
            if k in kwargs:
                dialect_args[k] = kwargs.pop(k)

        # create dialect
        dialect = dialect_cls(**dialect_args)

        return MockEngineStrategy.MockConnection(dialect, executor)

    class MockConnection(base.Connectable):
        def __init__(self, dialect, execute):
            self._dialect = dialect
            self.execute = execute

        engine = property(lambda s: s)
        dialect = property(attrgetter('_dialect'))
        name = property(lambda s: s._dialect.name)

        def contextual_connect(self, **kwargs):
            return self

        def compiler(self, statement, parameters, **kwargs):
            return self._dialect.compiler(
                statement, parameters, engine=self, **kwargs)

        def create(self, entity, **kwargs):
            kwargs['checkfirst'] = False
            from sqlalchemy.engine import ddl
            
            ddl.SchemaGenerator(self.dialect, self, **kwargs).traverse(entity)

        def drop(self, entity, **kwargs):
            kwargs['checkfirst'] = False
            from sqlalchemy.engine import ddl
            ddl.SchemaDropper(self.dialect, self, **kwargs).traverse(entity)

        def execute(self, object, *multiparams, **params):
            raise NotImplementedError()

MockEngineStrategy()
