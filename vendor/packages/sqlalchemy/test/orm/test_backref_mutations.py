"""
a series of tests which assert the behavior of moving objects between collections
and scalar attributes resulting in the expected state w.r.t. backrefs, add/remove
events, etc.

there's a particular focus on collections that have "uselist=False", since in these
cases the re-assignment of an attribute means the previous owner needs an
UPDATE in the database.

"""

from sqlalchemy.test.testing import assert_raises, assert_raises_message
from sqlalchemy import Integer, String, ForeignKey, Sequence, exc as sa_exc
from sqlalchemy.test.schema import Table
from sqlalchemy.test.schema import Column
from sqlalchemy.orm import mapper, relationship, create_session, class_mapper, backref, sessionmaker
from sqlalchemy.orm import attributes, exc as orm_exc
from sqlalchemy.test import testing
from sqlalchemy.test.testing import eq_
from test.orm import _base, _fixtures

class O2MCollectionTest(_fixtures.FixtureTest):
    run_inserts = None

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Address, addresses)
        mapper(User, users, properties = dict(
            addresses = relationship(Address, backref="user"),
        ))

    @testing.resolve_artifact_names
    def test_collection_move_hitslazy(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        a2 = Address(email_address="address2")
        a3 = Address(email_address="address3")
        u1= User(name='jack', addresses=[a1, a2, a3])
        u2= User(name='ed')
        sess.add_all([u1, a1, a2, a3])
        sess.commit()
        
        #u1.addresses
        
        def go():
            u2.addresses.append(a1)
            u2.addresses.append(a2)
            u2.addresses.append(a3)
        self.assert_sql_count(testing.db, go, 0)
        
    @testing.resolve_artifact_names
    def test_collection_move_preloaded(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', addresses=[a1])

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        # load u1.addresses collection
        u1.addresses

        u2.addresses.append(a1)

        # backref fires
        assert a1.user is u2

        # doesn't extend to the previous collection tho,
        # which was already loaded.
        # flushing at this point means its anyone's guess.
        assert a1 in u1.addresses
        assert a1 in u2.addresses

    @testing.resolve_artifact_names
    def test_collection_move_notloaded(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', addresses=[a1])

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        u2.addresses.append(a1)

        # backref fires
        assert a1.user is u2
        
        # u1.addresses wasn't loaded,
        # so when it loads its correct
        assert a1 not in u1.addresses
        assert a1 in u2.addresses

    @testing.resolve_artifact_names
    def test_collection_move_commitfirst(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', addresses=[a1])

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        # load u1.addresses collection
        u1.addresses

        u2.addresses.append(a1)

        # backref fires
        assert a1.user is u2
        
        # everything expires, no changes in 
        # u1.addresses, so all is fine
        sess.commit()
        assert a1 not in u1.addresses
        assert a1 in u2.addresses

    @testing.resolve_artifact_names
    def test_scalar_move_preloaded(self):
        sess = sessionmaker()()

        u1 = User(name='jack')
        u2 = User(name='ed')
        a1 = Address(email_address='a1')
        a1.user = u1
        sess.add_all([u1, u2, a1])
        sess.commit()

        # u1.addresses is loaded
        u1.addresses

        # direct set - the "old" is "fetched",
        # but only from the local session - not the 
        # database, due to the PASSIVE_NO_FETCH flag.
        # this is a more fine grained behavior introduced
        # in 0.6
        a1.user = u2

        assert a1 not in u1.addresses
        assert a1 in u2.addresses

    @testing.resolve_artifact_names
    def test_plain_load_passive(self):
        """test that many-to-one set doesn't load the old value."""
        
        sess = sessionmaker()()
        u1 = User(name='jack')
        u2 = User(name='ed')
        a1 = Address(email_address='a1')
        a1.user = u1
        sess.add_all([u1, u2, a1])
        sess.commit()

        # in this case, a lazyload would
        # ordinarily occur except for the
        # PASSIVE_NO_FETCH flag.
        def go():
            a1.user = u2
        self.assert_sql_count(testing.db, go, 0)
        
        assert a1 not in u1.addresses
        assert a1 in u2.addresses
        
    @testing.resolve_artifact_names
    def test_set_none(self):
        sess = sessionmaker()()
        u1 = User(name='jack')
        a1 = Address(email_address='a1')
        a1.user = u1
        sess.add_all([u1, a1])
        sess.commit()

        # works for None too
        def go():
            a1.user = None
        self.assert_sql_count(testing.db, go, 0)
        
        assert a1 not in u1.addresses
        
        
        
    @testing.resolve_artifact_names
    def test_scalar_move_notloaded(self):
        sess = sessionmaker()()

        u1 = User(name='jack')
        u2 = User(name='ed')
        a1 = Address(email_address='a1')
        a1.user = u1
        sess.add_all([u1, u2, a1])
        sess.commit()

        # direct set - the fetching of the 
        # "old" u1 here allows the backref
        # to remove it from the addresses collection
        a1.user = u2

        assert a1 not in u1.addresses
        assert a1 in u2.addresses

    @testing.resolve_artifact_names
    def test_scalar_move_commitfirst(self):
        sess = sessionmaker()()

        u1 = User(name='jack')
        u2 = User(name='ed')
        a1 = Address(email_address='a1')
        a1.user = u1
        sess.add_all([u1, u2, a1])
        sess.commit()

        # u1.addresses is loaded
        u1.addresses

        # direct set - the fetching of the 
        # "old" u1 here allows the backref
        # to remove it from the addresses collection
        a1.user = u2
        
        sess.commit()
        assert a1 not in u1.addresses
        assert a1 in u2.addresses

class O2OScalarBackrefMoveTest(_fixtures.FixtureTest):
    run_inserts = None

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Address, addresses)
        mapper(User, users, properties = {
            'address':relationship(Address, backref=backref("user"), uselist=False)
        })

    @testing.resolve_artifact_names
    def test_collection_move_preloaded(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        # load u1.address
        u1.address

        # reassign
        u2.address = a1
        assert u2.address is a1

        # backref fires
        assert a1.user is u2

        # doesn't extend to the previous attribute tho.
        # flushing at this point means its anyone's guess.
        assert u1.address is a1
        assert u2.address is a1

    @testing.resolve_artifact_names
    def test_scalar_move_preloaded(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        a2 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)

        sess.add_all([u1, a1, a2])
        sess.commit() # everything is expired

        # load a1.user
        a1.user
        
        # reassign
        a2.user = u1

        # backref fires
        assert u1.address is a2
        
        # stays on both sides
        assert a1.user is u1
        assert a2.user is u1

    @testing.resolve_artifact_names
    def test_collection_move_notloaded(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        # reassign
        u2.address = a1
        assert u2.address is a1

        # backref fires
        assert a1.user is u2
        
        # u1.address loads now after a flush
        assert u1.address is None
        assert u2.address is a1

    @testing.resolve_artifact_names
    def test_scalar_move_notloaded(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        a2 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)

        sess.add_all([u1, a1, a2])
        sess.commit() # everything is expired

        # reassign
        a2.user = u1

        # backref fires
        assert u1.address is a2

        # stays on both sides
        assert a1.user is u1
        assert a2.user is u1

    @testing.resolve_artifact_names
    def test_collection_move_commitfirst(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        # load u1.address
        u1.address

        # reassign
        u2.address = a1
        assert u2.address is a1

        # backref fires
        assert a1.user is u2

        # the commit cancels out u1.addresses
        # being loaded, on next access its fine.
        sess.commit()
        assert u1.address is None
        assert u2.address is a1

    @testing.resolve_artifact_names
    def test_scalar_move_commitfirst(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        a2 = Address(email_address="address2")
        u1 = User(name='jack', address=a1)

        sess.add_all([u1, a1, a2])
        sess.commit() # everything is expired

        # load
        assert a1.user is u1
        
        # reassign
        a2.user = u1

        # backref fires
        assert u1.address is a2

        # didnt work this way tho
        assert a1.user is u1
        
        # moves appropriately after commit
        sess.commit()
        assert u1.address is a2
        assert a1.user is None
        assert a2.user is u1

class O2OScalarMoveTest(_fixtures.FixtureTest):
    run_inserts = None

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Address, addresses)
        mapper(User, users, properties = {
            'address':relationship(Address, uselist=False)
        })

    @testing.resolve_artifact_names
    def test_collection_move_commitfirst(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)

        u2 = User(name='ed')
        sess.add_all([u1, u2])
        sess.commit() # everything is expired

        # load u1.address
        u1.address

        # reassign
        u2.address = a1
        assert u2.address is a1

        # the commit cancels out u1.addresses
        # being loaded, on next access its fine.
        sess.commit()
        assert u1.address is None
        assert u2.address is a1

class O2OScalarOrphanTest(_fixtures.FixtureTest):
    run_inserts = None

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Address, addresses)
        mapper(User, users, properties = {
            'address':relationship(Address, uselist=False, 
                backref=backref('user', single_parent=True, cascade="all, delete-orphan"))
        })

    @testing.resolve_artifact_names
    def test_m2o_event(self):
        sess = sessionmaker()()
        a1 = Address(email_address="address1")
        u1 = User(name='jack', address=a1)
        
        sess.add(u1)
        sess.commit()
        sess.expunge(u1)
        
        u2= User(name='ed')
        # the _SingleParent extension sets the backref get to "active" !
        # u1 gets loaded and deleted
        u2.address = a1
        sess.commit()
        assert sess.query(User).count() == 1
        
    
class M2MScalarMoveTest(_fixtures.FixtureTest):
    run_inserts = None

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Item, items, properties={
            'keyword':relationship(Keyword, secondary=item_keywords, uselist=False, backref=backref("item", uselist=False))
        })
        mapper(Keyword, keywords)
    
    @testing.resolve_artifact_names
    def test_collection_move_preloaded(self):
        sess = sessionmaker()()
        
        k1 = Keyword(name='k1')
        i1 = Item(description='i1', keyword=k1)
        i2 = Item(description='i2')

        sess.add_all([i1, i2, k1])
        sess.commit() # everything is expired
        
        # load i1.keyword
        assert i1.keyword is k1
        
        i2.keyword = k1

        assert k1.item is i2
        
        # nothing happens.
        assert i1.keyword is k1
        assert i2.keyword is k1

    @testing.resolve_artifact_names
    def test_collection_move_notloaded(self):
        sess = sessionmaker()()

        k1 = Keyword(name='k1')
        i1 = Item(description='i1', keyword=k1)
        i2 = Item(description='i2')

        sess.add_all([i1, i2, k1])
        sess.commit() # everything is expired

        i2.keyword = k1

        assert k1.item is i2

        assert i1.keyword is None
        assert i2.keyword is k1

    @testing.resolve_artifact_names
    def test_collection_move_commit(self):
        sess = sessionmaker()()

        k1 = Keyword(name='k1')
        i1 = Item(description='i1', keyword=k1)
        i2 = Item(description='i2')

        sess.add_all([i1, i2, k1])
        sess.commit() # everything is expired

        # load i1.keyword
        assert i1.keyword is k1

        i2.keyword = k1

        assert k1.item is i2

        sess.commit()
        assert i1.keyword is None
        assert i2.keyword is k1
