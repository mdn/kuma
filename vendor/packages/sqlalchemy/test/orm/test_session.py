from sqlalchemy.test.testing import eq_, assert_raises, \
    assert_raises_message
from sqlalchemy.test.util import gc_collect
import inspect
import pickle
from sqlalchemy.orm import create_session, sessionmaker, attributes, \
    make_transient, Session
from sqlalchemy.orm.attributes import instance_state
import sqlalchemy as sa
from sqlalchemy.test import engines, testing, config
from sqlalchemy import Integer, String, Sequence
from sqlalchemy.test.schema import Table, Column
from sqlalchemy.orm import mapper, relationship, backref, joinedload, \
    exc as orm_exc, object_session
from sqlalchemy.test.testing import eq_
from test.engine import _base as engine_base
from test.orm import _base, _fixtures


class SessionTest(_fixtures.FixtureTest):
    run_inserts = None

    @testing.resolve_artifact_names
    def test_no_close_on_flush(self):
        """Flush() doesn't close a connection the session didn't open"""
        c = testing.db.connect()
        c.execute("select * from users")

        mapper(User, users)
        s = create_session(bind=c)
        s.add(User(name='first'))
        s.flush()
        c.execute("select * from users")

    @testing.resolve_artifact_names
    def test_close(self):
        """close() doesn't close a connection the session didn't open"""
        c = testing.db.connect()
        c.execute("select * from users")

        mapper(User, users)
        s = create_session(bind=c)
        s.add(User(name='first'))
        s.flush()
        c.execute("select * from users")
        s.close()
        c.execute("select * from users")

    @testing.resolve_artifact_names
    def test_no_close_transaction_on_flulsh(self):
        c = testing.db.connect()
        try:
            mapper(User, users)
            s = create_session(bind=c)
            s.begin()
            tran = s.transaction
            s.add(User(name='first'))
            s.flush()
            c.execute("select * from users")
            u = User(name='two')
            s.add(u)
            s.flush()
            u = User(name='third')
            s.add(u)
            s.flush()
            assert s.transaction is tran
            tran.close()
        finally:
            c.close()

    @testing.resolve_artifact_names
    def test_object_session_raises(self):
        assert_raises(
            orm_exc.UnmappedInstanceError,
            object_session, 
            object()
        )

        assert_raises(
            orm_exc.UnmappedInstanceError,
            object_session, 
            User()
        )
        
    @testing.requires.sequences
    def test_sequence_execute(self):
        seq = Sequence("some_sequence")
        seq.create(testing.db)
        try:
            sess = create_session(bind=testing.db)
            eq_(sess.execute(seq), 1)
        finally:
            seq.drop(testing.db)
        
        
    @testing.resolve_artifact_names
    def test_expunge_cascade(self):
        mapper(Address, addresses)
        mapper(User, users, properties={
            'addresses':relationship(Address,
                                 backref=backref("user", cascade="all"),
                                 cascade="all")})

        _fixtures.run_inserts_for(users)
        _fixtures.run_inserts_for(addresses)

        session = create_session()
        u = session.query(User).filter_by(id=7).one()

        # get everything to load in both directions
        print [a.user for a in u.addresses]

        # then see if expunge fails
        session.expunge(u)

        assert sa.orm.object_session(u) is None
        assert sa.orm.attributes.instance_state(u).session_id is None
        for a in u.addresses:
            assert sa.orm.object_session(a) is None
            assert sa.orm.attributes.instance_state(a).session_id is None

    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_mapped_binds(self):

        # ensure tables are unbound
        m2 = sa.MetaData()
        users_unbound =users.tometadata(m2)
        addresses_unbound = addresses.tometadata(m2)

        mapper(Address, addresses_unbound)
        mapper(User, users_unbound, properties={
            'addresses':relationship(Address,
                                 backref=backref("user", cascade="all"),
                                 cascade="all")})

        Session = sessionmaker(binds={User: self.metadata.bind,
                                      Address: self.metadata.bind})
        sess = Session()

        u1 = User(id=1, name='ed')
        sess.add(u1)
        eq_(sess.query(User).filter(User.id==1).all(),
            [User(id=1, name='ed')])

        # test expression binding

        sess.execute(users_unbound.insert(), params=dict(id=2,
                     name='jack'))
        eq_(sess.execute(users_unbound.select(users_unbound.c.id
            == 2)).fetchall(), [(2, 'jack')])

        eq_(sess.execute(users_unbound.select(User.id == 2)).fetchall(),
            [(2, 'jack')])

        sess.execute(users_unbound.delete())
        eq_(sess.execute(users_unbound.select()).fetchall(), [])
        
        sess.close()

    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_table_binds(self):

        # ensure tables are unbound
        m2 = sa.MetaData()
        users_unbound =users.tometadata(m2)
        addresses_unbound = addresses.tometadata(m2)

        mapper(Address, addresses_unbound)
        mapper(User, users_unbound, properties={
            'addresses':relationship(Address,
                                 backref=backref("user", cascade="all"),
                                 cascade="all")})

        Session = sessionmaker(binds={users_unbound: self.metadata.bind,
                                      addresses_unbound: self.metadata.bind})
        sess = Session()

        u1 = User(id=1, name='ed')
        sess.add(u1)
        eq_(sess.query(User).filter(User.id==1).all(),
            [User(id=1, name='ed')])

        sess.execute(users_unbound.insert(), params=dict(id=2, name='jack'))

        eq_(sess.execute(users_unbound.select(users_unbound.c.id
            == 2)).fetchall(), [(2, 'jack')])

        eq_(sess.execute(users_unbound.select(User.id == 2)).fetchall(),
            [(2, 'jack')])

        sess.execute(users_unbound.delete())
        eq_(sess.execute(users_unbound.select()).fetchall(), [])

        sess.close()

    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_bind_from_metadata(self):
        mapper(User, users)

        session = create_session()
        session.execute(users.insert(), dict(name='Johnny'))

        assert len(session.query(User).filter_by(name='Johnny').all()) == 1

        session.execute(users.delete())

        assert len(session.query(User).filter_by(name='Johnny').all()) == 0
        session.close()

    @testing.requires.independent_connections
    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_transaction(self):
        mapper(User, users)
        conn1 = testing.db.connect()
        conn2 = testing.db.connect()

        sess = create_session(autocommit=False, bind=conn1)
        u = User(name='x')
        sess.add(u)
        sess.flush()
        assert conn1.execute("select count(1) from users").scalar() == 1
        assert conn2.execute("select count(1) from users").scalar() == 0
        sess.commit()
        assert conn1.execute("select count(1) from users").scalar() == 1

        assert testing.db.connect().execute('select count(1) from users'
                ).scalar() == 1
        sess.close()

    @testing.requires.independent_connections
    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_autoflush(self):
        bind = self.metadata.bind
        mapper(User, users)
        conn1 = bind.connect()
        conn2 = bind.connect()

        sess = create_session(bind=conn1, autocommit=False, autoflush=True)
        u = User()
        u.name='ed'
        sess.add(u)
        u2 = sess.query(User).filter_by(name='ed').one()
        assert u2 is u
        eq_(conn1.execute("select count(1) from users").scalar(), 1)
        eq_(conn2.execute("select count(1) from users").scalar(), 0)
        sess.commit()
        eq_(conn1.execute("select count(1) from users").scalar(), 1)
        eq_(bind.connect().execute("select count(1) from users").scalar(), 1)
        sess.close()

    @testing.resolve_artifact_names
    def test_make_transient(self):
        mapper(User, users)
        sess = create_session()
        sess.add(User(name='test'))
        sess.flush()
        
        u1 = sess.query(User).first()
        make_transient(u1)
        assert u1 not in sess
        sess.add(u1)
        assert u1 in sess.new

        u1 = sess.query(User).first()
        sess.expunge(u1)
        make_transient(u1)
        sess.add(u1)
        assert u1 in sess.new
        
        # test expired attributes 
        # get unexpired
        u1 = sess.query(User).first()
        sess.expire(u1)
        make_transient(u1)
        assert u1.id is None
        assert u1.name is None

        # works twice
        make_transient(u1)
        
        sess.close()
        
        u1.name = 'test2'
        sess.add(u1)
        sess.flush()
        assert u1 in sess
        sess.delete(u1)
        sess.flush()
        assert u1 not in sess
        
        assert_raises(sa.exc.InvalidRequestError, sess.add, u1)
        make_transient(u1)
        sess.add(u1)
        sess.flush()
        assert u1 in sess

    @testing.resolve_artifact_names
    def test_deleted_flag(self):
        mapper(User, users)
        
        sess = sessionmaker()()
        
        u1 = User(name='u1')
        sess.add(u1)
        sess.commit()
        
        sess.delete(u1)
        sess.flush()
        assert u1 not in sess
        assert_raises(sa.exc.InvalidRequestError, sess.add, u1)
        sess.rollback()
        assert u1 in sess
        
        sess.delete(u1)
        sess.commit()
        assert u1 not in sess
        assert_raises(sa.exc.InvalidRequestError, sess.add, u1)
        
        make_transient(u1)
        sess.add(u1)
        sess.commit()
        
        eq_(sess.query(User).count(), 1)
        
    @testing.resolve_artifact_names
    def test_autoflush_expressions(self):
        """test that an expression which is dependent on object state is 
        evaluated after the session autoflushes.   This is the lambda
        inside of strategies.py lazy_clause.
        
        """
        mapper(User, users, properties={
            'addresses':relationship(Address, backref="user")})
        mapper(Address, addresses)

        sess = create_session(autoflush=True, autocommit=False)
        u = User(name='ed', addresses=[Address(email_address='foo')])
        sess.add(u)
        eq_(sess.query(Address).filter(Address.user==u).one(),
            Address(email_address='foo'))

        # still works after "u" is garbage collected
        sess.commit()
        sess.close()
        u = sess.query(User).get(u.id)
        q = sess.query(Address).filter(Address.user==u)
        del u
        gc_collect()
        eq_(q.one(), Address(email_address='foo'))



    @testing.requires.independent_connections
    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_autoflush_unbound(self):
        mapper(User, users)
        try:
            sess = create_session(autocommit=False, autoflush=True)
            u = User()
            u.name = 'ed'
            sess.add(u)
            u2 = sess.query(User).filter_by(name='ed').one()
            assert u2 is u
            assert sess.execute('select count(1) from users',
                                mapper=User).scalar() == 1
            assert testing.db.connect().execute('select count(1) from '
                    'users').scalar() == 0
            sess.commit()
            assert sess.execute('select count(1) from users',
                                mapper=User).scalar() == 1
            assert testing.db.connect().execute('select count(1) from '
                    'users').scalar() == 1
            sess.close()
        except:
            sess.rollback()
            raise

    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_autoflush_2(self):
        mapper(User, users)
        conn1 = testing.db.connect()
        conn2 = testing.db.connect()
        sess = create_session(bind=conn1, autocommit=False,
                              autoflush=True)
        u = User()
        u.name = 'ed'
        sess.add(u)
        sess.commit()
        assert conn1.execute('select count(1) from users').scalar() == 1
        assert testing.db.connect().execute('select count(1) from users'
                ).scalar() == 1
        sess.commit()

    @testing.resolve_artifact_names
    def test_autoflush_rollback(self):
        mapper(Address, addresses)
        mapper(User, users, properties={
            'addresses':relationship(Address)})

        _fixtures.run_inserts_for(users)
        _fixtures.run_inserts_for(addresses)

        sess = create_session(autocommit=False, autoflush=True)
        u = sess.query(User).get(8)
        newad = Address(email_address='a new address')
        u.addresses.append(newad)
        u.name = 'some new name'
        assert u.name == 'some new name'
        assert len(u.addresses) == 4
        assert newad in u.addresses
        sess.rollback()
        assert u.name == 'ed'
        assert len(u.addresses) == 3

        assert newad not in u.addresses
        # pending objects dont get expired
        assert newad.email_address == 'a new address'
    
    @testing.resolve_artifact_names
    def test_autocommit_doesnt_raise_on_pending(self):
        mapper(User, users)
        session = create_session(autocommit=True)

        session.add(User(name='ed'))

        session.begin()
        session.flush()
        session.commit()
    
    def test_active_flag(self):
        sess = create_session(bind=config.db, autocommit=True)
        assert not sess.is_active
        sess.begin()
        assert sess.is_active
        sess.rollback()
        assert not sess.is_active
        
    @testing.resolve_artifact_names
    def test_textual_execute(self):
        """test that Session.execute() converts to text()"""

        sess = create_session(bind=self.metadata.bind)
        users.insert().execute(id=7, name='jack')

        # use :bindparam style
        eq_(sess.execute("select * from users where id=:id",
                         {'id':7}).fetchall(),
            [(7, u'jack')])


        # use :bindparam style
        eq_(sess.scalar("select id from users where id=:id",
                         {'id':7}),
            7)

    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_subtransaction_on_external(self):
        mapper(User, users)
        conn = testing.db.connect()
        trans = conn.begin()
        sess = create_session(bind=conn, autocommit=False, autoflush=True)
        sess.begin(subtransactions=True)
        u = User(name='ed')
        sess.add(u)
        sess.flush()
        sess.commit() # commit does nothing
        trans.rollback() # rolls back
        assert len(sess.query(User).all()) == 0
        sess.close()

    @testing.requires.savepoints
    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_external_nested_transaction(self):
        mapper(User, users)
        try:
            conn = testing.db.connect()
            trans = conn.begin()
            sess = create_session(bind=conn, autocommit=False, autoflush=True)
            u1 = User(name='u1')
            sess.add(u1)
            sess.flush()

            sess.begin_nested()
            u2 = User(name='u2')
            sess.add(u2)
            sess.flush()
            sess.rollback()

            trans.commit()
            assert len(sess.query(User).all()) == 1
        except:
            conn.close()
            raise

    @testing.requires.savepoints
    @testing.resolve_artifact_names
    def test_heavy_nesting(self):
        session = create_session(bind=testing.db)
        session.begin()
        session.connection().execute(users.insert().values(name='user1'
                ))
        session.begin(subtransactions=True)
        session.begin_nested()
        session.connection().execute(users.insert().values(name='user2'
                ))
        assert session.connection().execute('select count(1) from users'
                ).scalar() == 2
        session.rollback()
        assert session.connection().execute('select count(1) from users'
                ).scalar() == 1
        session.connection().execute(users.insert().values(name='user3'
                ))
        session.commit()
        assert session.connection().execute('select count(1) from users'
                ).scalar() == 2

    @testing.fails_on('sqlite', 'FIXME: unknown')
    @testing.resolve_artifact_names
    def test_transactions_isolated(self):
        mapper(User, users)
        users.delete().execute()
        
        s1 = create_session(bind=testing.db, autocommit=False)
        s2 = create_session(bind=testing.db, autocommit=False)
        u1 = User(name='u1')
        s1.add(u1)
        s1.flush()
        
        assert s2.query(User).all() == []
        
    @testing.requires.two_phase_transactions
    @testing.resolve_artifact_names
    def test_twophase(self):
        # TODO: mock up a failure condition here
        # to ensure a rollback succeeds
        mapper(User, users)
        mapper(Address, addresses)

        engine2 = engines.testing_engine()
        sess = create_session(autocommit=True, autoflush=False, twophase=True)
        sess.bind_mapper(User, testing.db)
        sess.bind_mapper(Address, engine2)
        sess.begin()
        u1 = User(name='u1')
        a1 = Address(email_address='u1@e')
        sess.add_all((u1, a1))
        sess.commit()
        sess.close()
        engine2.dispose()
        assert users.count().scalar() == 1
        assert addresses.count().scalar() == 1

    @testing.resolve_artifact_names
    def test_subtransaction_on_noautocommit(self):
        mapper(User, users)
        sess = create_session(autocommit=False, autoflush=True)
        sess.begin(subtransactions=True)
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        sess.commit() # commit does nothing
        sess.rollback() # rolls back
        assert len(sess.query(User).all()) == 0
        sess.close()

    @testing.requires.savepoints
    @testing.resolve_artifact_names
    def test_nested_transaction(self):
        mapper(User, users)
        sess = create_session()
        sess.begin()

        u = User(name='u1')
        sess.add(u)
        sess.flush()

        sess.begin_nested()  # nested transaction

        u2 = User(name='u2')
        sess.add(u2)
        sess.flush()

        sess.rollback()

        sess.commit()
        assert len(sess.query(User).all()) == 1
        sess.close()

    @testing.requires.savepoints
    @testing.resolve_artifact_names
    def test_nested_autotrans(self):
        mapper(User, users)
        sess = create_session(autocommit=False)
        u = User(name='u1')
        sess.add(u)
        sess.flush()

        sess.begin_nested()  # nested transaction

        u2 = User(name='u2')
        sess.add(u2)
        sess.flush()

        sess.rollback()

        sess.commit()
        assert len(sess.query(User).all()) == 1
        sess.close()

    @testing.requires.savepoints
    @testing.resolve_artifact_names
    def test_nested_transaction_connection_add(self):
        mapper(User, users)

        sess = create_session(autocommit=True)

        sess.begin()
        sess.begin_nested()

        u1 = User(name='u1')
        sess.add(u1)
        sess.flush()

        sess.rollback()

        u2 = User(name='u2')
        sess.add(u2)

        sess.commit()

        eq_(set(sess.query(User).all()), set([u2]))

        sess.begin()
        sess.begin_nested()

        u3 = User(name='u3')
        sess.add(u3)
        sess.commit() # commit the nested transaction
        sess.rollback()

        eq_(set(sess.query(User).all()), set([u2]))

        sess.close()

    @testing.requires.savepoints
    @testing.resolve_artifact_names
    def test_mixed_transaction_control(self):
        mapper(User, users)

        sess = create_session(autocommit=True)

        sess.begin()
        sess.begin_nested()
        transaction = sess.begin(subtransactions=True)

        sess.add(User(name='u1'))

        transaction.commit()
        sess.commit()
        sess.commit()

        sess.close()

        eq_(len(sess.query(User).all()), 1)

        t1 = sess.begin()
        t2 = sess.begin_nested()

        sess.add(User(name='u2'))

        t2.commit()
        assert sess.transaction is t1

        sess.close()

    @testing.requires.savepoints
    @testing.resolve_artifact_names
    def test_mixed_transaction_close(self):
        mapper(User, users)

        sess = create_session(autocommit=False)

        sess.begin_nested()

        sess.add(User(name='u1'))
        sess.flush()

        sess.close()

        sess.add(User(name='u2'))
        sess.commit()

        sess.close()

        eq_(len(sess.query(User).all()), 1)

    @testing.resolve_artifact_names
    def test_error_on_using_inactive_session(self):
        mapper(User, users)
        sess = create_session(autocommit=True)
        sess.begin()
        sess.begin(subtransactions=True)
        sess.add(User(name='u1'))
        sess.flush()
        sess.rollback()
        assert_raises_message(sa.exc.InvalidRequestError,
                              'inactive due to a rollback in a '
                              'subtransaction', sess.begin,
                              subtransactions=True)
        sess.close()

    @testing.resolve_artifact_names
    def test_no_autocommit_with_explicit_commit(self):
        mapper(User, users)
        session = create_session(autocommit=False)
        session.add(User(name='ed'))
        session.transaction.commit()
        assert session.transaction is not None, \
            'autocommit=False should start a new transaction'

    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_bound_connection(self):
        mapper(User, users)
        c = testing.db.connect()
        sess = create_session(bind=c)
        sess.begin()
        transaction = sess.transaction
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        assert transaction._connection_for_bind(testing.db) \
            is transaction._connection_for_bind(c) is c

        assert_raises_message(sa.exc.InvalidRequestError,
                              'Session already has a Connection '
                              'associated',
                              transaction._connection_for_bind,
                              testing.db.connect())
        transaction.rollback()
        assert len(sess.query(User).all()) == 0
        sess.close()

    @testing.resolve_artifact_names
    def test_bound_connection_transactional(self):
        mapper(User, users)
        c = testing.db.connect()

        sess = create_session(bind=c, autocommit=False)
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        sess.close()
        assert not c.in_transaction()
        assert c.scalar("select count(1) from users") == 0

        sess = create_session(bind=c, autocommit=False)
        u = User(name='u2')
        sess.add(u)
        sess.flush()
        sess.commit()
        assert not c.in_transaction()
        assert c.scalar("select count(1) from users") == 1
        c.execute("delete from users")
        assert c.scalar("select count(1) from users") == 0

        c = testing.db.connect()

        trans = c.begin()
        sess = create_session(bind=c, autocommit=True)
        u = User(name='u3')
        sess.add(u)
        sess.flush()
        assert c.in_transaction()
        trans.commit()
        assert not c.in_transaction()
        assert c.scalar("select count(1) from users") == 1


    @engines.close_open_connections
    @testing.resolve_artifact_names
    def test_add_delete(self):

        s = create_session()
        mapper(User, users, properties={
            'addresses':relationship(Address, cascade="all, delete")
        })
        mapper(Address, addresses)

        user = User(name='u1')

        assert_raises_message(sa.exc.InvalidRequestError,
                              'is not persisted', s.delete, user)

        s.add(user)
        s.flush()
        user = s.query(User).one()
        s.expunge(user)
        assert user not in s

        # modify outside of session, assert changes remain/get saved
        user.name = "fred"
        s.add(user)
        assert user in s
        assert user in s.dirty
        s.flush()
        s.expunge_all()
        assert s.query(User).count() == 1
        user = s.query(User).one()
        assert user.name == 'fred'

        # ensure its not dirty if no changes occur
        s.expunge_all()
        assert user not in s
        s.add(user)
        assert user in s
        assert user not in s.dirty

        s2 = create_session()
        assert_raises_message(sa.exc.InvalidRequestError,
                              'is already attached to session',
                              s2.delete, user)
        u2 = s2.query(User).get(user.id)
        assert_raises_message(sa.exc.InvalidRequestError,
                              'another instance with key', s.delete, u2)
        s.expire(user)
        s.expunge(user)
        assert user not in s
        s.delete(user)
        assert user in s
        
        s.flush()
        assert user not in s
        assert s.query(User).count() == 0

    @testing.resolve_artifact_names
    def test_is_modified(self):
        s = create_session()

        mapper(User, users, properties={'addresses':relationship(Address)})
        mapper(Address, addresses)

        # save user
        u = User(name='fred')
        s.add(u)
        s.flush()
        s.expunge_all()

        user = s.query(User).one()
        assert user not in s.dirty
        assert not s.is_modified(user)
        user.name = 'fred'
        assert user in s.dirty
        assert not s.is_modified(user)
        user.name = 'ed'
        assert user in s.dirty
        assert s.is_modified(user)
        s.flush()
        assert user not in s.dirty
        assert not s.is_modified(user)

        a = Address()
        user.addresses.append(a)
        assert user in s.dirty
        assert s.is_modified(user)
        assert not s.is_modified(user, include_collections=False)

    @testing.resolve_artifact_names
    def test_is_modified_syn(self):
        s = sessionmaker()()

        mapper(User, users, properties={'uname':sa.orm.synonym('name')})
        u = User(uname='fred')
        assert s.is_modified(u)
        s.add(u)
        s.commit()
        assert not s.is_modified(u)

    @testing.resolve_artifact_names
    def test_weak_ref(self):
        """test the weak-referencing identity map, which strongly-
        references modified items."""

        s = create_session()
        mapper(User, users)

        s.add(User(name='ed'))
        s.flush()
        assert not s.dirty

        user = s.query(User).one()
        del user
        gc_collect()
        assert len(s.identity_map) == 0

        user = s.query(User).one()
        user.name = 'fred'
        del user
        gc_collect()
        assert len(s.identity_map) == 1
        assert len(s.dirty) == 1
        assert None not in s.dirty
        s.flush()
        gc_collect()
        assert not s.dirty
        assert not s.identity_map

        user = s.query(User).one()
        assert user.name == 'fred'
        assert s.identity_map

    @testing.resolve_artifact_names
    def test_weak_ref_pickled(self):
        s = create_session()
        mapper(User, users)

        s.add(User(name='ed'))
        s.flush()
        assert not s.dirty

        user = s.query(User).one()
        user.name = 'fred'
        s.expunge(user)

        u2 = pickle.loads(pickle.dumps(user))

        del user
        s.add(u2)
        
        del u2
        gc_collect()
        
        assert len(s.identity_map) == 1
        assert len(s.dirty) == 1
        assert None not in s.dirty
        s.flush()
        gc_collect()
        assert not s.dirty
        
        assert not s.identity_map

    @testing.resolve_artifact_names
    def test_identity_conflict(self):
        mapper(User, users)
        for s in (
            create_session(),
            create_session(weak_identity_map=False),
        ):
            users.delete().execute()
            u1 = User(name="ed")
            s.add(u1)
            s.flush()
            s.expunge(u1)
            u2 = s.query(User).first()
            s.expunge(u2)
            s.identity_map.add(sa.orm.attributes.instance_state(u1))

            assert_raises(AssertionError, s.identity_map.add,
                          sa.orm.attributes.instance_state(u2))
        
        
    @testing.resolve_artifact_names
    def test_weakref_with_cycles_o2m(self):
        s = sessionmaker()()
        mapper(User, users, properties={
            "addresses":relationship(Address, backref="user")
        })
        mapper(Address, addresses)
        s.add(User(name="ed", addresses=[Address(email_address="ed1")]))
        s.commit()
        
        user = s.query(User).options(joinedload(User.addresses)).one()
        user.addresses[0].user # lazyload
        eq_(user, User(name="ed", addresses=[Address(email_address="ed1")]))
        
        del user
        gc_collect()
        assert len(s.identity_map) == 0

        user = s.query(User).options(joinedload(User.addresses)).one()
        user.addresses[0].email_address='ed2'
        user.addresses[0].user # lazyload
        del user
        gc_collect()
        assert len(s.identity_map) == 2
        
        s.commit()
        user = s.query(User).options(joinedload(User.addresses)).one()
        eq_(user, User(name="ed", addresses=[Address(email_address="ed2")]))
        
    @testing.resolve_artifact_names
    def test_weakref_with_cycles_o2o(self):
        s = sessionmaker()()
        mapper(User, users, properties={
            "address":relationship(Address, backref="user", uselist=False)
        })
        mapper(Address, addresses)
        s.add(User(name="ed", address=Address(email_address="ed1")))
        s.commit()

        user = s.query(User).options(joinedload(User.address)).one()
        user.address.user
        eq_(user, User(name="ed", address=Address(email_address="ed1")))

        del user
        gc_collect()
        assert len(s.identity_map) == 0

        user = s.query(User).options(joinedload(User.address)).one()
        user.address.email_address='ed2'
        user.address.user # lazyload

        del user
        gc_collect()
        assert len(s.identity_map) == 2
        
        s.commit()
        user = s.query(User).options(joinedload(User.address)).one()
        eq_(user, User(name="ed", address=Address(email_address="ed2")))
    
    @testing.resolve_artifact_names
    def test_strong_ref(self):
        s = create_session(weak_identity_map=False)
        mapper(User, users)

        # save user
        s.add(User(name='u1'))
        s.flush()
        user = s.query(User).one()
        user = None
        print s.identity_map
        gc_collect()
        assert len(s.identity_map) == 1

        user = s.query(User).one()
        assert not s.identity_map._modified
        user.name = 'u2'
        assert s.identity_map._modified
        s.flush()
        eq_(users.select().execute().fetchall(), [(user.id, 'u2')])
        
    @testing.fails_on('+zxjdbc', 'http://www.sqlalchemy.org/trac/ticket/1473')
    @testing.resolve_artifact_names
    def test_prune(self):
        s = create_session(weak_identity_map=False)
        mapper(User, users)

        for o in [User(name='u%s' % x) for x in xrange(10)]:
            s.add(o)
        # o is still live after this loop...

        self.assert_(len(s.identity_map) == 0)
        self.assert_(s.prune() == 0)
        s.flush()
        gc_collect()
        self.assert_(s.prune() == 9)
        self.assert_(len(s.identity_map) == 1)

        id = o.id
        del o
        self.assert_(s.prune() == 1)
        self.assert_(len(s.identity_map) == 0)

        u = s.query(User).get(id)
        self.assert_(s.prune() == 0)
        self.assert_(len(s.identity_map) == 1)
        u.name = 'squiznart'
        del u
        self.assert_(s.prune() == 0)
        self.assert_(len(s.identity_map) == 1)
        s.flush()
        self.assert_(s.prune() == 1)
        self.assert_(len(s.identity_map) == 0)

        s.add(User(name='x'))
        self.assert_(s.prune() == 0)
        self.assert_(len(s.identity_map) == 0)
        s.flush()
        self.assert_(len(s.identity_map) == 1)
        self.assert_(s.prune() == 1)
        self.assert_(len(s.identity_map) == 0)

        u = s.query(User).get(id)
        s.delete(u)
        del u
        self.assert_(s.prune() == 0)
        self.assert_(len(s.identity_map) == 1)
        s.flush()
        self.assert_(s.prune() == 0)
        self.assert_(len(s.identity_map) == 0)

    @testing.resolve_artifact_names
    def test_no_save_cascade_1(self):
        mapper(Address, addresses)
        mapper(User, users, properties=dict(
            addresses=relationship(Address, cascade="none", backref="user")))
        s = create_session()

        u = User(name='u1')
        s.add(u)
        a = Address(email_address='u1@e')
        u.addresses.append(a)
        assert u in s
        assert a not in s
        s.flush()
        print "\n".join([repr(x.__dict__) for x in s])
        s.expunge_all()
        assert s.query(User).one().id == u.id
        assert s.query(Address).first() is None

    @testing.resolve_artifact_names
    def test_no_save_cascade_2(self):
        mapper(Address, addresses)
        mapper(User, users, properties=dict(
            addresses=relationship(Address,
                               cascade="all",
                               backref=backref("user", cascade="none"))))

        s = create_session()
        u = User(name='u1')
        a = Address(email_address='u1@e')
        a.user = u
        s.add(a)
        assert u not in s
        assert a in s
        s.flush()
        s.expunge_all()
        assert s.query(Address).one().id == a.id
        assert s.query(User).first() is None

    @testing.resolve_artifact_names
    def test_extension(self):
        mapper(User, users)
        log = []
        class MyExt(sa.orm.session.SessionExtension):
            def before_commit(self, session):
                log.append('before_commit')
            def after_commit(self, session):
                log.append('after_commit')
            def after_rollback(self, session):
                log.append('after_rollback')
            def before_flush(self, session, flush_context, objects):
                log.append('before_flush')
            def after_flush(self, session, flush_context):
                log.append('after_flush')
            def after_flush_postexec(self, session, flush_context):
                log.append('after_flush_postexec')
            def after_begin(self, session, transaction, connection):
                log.append('after_begin')
            def after_attach(self, session, instance):
                log.append('after_attach')
            def after_bulk_update(
                self,
                session,
                query,
                query_context,
                result,
                ):
                log.append('after_bulk_update')

            def after_bulk_delete(
                self,
                session,
                query,
                query_context,
                result,
                ):
                log.append('after_bulk_delete')

        sess = create_session(extension = MyExt())
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        assert log == [
            'after_attach',
            'before_flush',
            'after_begin',
            'after_flush',
            'before_commit',
            'after_commit',
            'after_flush_postexec',
            ]
        log = []
        sess = create_session(autocommit=False, extension=MyExt())
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        assert log == ['after_attach', 'before_flush', 'after_begin',
                       'after_flush', 'after_flush_postexec']
        log = []
        u.name = 'ed'
        sess.commit()
        assert log == ['before_commit', 'before_flush', 'after_flush',
                       'after_flush_postexec', 'after_commit']
        log = []
        sess.commit()
        assert log == ['before_commit', 'after_commit']
        log = []
        sess.query(User).delete()
        assert log == ['after_begin', 'after_bulk_delete']
        log = []
        sess.query(User).update({'name': 'foo'})
        assert log == ['after_bulk_update']
        log = []
        sess = create_session(autocommit=False, extension=MyExt(),
                              bind=testing.db)
        conn = sess.connection()
        assert log == ['after_begin']

    @testing.resolve_artifact_names
    def test_before_flush(self):
        """test that the flush plan can be affected during before_flush()"""
        
        mapper(User, users)
        
        class MyExt(sa.orm.session.SessionExtension):
            def before_flush(self, session, flush_context, objects):
                for obj in list(session.new) + list(session.dirty):
                    if isinstance(obj, User):
                        session.add(User(name='another %s' % obj.name))
                for obj in list(session.deleted):
                    if isinstance(obj, User):
                        x = session.query(User).filter(User.name
                                == 'another %s' % obj.name).one()
                        session.delete(x)
                    
        sess = create_session(extension = MyExt(), autoflush=True)
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        eq_(sess.query(User).order_by(User.name).all(), 
            [
                User(name='another u1'),
                User(name='u1')
            ]
        )
        
        sess.flush()
        eq_(sess.query(User).order_by(User.name).all(), 
            [
                User(name='another u1'),
                User(name='u1')
            ]
        )

        u.name='u2'
        sess.flush()
        eq_(sess.query(User).order_by(User.name).all(), 
            [
                User(name='another u1'),
                User(name='another u2'),
                User(name='u2')
            ]
        )

        sess.delete(u)
        sess.flush()
        eq_(sess.query(User).order_by(User.name).all(), 
            [
                User(name='another u1'),
            ]
        )

    @testing.resolve_artifact_names
    def test_before_flush_affects_dirty(self):
        mapper(User, users)
        
        class MyExt(sa.orm.session.SessionExtension):
            def before_flush(self, session, flush_context, objects):
                for obj in list(session.identity_map.values()):
                    obj.name += " modified"
                    
        sess = create_session(extension = MyExt(), autoflush=True)
        u = User(name='u1')
        sess.add(u)
        sess.flush()
        eq_(sess.query(User).order_by(User.name).all(), 
            [
                User(name='u1')
            ]
        )
        
        sess.add(User(name='u2'))
        sess.flush()
        sess.expunge_all()
        eq_(sess.query(User).order_by(User.name).all(), 
            [
                User(name='u1 modified'),
                User(name='u2')
            ]
        )

    @testing.resolve_artifact_names
    def test_reentrant_flush(self):

        mapper(User, users)

        class MyExt(sa.orm.session.SessionExtension):
            def before_flush(s, session, flush_context, objects):
                session.flush()
        
        sess = create_session(extension=MyExt())
        sess.add(User(name='foo'))
        assert_raises_message(sa.exc.InvalidRequestError,
                              'already flushing', sess.flush)

    @testing.resolve_artifact_names
    def test_pickled_update(self):
        mapper(User, users)
        sess1 = create_session()
        sess2 = create_session()
        u1 = User(name='u1')
        sess1.add(u1)
        assert_raises_message(sa.exc.InvalidRequestError,
                              'already attached to session', sess2.add,
                              u1)
        u2 = pickle.loads(pickle.dumps(u1))
        sess2.add(u2)

    @testing.resolve_artifact_names
    def test_duplicate_update(self):
        mapper(User, users)
        Session = sessionmaker()
        sess = Session()

        u1 = User(name='u1')
        sess.add(u1)
        sess.flush()
        assert u1.id is not None

        sess.expunge(u1)

        assert u1 not in sess
        assert Session.object_session(u1) is None

        u2 = sess.query(User).get(u1.id)
        assert u2 is not None and u2 is not u1
        assert u2 in sess

        assert_raises(Exception, lambda: sess.add(u1))

        sess.expunge(u2)
        assert u2 not in sess
        assert Session.object_session(u2) is None

        u1.name = "John"
        u2.name = "Doe"

        sess.add(u1)
        assert u1 in sess
        assert Session.object_session(u1) is sess

        sess.flush()

        sess.expunge_all()

        u3 = sess.query(User).get(u1.id)
        assert u3 is not u1 and u3 is not u2 and u3.name == u1.name

    @testing.resolve_artifact_names
    def test_no_double_save(self):
        sess = create_session()
        class Foo(object):
            def __init__(self):
                sess.add(self)
        class Bar(Foo):
            def __init__(self):
                sess.add(self)
                Foo.__init__(self)
        mapper(Foo, users)
        mapper(Bar, users)

        b = Bar()
        assert b in sess
        assert len(list(sess)) == 1

    @testing.resolve_artifact_names
    def test_identity_map_mutate(self):
        mapper(User, users)

        sess = Session()
        
        sess.add_all([User(name='u1'), User(name='u2'), User(name='u3')])
        sess.commit()
        
        u1, u2, u3 = sess.query(User).all()
        for i, (key, value) in enumerate(sess.identity_map.iteritems()):
            if i == 2:
                del u3
                gc_collect()
        
        
class DisposedStates(_base.MappedTest):
    run_setup_mappers = 'once'
    run_inserts = 'once'
    run_deletes = None
    
    @classmethod
    def define_tables(cls, metadata):
        global t1
        t1 = Table('t1', metadata, Column('id', Integer,
                   primary_key=True, test_needs_autoincrement=True),
                   Column('data', String(50)))

    @classmethod
    def setup_mappers(cls):
        global T
        class T(object):
            def __init__(self, data):
                self.data = data
        mapper(T, t1)
    
    def teardown(self):
        from sqlalchemy.orm.session import _sessions
        _sessions.clear()
        super(DisposedStates, self).teardown()
        
    def _set_imap_in_disposal(self, sess, *objs):
        """remove selected objects from the given session, as though
        they were dereferenced and removed from WeakIdentityMap.
        
        Hardcodes the identity map's "all_states()" method to return the
        full list of states.  This simulates the all_states() method
        returning results, afterwhich some of the states get garbage
        collected (this normally only happens during asynchronous gc).
        The Session now has one or more InstanceState's which have been
        removed from the identity map and disposed.
        
        Will the Session not trip over this ???  Stay tuned.
        
        """

        all_states = sess.identity_map.all_states()
        sess.identity_map.all_states = lambda : all_states
        for obj in objs:
            state = attributes.instance_state(obj)
            sess.identity_map.remove(state)
            state.dispose()
    
    def _test_session(self, **kwargs):
        global sess
        sess = create_session(**kwargs)

        data = o1, o2, o3, o4, o5 = [T('t1'), T('t2'), T('t3'), T('t4'
                ), T('t5')]

        sess.add_all(data)

        sess.flush()

        o1.data = 't1modified'
        o5.data = 't5modified'
        
        self._set_imap_in_disposal(sess, o2, o4, o5)
        return sess
        
    def test_flush(self):
        self._test_session().flush()
    
    def test_clear(self):
        self._test_session().expunge_all()
    
    def test_close(self):
        self._test_session().close()
        
    def test_expunge_all(self):
        self._test_session().expunge_all()
        
    def test_expire_all(self):
        self._test_session().expire_all()
    
    def test_rollback(self):
        sess = self._test_session(autocommit=False, expire_on_commit=True)
        sess.commit()
        
        sess.rollback()
        
        
class SessionInterface(testing.TestBase):
    """Bogus args to Session methods produce actionable exceptions."""

    # TODO: expand with message body assertions.

    _class_methods = set((
        'connection', 'execute', 'get_bind', 'scalar'))

    def _public_session_methods(self):
        Session = sa.orm.session.Session

        blacklist = set(('begin', 'query'))

        ok = set()
        for meth in Session.public_methods:
            if meth in blacklist:
                continue
            spec = inspect.getargspec(getattr(Session, meth))
            if len(spec[0]) > 1 or spec[1]:
                ok.add(meth)
        return ok

    def _map_it(self, cls):
        return mapper(cls, Table('t', sa.MetaData(), Column('id',
                      Integer, primary_key=True,
                      test_needs_autoincrement=True)))

    @testing.uses_deprecated()
    def _test_instance_guards(self, user_arg):
        watchdog = set()

        def x_raises_(obj, method, *args, **kw):
            watchdog.add(method)
            callable_ = getattr(obj, method)
            assert_raises(sa.orm.exc.UnmappedInstanceError,
                              callable_, *args, **kw)

        def raises_(method, *args, **kw):
            x_raises_(create_session(), method, *args, **kw)

        raises_('__contains__', user_arg)

        raises_('add', user_arg)

        raises_('add_all', (user_arg,))

        raises_('delete', user_arg)

        raises_('expire', user_arg)

        raises_('expunge', user_arg)

        # flush will no-op without something in the unit of work
        def _():
            class OK(object):
                pass
            self._map_it(OK)

            s = create_session()
            s.add(OK())
            x_raises_(s, 'flush', (user_arg,))
        _()

        raises_('is_modified', user_arg)

        raises_('merge', user_arg)

        raises_('refresh', user_arg)

        instance_methods = self._public_session_methods() \
            - self._class_methods

        eq_(watchdog, instance_methods,
            watchdog.symmetric_difference(instance_methods))

    def _test_class_guards(self, user_arg):
        watchdog = set()

        def raises_(method, *args, **kw):
            watchdog.add(method)
            callable_ = getattr(create_session(), method)
            assert_raises(sa.orm.exc.UnmappedClassError,
                              callable_, *args, **kw)

        raises_('connection', mapper=user_arg)

        raises_('execute', 'SELECT 1', mapper=user_arg)

        raises_('get_bind', mapper=user_arg)

        raises_('scalar', 'SELECT 1', mapper=user_arg)

        eq_(watchdog, self._class_methods,
            watchdog.symmetric_difference(self._class_methods))

    def test_unmapped_instance(self):
        class Unmapped(object):
            pass

        self._test_instance_guards(Unmapped())
        self._test_class_guards(Unmapped)

    def test_unmapped_primitives(self):
        for prim in ('doh', 123, ('t', 'u', 'p', 'l', 'e')):
            self._test_instance_guards(prim)
            self._test_class_guards(prim)

    def test_unmapped_class_for_instance(self):
        class Unmapped(object):
            pass

        self._test_instance_guards(Unmapped)
        self._test_class_guards(Unmapped)

    def test_mapped_class_for_instance(self):
        class Mapped(object):
            pass
        self._map_it(Mapped)

        self._test_instance_guards(Mapped)
        # no class guards- it would pass.

    def test_missing_state(self):
        class Mapped(object):
            pass
        early = Mapped()
        self._map_it(Mapped)

        self._test_instance_guards(early)
        self._test_class_guards(early)


class TLTransactionTest(engine_base.AltEngineTest, _base.MappedTest):
    @classmethod
    def create_engine(cls):
        return engines.testing_engine(options=dict(strategy='threadlocal'))

    @classmethod
    def define_tables(cls, metadata):
        Table('users', metadata, Column('id', Integer,
              primary_key=True, test_needs_autoincrement=True),
              Column('name', String(20)), test_needs_acid=True)

    @classmethod
    def setup_classes(cls):
        class User(_base.BasicEntity):
            pass

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(User, users)

    @testing.exclude('mysql', '<', (5, 0, 3), 'FIXME: unknown')
    @testing.resolve_artifact_names
    def test_session_nesting(self):
        sess = create_session(bind=self.engine)
        self.engine.begin()
        u = User(name='ed')
        sess.add(u)
        sess.flush()
        self.engine.commit()


