from sqlalchemy import *
from sqlalchemy.test import *


class FoundRowsTest(TestBase, AssertsExecutionResults):
    """tests rowcount functionality"""
    
    __requires__ = ('sane_rowcount', )
    
    @classmethod
    def setup_class(cls):
        global employees_table, metadata
        metadata = MetaData(testing.db)

        employees_table = Table('employees', metadata,
            Column('employee_id', Integer, 
                        Sequence('employee_id_seq', optional=True), 
                        primary_key=True),
            Column('name', String(50)),
            Column('department', String(1)),
        )
        metadata.create_all()

    def setup(self):
        global data
        data = [ ('Angela', 'A'),
                 ('Andrew', 'A'),
                 ('Anand', 'A'),
                 ('Bob', 'B'),
                 ('Bobette', 'B'),
                 ('Buffy', 'B'),
                 ('Charlie', 'C'),
                 ('Cynthia', 'C'),
                 ('Chris', 'C') ]

        i = employees_table.insert()
        i.execute(*[{'name':n, 'department':d} for n, d in data])
    def teardown(self):
        employees_table.delete().execute()

    @classmethod
    def teardown_class(cls):
        metadata.drop_all()

    def testbasic(self):
        s = employees_table.select()
        r = s.execute().fetchall()

        assert len(r) == len(data)

    def test_update_rowcount1(self):
        # WHERE matches 3, 3 rows changed
        department = employees_table.c.department
        r = employees_table.update(department=='C').execute(department='Z')
        print "expecting 3, dialect reports %s" % r.rowcount
        assert r.rowcount == 3

    def test_update_rowcount2(self):
        # WHERE matches 3, 0 rows changed
        department = employees_table.c.department
        r = employees_table.update(department=='C').execute(department='C')
        print "expecting 3, dialect reports %s" % r.rowcount
        assert r.rowcount == 3

    def test_delete_rowcount(self):
        # WHERE matches 3, 3 rows deleted
        department = employees_table.c.department
        r = employees_table.delete(department=='C').execute()
        print "expecting 3, dialect reports %s" % r.rowcount
        assert r.rowcount == 3

