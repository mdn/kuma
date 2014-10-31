import sqlalchemy as sa
from sqlalchemy.test import testing
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.test.schema import Table, Column
from sqlalchemy.orm import mapper, relationship, create_session
from test.orm import _base


class O2OTest(_base.MappedTest):
    @classmethod
    def define_tables(cls, metadata):
        Table('jack', metadata,
              Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
              Column('number', String(50)),
              Column('status', String(20)),
              Column('subroom', String(5)))

        Table('port', metadata,
              Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
              Column('name', String(30)),
              Column('description', String(100)),
              Column('jack_id', Integer, ForeignKey("jack.id")))

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        class Jack(_base.BasicEntity):
            pass
        class Port(_base.BasicEntity):
            pass


    @testing.resolve_artifact_names
    def test_basic(self):
        mapper(Port, port)
        mapper(Jack, jack,
               order_by=[jack.c.number],
               properties=dict(
                   port=relationship(Port, backref='jack',
                                 uselist=False,
                                 )),
               )

        session = create_session()

        j = Jack(number='101')
        session.add(j)
        p = Port(name='fa0/1')
        session.add(p)
        
        j.port=p
        session.flush()
        jid = j.id
        pid = p.id

        j=session.query(Jack).get(jid)
        p=session.query(Port).get(pid)
        assert p.jack is not None
        assert p.jack is  j
        assert j.port is not None
        p.jack = None
        assert j.port is None

        session.expunge_all()

        j = session.query(Jack).get(jid)
        p = session.query(Port).get(pid)

        j.port=None
        self.assert_(p.jack is None)
        session.flush()

        session.delete(j)
        session.flush()

