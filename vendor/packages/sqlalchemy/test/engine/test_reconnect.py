from sqlalchemy.test.testing import eq_, assert_raises
import time
import weakref
from sqlalchemy import select, MetaData, Integer, String, pool
from sqlalchemy.test.schema import Table, Column
import sqlalchemy as tsa
from sqlalchemy.test import TestBase, testing, engines
from sqlalchemy.test.util import gc_collect
from sqlalchemy import exc

class MockDisconnect(Exception):
    pass

class MockDBAPI(object):
    def __init__(self):
        self.paramstyle = 'named'
        self.connections = weakref.WeakKeyDictionary()
    def connect(self, *args, **kwargs):
        return MockConnection(self)
    def shutdown(self):
        for c in self.connections:
            c.explode[0] = True
    Error = MockDisconnect

class MockConnection(object):
    def __init__(self, dbapi):
        dbapi.connections[self] = True
        self.explode = [False]
    def rollback(self):
        pass
    def commit(self):
        pass
    def cursor(self):
        return MockCursor(self)
    def close(self):
        pass

class MockCursor(object):
    def __init__(self, parent):
        self.explode = parent.explode
        self.description = ()
    def execute(self, *args, **kwargs):
        if self.explode[0]:
            raise MockDisconnect("Lost the DB connection")
        else:
            return
    def close(self):
        pass

db, dbapi = None, None
class MockReconnectTest(TestBase):
    def setup(self):
        global db, dbapi
        dbapi = MockDBAPI()

        db = tsa.create_engine(
                    'postgresql://foo:bar@localhost/test', 
                    module=dbapi, _initialize=False)

        # monkeypatch disconnect checker
        db.dialect.is_disconnect = lambda e: isinstance(e, MockDisconnect)

    def test_reconnect(self):
        """test that an 'is_disconnect' condition will invalidate the
        connection, and additionally dispose the previous connection
        pool and recreate."""

        pid = id(db.pool)

        # make a connection

        conn = db.connect()

        # connection works

        conn.execute(select([1]))

        # create a second connection within the pool, which we'll ensure
        # also goes away

        conn2 = db.connect()
        conn2.close()

        # two connections opened total now

        assert len(dbapi.connections) == 2

        # set it to fail

        dbapi.shutdown()
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError:
            pass

        # assert was invalidated

        assert not conn.closed
        assert conn.invalidated

        # close shouldnt break

        conn.close()
        assert id(db.pool) != pid

        # ensure all connections closed (pool was recycled)

        gc_collect()
        assert len(dbapi.connections) == 0
        conn = db.connect()
        conn.execute(select([1]))
        conn.close()
        assert len(dbapi.connections) == 1

    def test_invalidate_trans(self):
        conn = db.connect()
        trans = conn.begin()
        dbapi.shutdown()
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError:
            pass

        # assert was invalidated

        gc_collect()
        assert len(dbapi.connections) == 0
        assert not conn.closed
        assert conn.invalidated
        assert trans.is_active
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.InvalidRequestError, e:
            assert str(e) \
                == "Can't reconnect until invalid transaction is "\
                "rolled back"
        assert trans.is_active
        try:
            trans.commit()
            assert False
        except tsa.exc.InvalidRequestError, e:
            assert str(e) \
                == "Can't reconnect until invalid transaction is "\
                "rolled back"
        assert trans.is_active
        trans.rollback()
        assert not trans.is_active
        conn.execute(select([1]))
        assert not conn.invalidated
        assert len(dbapi.connections) == 1

    def test_conn_reusable(self):
        conn = db.connect()

        conn.execute(select([1]))

        assert len(dbapi.connections) == 1

        dbapi.shutdown()

        # raises error
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError:
            pass

        assert not conn.closed
        assert conn.invalidated

        # ensure all connections closed (pool was recycled)
        gc_collect()
        assert len(dbapi.connections) == 0

        # test reconnects
        conn.execute(select([1]))
        assert not conn.invalidated
        assert len(dbapi.connections) == 1

class CursorErrTest(TestBase):

    def setup(self):
        global db, dbapi
        
        class MDBAPI(MockDBAPI):
            def connect(self, *args, **kwargs):
                return MConn(self)
            
        class MConn(MockConnection):
            def cursor(self):
                return MCursor(self)

        class MCursor(MockCursor):
            def close(self):
                raise Exception("explode")

        dbapi = MDBAPI()

        db = tsa.create_engine(
                    'postgresql://foo:bar@localhost/test', 
                    module=dbapi, _initialize=False)
    
    def test_cursor_explode(self):
        conn = db.connect()
        result = conn.execute("select foo")
        result.close()
        conn.close()
    
    def teardown(self):
        db.dispose()
        
engine = None
class RealReconnectTest(TestBase):
    def setup(self):
        global engine
        engine = engines.reconnecting_engine()

    def teardown(self):
        engine.dispose()

    def test_reconnect(self):
        conn = engine.connect()

        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.closed

        engine.test_shutdown()

        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError, e:
            if not e.connection_invalidated:
                raise

        assert not conn.closed
        assert conn.invalidated

        assert conn.invalidated
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.invalidated

        # one more time
        engine.test_shutdown()
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError, e:
            if not e.connection_invalidated:
                raise
        assert conn.invalidated
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.invalidated

        conn.close()
    
    def test_invalidate_twice(self):
        conn = engine.connect()
        conn.invalidate()
        conn.invalidate()
    
    def test_explode_in_initializer(self):
        engine = engines.testing_engine()
        def broken_initialize(connection):
            connection.execute("select fake_stuff from _fake_table")
            
        engine.dialect.initialize = broken_initialize
        
        # raises a DBAPIError, not an AttributeError
        assert_raises(exc.DBAPIError, engine.connect)

        # dispose connections so we get a new one on
        # next go
        engine.dispose()

        p1 = engine.pool
        
        def is_disconnect(e):
            return True
            
        engine.dialect.is_disconnect = is_disconnect

        # invalidate() also doesn't screw up
        assert_raises(exc.DBAPIError, engine.connect)
        
        # pool was recreated
        assert engine.pool is not p1
        
    def test_null_pool(self):
        engine = \
            engines.reconnecting_engine(options=dict(poolclass=pool.NullPool))
        conn = engine.connect()
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.closed
        engine.test_shutdown()
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError, e:
            if not e.connection_invalidated:
                raise
        assert not conn.closed
        assert conn.invalidated
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.invalidated
        
    def test_close(self):
        conn = engine.connect()
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.closed

        engine.test_shutdown()

        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError, e:
            if not e.connection_invalidated:
                raise

        conn.close()
        conn = engine.connect()
        eq_(conn.execute(select([1])).scalar(), 1)

    def test_with_transaction(self):
        conn = engine.connect()
        trans = conn.begin()
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.closed
        engine.test_shutdown()
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.DBAPIError, e:
            if not e.connection_invalidated:
                raise
        assert not conn.closed
        assert conn.invalidated
        assert trans.is_active
        try:
            conn.execute(select([1]))
            assert False
        except tsa.exc.InvalidRequestError, e:
            assert str(e) \
                == "Can't reconnect until invalid transaction is "\
                "rolled back"
        assert trans.is_active
        try:
            trans.commit()
            assert False
        except tsa.exc.InvalidRequestError, e:
            assert str(e) \
                == "Can't reconnect until invalid transaction is "\
                "rolled back"
        assert trans.is_active
        trans.rollback()
        assert not trans.is_active
        assert conn.invalidated
        eq_(conn.execute(select([1])).scalar(), 1)
        assert not conn.invalidated

class RecycleTest(TestBase):

    def test_basic(self):
        for threadlocal in False, True:
            engine = engines.reconnecting_engine(options={'pool_recycle'
                    : 1, 'pool_threadlocal': threadlocal})
            conn = engine.contextual_connect()
            eq_(conn.execute(select([1])).scalar(), 1)
            conn.close()
            engine.test_shutdown()
            time.sleep(2)
            conn = engine.contextual_connect()
            eq_(conn.execute(select([1])).scalar(), 1)
            conn.close()
    
meta, table, engine = None, None, None
class InvalidateDuringResultTest(TestBase):
    def setup(self):
        global meta, table, engine
        engine = engines.reconnecting_engine()
        meta = MetaData(engine)
        table = Table('sometable', meta,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)))
        meta.create_all()
        table.insert().execute(
            [{'id':i, 'name':'row %d' % i} for i in range(1, 100)]
        )

    def teardown(self):
        meta.drop_all()
        engine.dispose()

    @testing.fails_on('+mysqldb',
                      "Buffers the result set and doesn't check for "
                      "connection close")
    @testing.fails_on('+pg8000',
                      "Buffers the result set and doesn't check for "
                      "connection close")
    def test_invalidate_on_results(self):
        conn = engine.connect()
        result = conn.execute('select * from sometable')
        for x in xrange(20):
            result.fetchone()
        engine.test_shutdown()
        try:
            print 'ghost result: %r' % result.fetchone()
            assert False
        except tsa.exc.DBAPIError, e:
            if not e.connection_invalidated:
                raise
        assert conn.invalidated
