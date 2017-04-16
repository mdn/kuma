from sqlalchemy.test.testing import eq_, assert_raises, assert_raises_message
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm import interfaces
from sqlalchemy import exc as sa_exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import default

from sqlalchemy.test import AssertsCompiledSQL, testing
from test.orm import _base, _fixtures
from sqlalchemy.test.testing import eq_
from sqlalchemy.test.schema import Table, Column

class Company(_fixtures.Base):
    pass

class Person(_fixtures.Base):
    pass
class Engineer(Person):
    pass
class Manager(Person):
    pass
class Boss(Manager):
    pass

class Machine(_fixtures.Base):
    pass
    
class Paperwork(_fixtures.Base):
    pass

def _produce_test(select_type):
    class PolymorphicQueryTest(_base.MappedTest, AssertsCompiledSQL):
        run_inserts = 'once'
        run_setup_mappers = 'once'
        run_deletes = None
        
        @classmethod
        def define_tables(cls, metadata):
            global companies, people, engineers, managers, boss, paperwork, machines

            companies = Table('companies', metadata,
               Column('company_id', Integer, primary_key=True, test_needs_autoincrement=True),
               Column('name', String(50)))

            people = Table('people', metadata,
               Column('person_id', Integer, primary_key=True, test_needs_autoincrement=True),
               Column('company_id', Integer, ForeignKey('companies.company_id')),
               Column('name', String(50)),
               Column('type', String(30)))

            engineers = Table('engineers', metadata,
               Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
               Column('status', String(30)),
               Column('engineer_name', String(50)),
               Column('primary_language', String(50)),
              )
         
            machines = Table('machines', metadata,
                Column('machine_id', Integer, primary_key=True, test_needs_autoincrement=True),
                Column('name', String(50)),
                Column('engineer_id', Integer, ForeignKey('engineers.person_id')))
            
            managers = Table('managers', metadata,
               Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
               Column('status', String(30)),
               Column('manager_name', String(50))
               )

            boss = Table('boss', metadata,
                Column('boss_id', Integer, ForeignKey('managers.person_id'), primary_key=True),
                Column('golf_swing', String(30)),
                )

            paperwork = Table('paperwork', metadata,
                Column('paperwork_id', Integer, primary_key=True, test_needs_autoincrement=True),
                Column('description', String(50)),
                Column('person_id', Integer, ForeignKey('people.person_id')))

            clear_mappers()
            
            mapper(Company, companies, properties={
                'employees':relationship(Person, order_by=people.c.person_id)
            })

            mapper(Machine, machines)

            if select_type == '':
                person_join = manager_join = None
                person_with_polymorphic = None
                manager_with_polymorphic = None
            elif select_type == 'Polymorphic':
                person_join = manager_join = None
                person_with_polymorphic = '*'
                manager_with_polymorphic = '*'
            elif select_type == 'Unions':
                person_join = polymorphic_union(
                    {
                        'engineer':people.join(engineers),
                        'manager':people.join(managers),
                    }, None, 'pjoin')

                manager_join = people.join(managers).outerjoin(boss)
                person_with_polymorphic = ([Person, Manager, Engineer], person_join)
                manager_with_polymorphic = ('*', manager_join)
            elif select_type == 'AliasedJoins':
                person_join = people.outerjoin(engineers).outerjoin(managers).select(use_labels=True).alias('pjoin')
                manager_join = people.join(managers).outerjoin(boss).select(use_labels=True).alias('mjoin')
                person_with_polymorphic = ([Person, Manager, Engineer], person_join)
                manager_with_polymorphic = ('*', manager_join)
            elif select_type == 'Joins':
                person_join = people.outerjoin(engineers).outerjoin(managers)
                manager_join = people.join(managers).outerjoin(boss)
                person_with_polymorphic = ([Person, Manager, Engineer], person_join)
                manager_with_polymorphic = ('*', manager_join)


            # testing a order_by here as well; the surrogate mapper has to adapt it
            mapper(Person, people, 
                with_polymorphic=person_with_polymorphic, 
                polymorphic_on=people.c.type, polymorphic_identity='person', order_by=people.c.person_id, 
                properties={
                    'paperwork':relationship(Paperwork, order_by=paperwork.c.paperwork_id)
                })
            mapper(Engineer, engineers, inherits=Person, polymorphic_identity='engineer', properties={
                    'machines':relationship(Machine, order_by=machines.c.machine_id)
                })
            mapper(Manager, managers, with_polymorphic=manager_with_polymorphic, 
                        inherits=Person, polymorphic_identity='manager')
            mapper(Boss, boss, inherits=Manager, polymorphic_identity='boss')
            mapper(Paperwork, paperwork)
        

        @classmethod
        def insert_data(cls):
            global all_employees, c1_employees, c2_employees, e1, e2, b1, m1, e3, c1, c2

            c1 = Company(name="MegaCorp, Inc.")
            c2 = Company(name="Elbonia, Inc.")
            e1 = Engineer(name="dilbert", engineer_name="dilbert", primary_language="java", status="regular engineer", paperwork=[
                Paperwork(description="tps report #1"),
                Paperwork(description="tps report #2")
            ], machines=[
                Machine(name='IBM ThinkPad'),
                Machine(name='IPhone'),
            ])
            e2 = Engineer(name="wally", engineer_name="wally", primary_language="c++", status="regular engineer", paperwork=[
                Paperwork(description="tps report #3"),
                Paperwork(description="tps report #4")
            ], machines=[
                Machine(name="Commodore 64")
            ])
            b1 = Boss(name="pointy haired boss", golf_swing="fore", manager_name="pointy", status="da boss", paperwork=[
                Paperwork(description="review #1"),
            ])
            m1 = Manager(name="dogbert", manager_name="dogbert", status="regular manager", paperwork=[
                Paperwork(description="review #2"),
                Paperwork(description="review #3")
            ])
            c1.employees = [e1, e2, b1, m1]

            e3 = Engineer(name="vlad", engineer_name="vlad", primary_language="cobol", status="elbonian engineer", paperwork=[
                Paperwork(description='elbonian missive #3')
            ], machines=[
                    Machine(name="Commodore 64"),
                    Machine(name="IBM 3270")
            ])
        
            c2.employees = [e3]
            sess = create_session()
            sess.add(c1)
            sess.add(c2)
            sess.flush()
            sess.expunge_all()

            all_employees = [e1, e2, b1, m1, e3]
            c1_employees = [e1, e2, b1, m1]
            c2_employees = [e3]
        
        def test_loads_at_once(self):
            """test that all objects load from the full query, when with_polymorphic is used"""
            
            sess = create_session()
            def go():
                eq_(sess.query(Person).all(), all_employees)
            self.assert_sql_count(testing.db, go, {'':14, 'Polymorphic':9}.get(select_type, 10))

        def test_foo(self):
            sess = create_session()
            
            def go():
                eq_(sess.query(Person).options(subqueryload(Engineer.machines)).all(), all_employees)
            self.assert_sql_count(testing.db, go, {'':14, 'Unions':8, 'Polymorphic':7}.get(select_type, 8))

        def test_primary_eager_aliasing(self):
            sess = create_session()

            # for both joinedload() and subqueryload(), if the original q is not loading
            # the subclass table, the joinedload doesn't happen.
            
            def go():
                eq_(sess.query(Person).options(joinedload(Engineer.machines))[1:3], all_employees[1:3])
            self.assert_sql_count(testing.db, go, {'':6, 'Polymorphic':3}.get(select_type, 4))

            sess = create_session()
            
            def go():
                eq_(sess.query(Person).options(subqueryload(Engineer.machines)).all(), all_employees)
            self.assert_sql_count(testing.db, go, {'':14, 'Unions':8, 'Polymorphic':7}.get(select_type, 8))

            sess = create_session()

            # assert the JOINs dont over JOIN
            assert sess.query(Person).with_polymorphic('*').options(joinedload(Engineer.machines)).\
                                    limit(2).offset(1).with_labels().subquery().count().scalar() == 2

            def go():
                eq_(
                    sess.query(Person).with_polymorphic('*').
                        options(joinedload(Engineer.machines))[1:3], 
                    all_employees[1:3])
            self.assert_sql_count(testing.db, go, 3)
            
            
        def test_get(self):
            sess = create_session()
            
            # for all mappers, ensure the primary key has been calculated as just the "person_id"
            # column
            eq_(sess.query(Person).get(e1.person_id), Engineer(name="dilbert", primary_language="java"))
            eq_(sess.query(Engineer).get(e1.person_id), Engineer(name="dilbert", primary_language="java"))
            eq_(sess.query(Manager).get(b1.person_id), Boss(name="pointy haired boss", golf_swing="fore"))
        
        def test_multi_join(self):
            sess = create_session()

            e = aliased(Person)
            c = aliased(Company)
            
            q = sess.query(Company, Person, c, e).join((Person, Company.employees)).join((e, c.employees)).\
                    filter(Person.name=='dilbert').filter(e.name=='wally')
            
            eq_(q.count(), 1)
            eq_(q.all(), [
                (
                    Company(company_id=1,name=u'MegaCorp, Inc.'), 
                    Engineer(status=u'regular engineer',engineer_name=u'dilbert',name=u'dilbert',company_id=1,primary_language=u'java',person_id=1,type=u'engineer'),
                    Company(company_id=1,name=u'MegaCorp, Inc.'), 
                    Engineer(status=u'regular engineer',engineer_name=u'wally',name=u'wally',company_id=1,primary_language=u'c++',person_id=2,type=u'engineer')
                )
            ])
            
        def test_filter_on_subclass(self):
            sess = create_session()
            eq_(sess.query(Engineer).all()[0], Engineer(name="dilbert"))

            eq_(sess.query(Engineer).first(), Engineer(name="dilbert"))

            eq_(sess.query(Engineer).filter(Engineer.person_id==e1.person_id).first(), Engineer(name="dilbert"))

            eq_(sess.query(Manager).filter(Manager.person_id==m1.person_id).one(), Manager(name="dogbert"))

            eq_(sess.query(Manager).filter(Manager.person_id==b1.person_id).one(), Boss(name="pointy haired boss"))
        
            eq_(sess.query(Boss).filter(Boss.person_id==b1.person_id).one(), Boss(name="pointy haired boss"))

        def test_join_from_polymorphic(self):
            sess = create_session()

            for aliased in (True, False):
                eq_(sess.query(Person).join('paperwork', aliased=aliased).filter(Paperwork.description.like('%review%')).all(), [b1, m1])

                eq_(sess.query(Person).join('paperwork', aliased=aliased).filter(Paperwork.description.like('%#2%')).all(), [e1, m1])

                eq_(sess.query(Engineer).join('paperwork', aliased=aliased).filter(Paperwork.description.like('%#2%')).all(), [e1])

                eq_(sess.query(Person).join('paperwork', aliased=aliased).filter(Person.name.like('%dog%')).filter(Paperwork.description.like('%#2%')).all(), [m1])

        def test_join_from_with_polymorphic(self):
            sess = create_session()

            for aliased in (True, False):
                sess.expunge_all()
                eq_(sess.query(Person).with_polymorphic(Manager).join('paperwork', aliased=aliased).filter(Paperwork.description.like('%review%')).all(), [b1, m1])

                sess.expunge_all()
                eq_(sess.query(Person).with_polymorphic([Manager, Engineer]).join('paperwork', aliased=aliased).filter(Paperwork.description.like('%#2%')).all(), [e1, m1])

                sess.expunge_all()
                eq_(sess.query(Person).with_polymorphic([Manager, Engineer]).join('paperwork', aliased=aliased).filter(Person.name.like('%dog%')).filter(Paperwork.description.like('%#2%')).all(), [m1])
    
        def test_join_to_polymorphic(self):
            sess = create_session()
            eq_(sess.query(Company).join('employees').filter(Person.name=='vlad').one(), c2)

            eq_(sess.query(Company).join('employees', aliased=True).filter(Person.name=='vlad').one(), c2)

        def test_polymorphic_any(self):
            sess = create_session()

            eq_(
                sess.query(Company).\
                    filter(Company.employees.any(Person.name=='vlad')).all(), [c2]
            )
            
            # test that the aliasing on "Person" does not bleed into the
            # EXISTS clause generated by any()
            eq_(
                sess.query(Company).join(Company.employees, aliased=True).filter(Person.name=='dilbert').\
                    filter(Company.employees.any(Person.name=='wally')).all(), [c1]
            )

            eq_(
                sess.query(Company).join(Company.employees, aliased=True).filter(Person.name=='dilbert').\
                    filter(Company.employees.any(Person.name=='vlad')).all(), []
            )
            
            eq_(
                sess.query(Company).filter(Company.employees.of_type(Engineer).any(Engineer.primary_language=='cobol')).one(),
                c2
                )
            
            calias = aliased(Company)
            eq_(
                sess.query(calias).filter(calias.employees.of_type(Engineer).any(Engineer.primary_language=='cobol')).one(),
                c2
            )

            eq_(
                sess.query(Company).filter(Company.employees.of_type(Boss).any(Boss.golf_swing=='fore')).one(),
                c1
                )
            eq_(
                sess.query(Company).filter(Company.employees.of_type(Boss).any(Manager.manager_name=='pointy')).one(),
                c1
                )

            if select_type != '':
                eq_(
                    sess.query(Person).filter(Engineer.machines.any(Machine.name=="Commodore 64")).all(), [e2, e3]
                )

            eq_(
                sess.query(Person).filter(Person.paperwork.any(Paperwork.description=="review #2")).all(), [m1]
            )
            
            eq_(
                sess.query(Company).filter(Company.employees.of_type(Engineer).any(and_(Engineer.primary_language=='cobol'))).one(),
                c2
                )
                
        def test_join_from_columns_or_subclass(self):
            sess = create_session()

            eq_(
                sess.query(Manager.name).order_by(Manager.name).all(),
                [(u'dogbert',), (u'pointy haired boss',)]
            )
            
            eq_(
                sess.query(Manager.name).join((Paperwork, Manager.paperwork)).order_by(Manager.name).all(),
                [(u'dogbert',), (u'dogbert',), (u'pointy haired boss',)]
            )

            eq_(
                sess.query(Person.name).join((Paperwork, Person.paperwork)).order_by(Person.name).all(),
                [(u'dilbert',), (u'dilbert',), (u'dogbert',), (u'dogbert',), (u'pointy haired boss',), (u'vlad',), (u'wally',), (u'wally',)]
            )
            
            eq_(
                sess.query(Person.name).join((paperwork, Manager.person_id==paperwork.c.person_id)).order_by(Person.name).all(),
                [(u'dilbert',), (u'dilbert',), (u'dogbert',), (u'dogbert',), (u'pointy haired boss',), (u'vlad',), (u'wally',), (u'wally',)]
            )
            
            eq_(
                sess.query(Manager).join((Paperwork, Manager.paperwork)).order_by(Manager.name).all(),
                [m1, b1]
            )

            eq_(
                sess.query(Manager.name).join((paperwork, Manager.person_id==paperwork.c.person_id)).order_by(Manager.name).all(),
                [(u'dogbert',), (u'dogbert',), (u'pointy haired boss',)]
            )

            eq_(
                sess.query(Manager.person_id).join((paperwork, Manager.person_id==paperwork.c.person_id)).order_by(Manager.name).all(),
                [(4,), (4,), (3,)]
            )
            
            eq_(
                sess.query(Manager.name, Paperwork.description).
                    join((Paperwork, Manager.person_id==Paperwork.person_id)).
                    order_by(Paperwork.paperwork_id).
                    all(),
                [(u'pointy haired boss', u'review #1'), (u'dogbert', u'review #2'), (u'dogbert', u'review #3')]
            )
            
            malias = aliased(Manager)
            eq_(
                sess.query(malias.name).join((paperwork, malias.person_id==paperwork.c.person_id)).all(),
                [(u'pointy haired boss',), (u'dogbert',), (u'dogbert',)]
            )
        
        def test_polymorphic_option(self):
            """test that polymorphic loading sets state.load_path with its actual mapper
            on a subclass, and not the superclass mapper.
            
            """
            paths = []
            class MyOption(interfaces.MapperOption):
                propagate_to_loaders = True
                def process_query_conditionally(self, query):
                    paths.append(query._current_path)
            
            sess = create_session()
            dilbert, boss = sess.query(Person).\
                            options(MyOption()).\
                            filter(Person.name.in_(['dilbert', 'pointy haired boss'])).\
                            order_by(Person.name).\
                            all()
                            
            dilbert.machines
            boss.paperwork
            eq_(paths, 
                [(class_mapper(Engineer), 'machines'), 
                (class_mapper(Boss), 'paperwork')])
            
            
        def test_expire(self):
            """test that individual column refresh doesn't get tripped up by the select_table mapper"""
            
            sess = create_session()
            m1 = sess.query(Manager).filter(Manager.name=='dogbert').one()
            sess.expire(m1)
            assert m1.status == 'regular manager'

            m2 = sess.query(Manager).filter(Manager.name=='pointy haired boss').one()
            sess.expire(m2, ['manager_name', 'golf_swing'])
            assert m2.golf_swing=='fore'
            
        def test_with_polymorphic(self):
            
            sess = create_session()
            
            
            assert_raises(sa_exc.InvalidRequestError, sess.query(Person).with_polymorphic, Paperwork)
            assert_raises(sa_exc.InvalidRequestError, sess.query(Engineer).with_polymorphic, Boss)
            assert_raises(sa_exc.InvalidRequestError, sess.query(Engineer).with_polymorphic, Person)
            
            # compare to entities without related collections to prevent additional lazy SQL from firing on 
            # loaded entities
            emps_without_relationships = [
                Engineer(name="dilbert", engineer_name="dilbert", primary_language="java", status="regular engineer"),
                Engineer(name="wally", engineer_name="wally", primary_language="c++", status="regular engineer"),
                Boss(name="pointy haired boss", golf_swing="fore", manager_name="pointy", status="da boss"),
                Manager(name="dogbert", manager_name="dogbert", status="regular manager"),
                Engineer(name="vlad", engineer_name="vlad", primary_language="cobol", status="elbonian engineer")
            ]
            eq_(sess.query(Person).with_polymorphic('*').all(), emps_without_relationships)
            
            
            def go():
                eq_(sess.query(Person).with_polymorphic(Engineer).filter(Engineer.primary_language=='java').all(), emps_without_relationships[0:1])
            self.assert_sql_count(testing.db, go, 1)
            
            sess.expunge_all()
            def go():
                eq_(sess.query(Person).with_polymorphic('*').all(), emps_without_relationships)
            self.assert_sql_count(testing.db, go, 1)

            sess.expunge_all()
            def go():
                eq_(sess.query(Person).with_polymorphic(Engineer).all(), emps_without_relationships)
            self.assert_sql_count(testing.db, go, 3)

            sess.expunge_all()
            def go():
                eq_(sess.query(Person).with_polymorphic(Engineer, people.outerjoin(engineers)).all(), emps_without_relationships)
            self.assert_sql_count(testing.db, go, 3)
            
            sess.expunge_all()
            def go():
                # limit the polymorphic join down to just "Person", overriding select_table
                eq_(sess.query(Person).with_polymorphic(Person).all(), emps_without_relationships)
            self.assert_sql_count(testing.db, go, 6)
        
        def test_relationship_to_polymorphic(self):
            assert_result = [
                Company(name="MegaCorp, Inc.", employees=[
                    Engineer(name="dilbert", engineer_name="dilbert", 
                            primary_language="java", status="regular engineer", 
                            machines=[Machine(name="IBM ThinkPad"), Machine(name="IPhone")]),
                    Engineer(name="wally", engineer_name="wally", primary_language="c++", status="regular engineer"),
                    Boss(name="pointy haired boss", golf_swing="fore", manager_name="pointy", status="da boss"),
                    Manager(name="dogbert", manager_name="dogbert", status="regular manager"),
                ]),
                Company(name="Elbonia, Inc.", employees=[
                    Engineer(name="vlad", engineer_name="vlad", primary_language="cobol", status="elbonian engineer")
                ])
            ]
            
            sess = create_session()
            
            def go():
                # test load Companies with lazy load to 'employees'
                eq_(sess.query(Company).all(), assert_result)
            self.assert_sql_count(testing.db, go, {'':9, 'Polymorphic':4}.get(select_type, 5))
        
            sess = create_session()
            def go():
                # currently, it doesn't matter if we say Company.employees, 
                # or Company.employees.of_type(Engineer).  joinedloader doesn't
                # pick up on the "of_type()" as of yet.
                eq_(
                    sess.query(Company).options(
                                        joinedload_all(Company.employees.of_type(Engineer), Engineer.machines
                                    )).all(), 
                        assert_result)
            
            # in the case of select_type='', the joinedload 
            # doesn't take in this case; it joinedloads company->people, 
            # then a load for each of 5 rows, then lazyload of "machines"            
            self.assert_sql_count(testing.db, go, 
                                    {'':7, 'Polymorphic':1}.get(select_type, 2)
                                    )
            
            sess = create_session()
            def go():
                eq_(
                    sess.query(Company).options(
                                    subqueryload_all(Company.employees.of_type(Engineer), Engineer.machines
                                )).all(), 
                            assert_result)
        
            self.assert_sql_count(
                            testing.db, go, 
                            {'':8, 
                                'Joins':4,
                                'Unions':4,
                                'Polymorphic':3,
                                'AliasedJoins':4}[select_type]
                        )
    
        def test_joinedload_on_subclass(self):
            sess = create_session()
            def go():
                # test load People with joinedload to engineers + machines
                eq_(sess.query(Person).with_polymorphic('*').options(joinedload(Engineer.machines)).filter(Person.name=='dilbert').all(), 
                [Engineer(name="dilbert", engineer_name="dilbert", primary_language="java", status="regular engineer", machines=[Machine(name="IBM ThinkPad"), Machine(name="IPhone")])]
                )
            self.assert_sql_count(testing.db, go, 1)

            sess = create_session()
            def go():
                # test load People with subqueryload to engineers + machines
                eq_(sess.query(Person).with_polymorphic('*').options(subqueryload(Engineer.machines)).filter(Person.name=='dilbert').all(), 
                [Engineer(name="dilbert", engineer_name="dilbert", primary_language="java", status="regular engineer", machines=[Machine(name="IBM ThinkPad"), Machine(name="IPhone")])]
                )
            self.assert_sql_count(testing.db, go, 2)

            
        def test_query_subclass_join_to_base_relationship(self):
            sess = create_session()
            # non-polymorphic
            eq_(sess.query(Engineer).join(Person.paperwork).all(), [e1, e2, e3])

        def test_join_to_subclass(self):
            sess = create_session()
            eq_(sess.query(Company).join(('employees', people.join(engineers))).filter(Engineer.primary_language=='java').all(), [c1])

            if select_type == '':
                eq_(sess.query(Company).select_from(companies.join(people).join(engineers)).filter(Engineer.primary_language=='java').all(), [c1])
                eq_(sess.query(Company).join(('employees', people.join(engineers))).filter(Engineer.primary_language=='java').all(), [c1])
                
                ealias = aliased(Engineer)
                eq_(sess.query(Company).join(('employees', ealias)).filter(ealias.primary_language=='java').all(), [c1])

                eq_(sess.query(Person).select_from(people.join(engineers)).join(Engineer.machines).all(), [e1, e2, e3])
                eq_(sess.query(Person).select_from(people.join(engineers)).join(Engineer.machines).filter(Machine.name.ilike("%ibm%")).all(), [e1, e3])
                eq_(sess.query(Company).join(('employees', people.join(engineers)), Engineer.machines).all(), [c1, c2])
                eq_(sess.query(Company).join(('employees', people.join(engineers)), Engineer.machines).filter(Machine.name.ilike("%thinkpad%")).all(), [c1])
            else:
                eq_(sess.query(Company).select_from(companies.join(people).join(engineers)).filter(Engineer.primary_language=='java').all(), [c1])
                eq_(sess.query(Company).join('employees').filter(Engineer.primary_language=='java').all(), [c1])
                eq_(sess.query(Person).join(Engineer.machines).all(), [e1, e2, e3])
                eq_(sess.query(Person).join(Engineer.machines).filter(Machine.name.ilike("%ibm%")).all(), [e1, e3])
                eq_(sess.query(Company).join('employees', Engineer.machines).all(), [c1, c2])
                eq_(sess.query(Company).join('employees', Engineer.machines).filter(Machine.name.ilike("%thinkpad%")).all(), [c1])
            
            # non-polymorphic
            eq_(sess.query(Engineer).join(Engineer.machines).all(), [e1, e2, e3])
            eq_(sess.query(Engineer).join(Engineer.machines).filter(Machine.name.ilike("%ibm%")).all(), [e1, e3])

            # here's the new way
            eq_(sess.query(Company).join(Company.employees.of_type(Engineer)).filter(Engineer.primary_language=='java').all(), [c1])
            eq_(sess.query(Company).join(Company.employees.of_type(Engineer), 'machines').filter(Machine.name.ilike("%thinkpad%")).all(), [c1])

        def test_join_through_polymorphic(self):

            sess = create_session()

            for aliased in (True, False):
                eq_(
                    sess.query(Company).\
                        join('employees', 'paperwork', aliased=aliased).filter(Paperwork.description.like('%#2%')).all(),
                    [c1]
                )

                eq_(
                    sess.query(Company).\
                        join('employees', 'paperwork', aliased=aliased).filter(Paperwork.description.like('%#%')).all(),
                    [c1, c2]
                )

                eq_(
                    sess.query(Company).\
                        join('employees', 'paperwork', aliased=aliased).filter(Person.name.in_(['dilbert', 'vlad'])).filter(Paperwork.description.like('%#2%')).all(),
                    [c1]
                )
        
                eq_(
                    sess.query(Company).\
                        join('employees', 'paperwork', aliased=aliased).filter(Person.name.in_(['dilbert', 'vlad'])).filter(Paperwork.description.like('%#%')).all(),
                    [c1, c2]
                )

                eq_(
                    sess.query(Company).join('employees', aliased=aliased).filter(Person.name.in_(['dilbert', 'vlad'])).\
                        join('paperwork', from_joinpoint=True, aliased=aliased).filter(Paperwork.description.like('%#2%')).all(),
                    [c1]
                )

                eq_(
                    sess.query(Company).join('employees', aliased=aliased).filter(Person.name.in_(['dilbert', 'vlad'])).\
                        join('paperwork', from_joinpoint=True, aliased=aliased).filter(Paperwork.description.like('%#%')).all(),
                    [c1, c2]
                )
        def test_explicit_polymorphic_join(self):
            sess = create_session()

            # join from Company to Engineer; join condition formulated by
            # ORMJoin using regular table foreign key connections.  Engineer
            # is expressed as "(select * people join engineers) as anon_1"
            # so the join is contained.
            eq_(
                sess.query(Company).join(Engineer).filter(Engineer.engineer_name=='vlad').one(),
                c2
            )

            # same, using explicit join condition.  Query.join() must adapt the on clause
            # here to match the subquery wrapped around "people join engineers".
            eq_(
                sess.query(Company).join((Engineer, Company.company_id==Engineer.company_id)).filter(Engineer.engineer_name=='vlad').one(),
                c2
            )
                
        
        def test_filter_on_baseclass(self):
            sess = create_session()

            eq_(sess.query(Person).all(), all_employees)

            eq_(sess.query(Person).first(), all_employees[0])
        
            eq_(sess.query(Person).filter(Person.person_id==e2.person_id).one(), e2)
    
        def test_from_alias(self):
            sess = create_session()
            
            palias = aliased(Person)
            eq_(
                sess.query(palias).filter(palias.name.in_(['dilbert', 'wally'])).all(),
                [e1, e2]
            )
            
        def test_self_referential(self):
            sess = create_session()
            
            c1_employees = [e1, e2, b1, m1]
            
            palias = aliased(Person)
            eq_(
                sess.query(Person, palias).filter(Person.company_id==palias.company_id).filter(Person.name=='dogbert').\
                    filter(Person.person_id>palias.person_id).order_by(Person.person_id, palias.person_id).all(), 
                [
                    (m1, e1),
                    (m1, e2),
                    (m1, b1),
                ]
            )

            eq_(
                sess.query(Person, palias).filter(Person.company_id==palias.company_id).filter(Person.name=='dogbert').\
                    filter(Person.person_id>palias.person_id).from_self().order_by(Person.person_id, palias.person_id).all(), 
                [
                    (m1, e1),
                    (m1, e2),
                    (m1, b1),
                ]
            )
        
        def test_nesting_queries(self):
            sess = create_session()
            
            # query.statement places a flag "no_adapt" on the returned statement.  This prevents
            # the polymorphic adaptation in the second "filter" from hitting it, which would pollute 
            # the subquery and usually results in recursion overflow errors within the adaption.
            subq = sess.query(engineers.c.person_id).filter(Engineer.primary_language=='java').statement.as_scalar()
            
            eq_(sess.query(Person).filter(Person.person_id==subq).one(), e1)
            
        def test_mixed_entities(self):
            sess = create_session()

            eq_(
                sess.query(Company.name, Person).join(Company.employees).filter(Company.name=='Elbonia, Inc.').all(),
                [(u'Elbonia, Inc.', 
                    Engineer(status=u'elbonian engineer',engineer_name=u'vlad',name=u'vlad',primary_language=u'cobol'))]
            )

            eq_(
                sess.query(Person, Company.name).join(Company.employees).filter(Company.name=='Elbonia, Inc.').all(),
                [(Engineer(status=u'elbonian engineer',engineer_name=u'vlad',name=u'vlad',primary_language=u'cobol'),
                    u'Elbonia, Inc.')]
            )
            
            
            eq_(
                sess.query(Manager.name).all(), 
                [('pointy haired boss', ), ('dogbert',)]
            )

            eq_(
                sess.query(Manager.name + " foo").all(), 
                [('pointy haired boss foo', ), ('dogbert foo',)]
            )

            row = sess.query(Engineer.name, Engineer.primary_language).filter(Engineer.name=='dilbert').first()
            assert row.name == 'dilbert'
            assert row.primary_language == 'java'
            

            eq_(
                sess.query(Engineer.name, Engineer.primary_language).all(),
                [(u'dilbert', u'java'), (u'wally', u'c++'), (u'vlad', u'cobol')]
            )

            eq_(
                sess.query(Boss.name, Boss.golf_swing).all(),
                [(u'pointy haired boss', u'fore')]
            )
            
            # TODO: I think raise error on these for now.  different inheritance/loading schemes have different
            # results here, all incorrect
            #
            # self.assertEquals(
            #    sess.query(Person.name, Engineer.primary_language).all(),
            #    []
            # )
            
            # self.assertEquals(
            #    sess.query(Person.name, Engineer.primary_language, Manager.manager_name).all(),
            #    []
            # )

            eq_(
                sess.query(Person.name, Company.name).join(Company.employees).filter(Company.name=='Elbonia, Inc.').all(),
                [(u'vlad',u'Elbonia, Inc.')]
            )

            eq_(
                sess.query(Engineer.primary_language).filter(Person.type=='engineer').all(),
                [(u'java',), (u'c++',), (u'cobol',)]
            )

            if select_type != '':
                eq_(
                    sess.query(Engineer, Company.name).join(Company.employees).filter(Person.type=='engineer').all(),
                    [
                    (Engineer(status=u'regular engineer',engineer_name=u'dilbert',name=u'dilbert',company_id=1,primary_language=u'java',person_id=1,type=u'engineer'), u'MegaCorp, Inc.'), 
                    (Engineer(status=u'regular engineer',engineer_name=u'wally',name=u'wally',company_id=1,primary_language=u'c++',person_id=2,type=u'engineer'), u'MegaCorp, Inc.'), 
                    (Engineer(status=u'elbonian engineer',engineer_name=u'vlad',name=u'vlad',company_id=2,primary_language=u'cobol',person_id=5,type=u'engineer'), u'Elbonia, Inc.')
                    ]
                )
            
                eq_(
                    sess.query(Engineer.primary_language, Company.name).join(Company.employees).filter(Person.type=='engineer').order_by(desc(Engineer.primary_language)).all(),
                    [(u'java', u'MegaCorp, Inc.'), (u'cobol', u'Elbonia, Inc.'), (u'c++', u'MegaCorp, Inc.')]
                )

            palias = aliased(Person)
            eq_(
                sess.query(Person, Company.name, palias).join(Company.employees).filter(Company.name=='Elbonia, Inc.').filter(palias.name=='dilbert').all(),
                [(Engineer(status=u'elbonian engineer',engineer_name=u'vlad',name=u'vlad',primary_language=u'cobol'),
                    u'Elbonia, Inc.', 
                    Engineer(status=u'regular engineer',engineer_name=u'dilbert',name=u'dilbert',company_id=1,primary_language=u'java',person_id=1,type=u'engineer'))]
            )

            eq_(
                sess.query(palias, Company.name, Person).join(Company.employees).filter(Company.name=='Elbonia, Inc.').filter(palias.name=='dilbert').all(),
                [(Engineer(status=u'regular engineer',engineer_name=u'dilbert',name=u'dilbert',company_id=1,primary_language=u'java',person_id=1,type=u'engineer'),
                    u'Elbonia, Inc.', 
                    Engineer(status=u'elbonian engineer',engineer_name=u'vlad',name=u'vlad',primary_language=u'cobol'),)
                ]
            )

            eq_(
                sess.query(Person.name, Company.name, palias.name).join(Company.employees).filter(Company.name=='Elbonia, Inc.').filter(palias.name=='dilbert').all(),
                [(u'vlad', u'Elbonia, Inc.', u'dilbert')]
            )
            
            palias = aliased(Person)
            eq_(
                sess.query(Person.type, Person.name, palias.type, palias.name).filter(Person.company_id==palias.company_id).filter(Person.name=='dogbert').\
                    filter(Person.person_id>palias.person_id).order_by(Person.person_id, palias.person_id).all(), 
                [(u'manager', u'dogbert', u'engineer', u'dilbert'), 
                (u'manager', u'dogbert', u'engineer', u'wally'), 
                (u'manager', u'dogbert', u'boss', u'pointy haired boss')]
            )
        
            eq_(
                sess.query(Person.name, Paperwork.description).filter(Person.person_id==Paperwork.person_id).order_by(Person.name, Paperwork.description).all(), 
                [(u'dilbert', u'tps report #1'), (u'dilbert', u'tps report #2'), (u'dogbert', u'review #2'), 
                (u'dogbert', u'review #3'), 
                (u'pointy haired boss', u'review #1'), 
                (u'vlad', u'elbonian missive #3'),
                (u'wally', u'tps report #3'), 
                (u'wally', u'tps report #4'),
                ]
            )

            if select_type != '':
                eq_(
                    sess.query(func.count(Person.person_id)).filter(Engineer.primary_language=='java').all(), 
                    [(1, )]
                )
            
            eq_(
                sess.query(Company.name, func.count(Person.person_id)).filter(Company.company_id==Person.company_id).group_by(Company.name).order_by(Company.name).all(),
                [(u'Elbonia, Inc.', 1), (u'MegaCorp, Inc.', 4)]
            )

            eq_(
                sess.query(Company.name, func.count(Person.person_id)).join(Company.employees).group_by(Company.name).order_by(Company.name).all(),
                [(u'Elbonia, Inc.', 1), (u'MegaCorp, Inc.', 4)]
            )
    
    
    PolymorphicQueryTest.__name__ = "Polymorphic%sTest" % select_type
    return PolymorphicQueryTest

for select_type in ('', 'Polymorphic', 'Unions', 'AliasedJoins', 'Joins'):
    testclass = _produce_test(select_type)
    exec("%s = testclass" % testclass.__name__)
    
del testclass

class SelfReferentialTestJoinedToBase(_base.MappedTest):
    run_setup_mappers = 'once'
    
    @classmethod
    def define_tables(cls, metadata):
        global people, engineers
        people = Table('people', metadata,
           Column('person_id', Integer, primary_key=True, test_needs_autoincrement=True),
           Column('name', String(50)),
           Column('type', String(30)))

        engineers = Table('engineers', metadata,
           Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
           Column('primary_language', String(50)),
           Column('reports_to_id', Integer, ForeignKey('people.person_id'))
          )

    @classmethod
    def setup_mappers(cls):
        mapper(Person, people, polymorphic_on=people.c.type, polymorphic_identity='person')
        mapper(Engineer, engineers, inherits=Person, 
          inherit_condition=engineers.c.person_id==people.c.person_id,
          polymorphic_identity='engineer', properties={
          'reports_to':relationship(Person, primaryjoin=people.c.person_id==engineers.c.reports_to_id)
        })
    
    def test_has(self):
        
        p1 = Person(name='dogbert')
        e1 = Engineer(name='dilbert', primary_language='java', reports_to=p1)
        sess = create_session()
        sess.add(p1)
        sess.add(e1)
        sess.flush()
        sess.expunge_all()
        
        eq_(sess.query(Engineer).filter(Engineer.reports_to.has(Person.name=='dogbert')).first(), Engineer(name='dilbert'))

    def test_oftype_aliases_in_exists(self):
        e1 = Engineer(name='dilbert', primary_language='java')
        e2 = Engineer(name='wally', primary_language='c++', reports_to=e1)
        sess = create_session()
        sess.add_all([e1, e2])
        sess.flush()
        
        eq_(sess.query(Engineer).filter(Engineer.reports_to.of_type(Engineer).has(Engineer.name=='dilbert')).first(), e2)
        
    def test_join(self):
        p1 = Person(name='dogbert')
        e1 = Engineer(name='dilbert', primary_language='java', reports_to=p1)
        sess = create_session()
        sess.add(p1)
        sess.add(e1)
        sess.flush()
        sess.expunge_all()
        
        eq_(
            sess.query(Engineer).join('reports_to', aliased=True).filter(Person.name=='dogbert').first(), 
            Engineer(name='dilbert'))

class SelfReferentialJ2JTest(_base.MappedTest):
    run_setup_mappers = 'once'

    @classmethod
    def define_tables(cls, metadata):
        global people, engineers, managers
        people = Table('people', metadata,
           Column('person_id', Integer, primary_key=True, test_needs_autoincrement=True),
           Column('name', String(50)),
           Column('type', String(30)))

        engineers = Table('engineers', metadata,
           Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
           Column('primary_language', String(50)),
           Column('reports_to_id', Integer, ForeignKey('managers.person_id'))
          )
          
        managers = Table('managers', metadata,
            Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
        )

    @classmethod
    def setup_mappers(cls):
        mapper(Person, people, polymorphic_on=people.c.type, polymorphic_identity='person')
        mapper(Manager, managers, inherits=Person, polymorphic_identity='manager')
        
        mapper(Engineer, engineers, inherits=Person, 
          polymorphic_identity='engineer', properties={
          'reports_to':relationship(Manager, primaryjoin=managers.c.person_id==engineers.c.reports_to_id, backref='engineers')
        })

    def test_has(self):

        m1 = Manager(name='dogbert')
        e1 = Engineer(name='dilbert', primary_language='java', reports_to=m1)
        sess = create_session()
        sess.add(m1)
        sess.add(e1)
        sess.flush()
        sess.expunge_all()

        eq_(sess.query(Engineer).filter(Engineer.reports_to.has(Manager.name=='dogbert')).first(), Engineer(name='dilbert'))

    def test_join(self):
        m1 = Manager(name='dogbert')
        e1 = Engineer(name='dilbert', primary_language='java', reports_to=m1)
        sess = create_session()
        sess.add(m1)
        sess.add(e1)
        sess.flush()
        sess.expunge_all()

        eq_(
            sess.query(Engineer).join('reports_to', aliased=True).filter(Manager.name=='dogbert').first(), 
            Engineer(name='dilbert'))
    
    def test_filter_aliasing(self):
        m1 = Manager(name='dogbert')
        m2 = Manager(name='foo')
        e1 = Engineer(name='wally', primary_language='java', reports_to=m1)
        e2 = Engineer(name='dilbert', primary_language='c++', reports_to=m2)
        e3 = Engineer(name='etc', primary_language='c++')
        sess = create_session()
        sess.add_all([m1, m2, e1, e2, e3])
        sess.flush()
        sess.expunge_all()

        # filter aliasing applied to Engineer doesn't whack Manager
        eq_(
            sess.query(Manager).join(Manager.engineers).filter(Manager.name=='dogbert').all(),
            [m1]
        )

        eq_(
            sess.query(Manager).join(Manager.engineers).filter(Engineer.name=='dilbert').all(),
            [m2]
        )

        eq_(
            sess.query(Manager, Engineer).join(Manager.engineers).order_by(Manager.name.desc()).all(),
            [
                (m2, e2),
                (m1, e1),
            ]
        )
        
    def test_relationship_compare(self):
        m1 = Manager(name='dogbert')
        m2 = Manager(name='foo')
        e1 = Engineer(name='dilbert', primary_language='java', reports_to=m1)
        e2 = Engineer(name='wally', primary_language='c++', reports_to=m2)
        e3 = Engineer(name='etc', primary_language='c++')
        sess = create_session()
        sess.add(m1)
        sess.add(m2)
        sess.add(e1)
        sess.add(e2)
        sess.add(e3)
        sess.flush()
        sess.expunge_all()

        eq_(
            sess.query(Manager).join(Manager.engineers).filter(Engineer.reports_to==None).all(), 
            []
        )

        eq_(
            sess.query(Manager).join(Manager.engineers).filter(Engineer.reports_to==m1).all(), 
            [m1]
        )

        

class M2MFilterTest(_base.MappedTest):
    run_setup_mappers = 'once'
    run_inserts = 'once'
    run_deletes = None
    
    @classmethod
    def define_tables(cls, metadata):
        global people, engineers, organizations, engineers_to_org
        
        organizations = Table('organizations', metadata,
            Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
            Column('name', String(50)),
            )
        engineers_to_org = Table('engineers_org', metadata,
            Column('org_id', Integer, ForeignKey('organizations.id')),
            Column('engineer_id', Integer, ForeignKey('engineers.person_id')),
        )
        
        people = Table('people', metadata,
           Column('person_id', Integer, primary_key=True, test_needs_autoincrement=True),
           Column('name', String(50)),
           Column('type', String(30)))

        engineers = Table('engineers', metadata,
           Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
           Column('primary_language', String(50)),
          )

    @classmethod
    def setup_mappers(cls):
        global Organization
        class Organization(_fixtures.Base):
            pass
            
        mapper(Organization, organizations, properties={
            'engineers':relationship(Engineer, secondary=engineers_to_org, backref='organizations')
        })
        
        mapper(Person, people, polymorphic_on=people.c.type, polymorphic_identity='person')
        mapper(Engineer, engineers, inherits=Person, polymorphic_identity='engineer')
    
    @classmethod
    def insert_data(cls):
        e1 = Engineer(name='e1')
        e2 = Engineer(name='e2')
        e3 = Engineer(name='e3')
        e4 = Engineer(name='e4')
        org1 = Organization(name='org1', engineers=[e1, e2])
        org2 = Organization(name='org2', engineers=[e3, e4])
        
        sess = create_session()
        sess.add(org1)
        sess.add(org2)
        sess.flush()
        
    def test_not_contains(self):
        sess = create_session()
        
        e1 = sess.query(Person).filter(Engineer.name=='e1').one()
        
        # this works
        eq_(sess.query(Organization).filter(~Organization.engineers.of_type(Engineer).contains(e1)).all(), [Organization(name='org2')])

        # this had a bug
        eq_(sess.query(Organization).filter(~Organization.engineers.contains(e1)).all(), [Organization(name='org2')])
    
    def test_any(self):
        sess = create_session()
        eq_(sess.query(Organization).filter(Organization.engineers.of_type(Engineer).any(Engineer.name=='e1')).all(), [Organization(name='org1')])
        eq_(sess.query(Organization).filter(Organization.engineers.any(Engineer.name=='e1')).all(), [Organization(name='org1')])

class SelfReferentialM2MTest(_base.MappedTest, AssertsCompiledSQL):
    run_setup_mappers = 'once'
    
    @classmethod
    def define_tables(cls, metadata):
        global Parent, Child1, Child2

        Base = declarative_base(metadata=metadata)

        secondary_table = Table('secondary', Base.metadata,
           Column('left_id', Integer, ForeignKey('parent.id'), nullable=False),
           Column('right_id', Integer, ForeignKey('parent.id'), nullable=False))

        class Parent(Base):
           __tablename__ = 'parent'
           id = Column(Integer, primary_key=True, test_needs_autoincrement=True)
           cls = Column(String(50))
           __mapper_args__ = dict(polymorphic_on = cls )

        class Child1(Parent):
           __tablename__ = 'child1'
           id = Column(Integer, ForeignKey('parent.id'), primary_key=True)
           __mapper_args__ = dict(polymorphic_identity = 'child1')

        class Child2(Parent):
           __tablename__ = 'child2'
           id = Column(Integer, ForeignKey('parent.id'), primary_key=True)
           __mapper_args__ = dict(polymorphic_identity = 'child2')

        Child1.left_child2 = relationship(Child2, secondary = secondary_table,
               primaryjoin = Parent.id == secondary_table.c.right_id,
               secondaryjoin = Parent.id == secondary_table.c.left_id,
               uselist = False, backref="right_children"
                               )

    
    def test_query_crit(self):
        session = create_session()
        c11, c12, c13 = Child1(), Child1(), Child1()
        c21, c22, c23 = Child2(), Child2(), Child2()
        
        c11.left_child2 = c22
        c12.left_child2 = c22
        c13.left_child2 = c23
        
        session.add_all([c11, c12, c13, c21, c22, c23])
        session.flush()
        
        # test that the join to Child2 doesn't alias Child1 in the select
        eq_(
            set(session.query(Child1).join(Child1.left_child2)), 
            set([c11, c12, c13])
        )

        eq_(
            set(session.query(Child1, Child2).join(Child1.left_child2)), 
            set([(c11, c22), (c12, c22), (c13, c23)])
        )

        # test __eq__() on property is annotating correctly
        eq_(
            set(session.query(Child2).join(Child2.right_children).filter(Child1.left_child2==c22)),
            set([c22])
        )

        # test the same again
        self.assert_compile(
            session.query(Child2).join(Child2.right_children).filter(Child1.left_child2==c22).with_labels().statement,
            "SELECT parent.id AS parent_id, child2.id AS child2_id, parent.cls AS parent_cls FROM "
            "secondary AS secondary_1, parent JOIN child2 ON parent.id = child2.id JOIN secondary AS secondary_2 "
            "ON parent.id = secondary_2.left_id JOIN (SELECT parent.id AS parent_id, parent.cls AS parent_cls, "
            "child1.id AS child1_id FROM parent JOIN child1 ON parent.id = child1.id) AS anon_1 ON "
            "anon_1.parent_id = secondary_2.right_id WHERE anon_1.parent_id = secondary_1.right_id AND :param_1 = secondary_1.left_id",
            dialect=default.DefaultDialect()
        )

    def test_eager_join(self):
        session = create_session()
        
        c1 = Child1()
        c1.left_child2 = Child2()
        session.add(c1)
        session.flush()
        
        q = session.query(Child1).options(joinedload('left_child2'))

        # test that the splicing of the join works here, doesnt break in the middle of "parent join child1"
        self.assert_compile(q.limit(1).with_labels().statement, 
        "SELECT anon_1.parent_id AS anon_1_parent_id, anon_1.child1_id AS anon_1_child1_id, "\
        "anon_1.parent_cls AS anon_1_parent_cls, anon_2.parent_id AS anon_2_parent_id, "\
        "anon_2.child2_id AS anon_2_child2_id, anon_2.parent_cls AS anon_2_parent_cls FROM "\
        "(SELECT parent.id AS parent_id, child1.id AS child1_id, parent.cls AS parent_cls FROM parent "\
        "JOIN child1 ON parent.id = child1.id  LIMIT 1) AS anon_1 LEFT OUTER JOIN secondary AS secondary_1 "\
        "ON anon_1.parent_id = secondary_1.right_id LEFT OUTER JOIN (SELECT parent.id AS parent_id, "\
        "parent.cls AS parent_cls, child2.id AS child2_id FROM parent JOIN child2 ON parent.id = child2.id) "\
        "AS anon_2 ON anon_2.parent_id = secondary_1.left_id"
        , dialect=default.DefaultDialect())

        # another way to check
        assert q.limit(1).with_labels().subquery().count().scalar() == 1
        
        assert q.first() is c1
    
    def test_subquery_load(self):
        session = create_session()
        
        c1 = Child1()
        c1.left_child2 = Child2()
        session.add(c1)
        session.flush()
        session.expunge_all()
        
        for row in session.query(Child1).options(subqueryload('left_child2')).all():
            assert row.left_child2
        
class EagerToSubclassTest(_base.MappedTest):
    """Test joinedloads to subclass mappers"""

    run_setup_classes = 'once'
    run_setup_mappers = 'once'
    run_inserts = 'once'
    run_deletes = None

    @classmethod
    def define_tables(cls, metadata):
        Table('parent', metadata,
            Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
            Column('data', String(10)),
        )

        Table('base', metadata,
            Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
            Column('type', String(10)),
        )

        Table('sub', metadata,
            Column('id', Integer, ForeignKey('base.id'), primary_key=True),
            Column('data', String(10)),
            Column('parent_id', Integer, ForeignKey('parent.id'), nullable=False)
        )

    @classmethod
    @testing.resolve_artifact_names
    def setup_classes(cls):
        class Parent(_base.ComparableEntity):
            pass

        class Base(_base.ComparableEntity):
            pass

        class Sub(Base):
            pass

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Parent, parent, properties={
            'children':relationship(Sub)
        })
        mapper(Base, base, polymorphic_on=base.c.type, polymorphic_identity='b')
        mapper(Sub, sub, inherits=Base, polymorphic_identity='s')

    @classmethod
    @testing.resolve_artifact_names
    def insert_data(cls):
        sess = create_session()
        p1 = Parent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')])
        p2 = Parent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
        sess.add(p1)
        sess.add(p2)
        sess.flush()

    @testing.resolve_artifact_names
    def test_joinedload(self):
        sess = create_session()
        def go():
            eq_(
                sess.query(Parent).options(joinedload(Parent.children)).all(), 
                [
                    Parent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Parent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_contains_eager(self):
        sess = create_session()
        def go():
            eq_(
                sess.query(Parent).join(Parent.children).options(contains_eager(Parent.children)).\
                                order_by(Parent.data, Sub.data).all(), 
                [
                    Parent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Parent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 1)

class SubClassEagerToSubClassTest(_base.MappedTest):
    """Test joinedloads from subclass to subclass mappers"""

    run_setup_classes = 'once'
    run_setup_mappers = 'once'
    run_inserts = 'once'
    run_deletes = None

    @classmethod
    def define_tables(cls, metadata):
        Table('parent', metadata,
            Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
            Column('type', String(10)),
        )

        Table('subparent', metadata,
            Column('id', Integer, ForeignKey('parent.id'), primary_key=True),
            Column('data', String(10)),
        )

        Table('base', metadata,
            Column('id', Integer, primary_key=True, test_needs_autoincrement=True),
            Column('type', String(10)),
        )

        Table('sub', metadata,
            Column('id', Integer, ForeignKey('base.id'), primary_key=True),
            Column('data', String(10)),
            Column('subparent_id', Integer, ForeignKey('subparent.id'), nullable=False)
        )

    @classmethod
    @testing.resolve_artifact_names
    def setup_classes(cls):
        class Parent(_base.ComparableEntity):
            pass

        class Subparent(Parent):
            pass

        class Base(_base.ComparableEntity):
            pass

        class Sub(Base):
            pass

    @classmethod
    @testing.resolve_artifact_names
    def setup_mappers(cls):
        mapper(Parent, parent, polymorphic_on=parent.c.type, polymorphic_identity='b')
        mapper(Subparent, subparent, inherits=Parent, polymorphic_identity='s', properties={
            'children':relationship(Sub, order_by=base.c.id)
        })
        mapper(Base, base, polymorphic_on=base.c.type, polymorphic_identity='b')
        mapper(Sub, sub, inherits=Base, polymorphic_identity='s')

    @classmethod
    @testing.resolve_artifact_names
    def insert_data(cls):
        sess = create_session()
        p1 = Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')])
        p2 = Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
        sess.add(p1)
        sess.add(p2)
        sess.flush()

    @testing.resolve_artifact_names
    def test_joinedload(self):
        sess = create_session()
        def go():
            eq_(
                sess.query(Subparent).options(joinedload(Subparent.children)).all(), 
                [
                    Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 1)

        sess.expunge_all()
        def go():
            eq_(
                sess.query(Subparent).options(joinedload("children")).all(), 
                [
                    Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_contains_eager(self):
        sess = create_session()
        def go():
            eq_(
                sess.query(Subparent).join(Subparent.children).options(contains_eager(Subparent.children)).all(), 
                [
                    Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 1)
        sess.expunge_all()

        def go():
            eq_(
                sess.query(Subparent).join(Subparent.children).options(contains_eager("children")).all(), 
                [
                    Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 1)

    @testing.resolve_artifact_names
    def test_subqueryload(self):
        sess = create_session()
        def go():
            eq_(
                sess.query(Subparent).options(subqueryload(Subparent.children)).all(), 
                [
                    Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 2)

        sess.expunge_all()
        def go():
            eq_(
                sess.query(Subparent).options(subqueryload("children")).all(), 
                [
                    Subparent(data='p1', children=[Sub(data='s1'), Sub(data='s2'), Sub(data='s3')]),
                    Subparent(data='p2', children=[Sub(data='s4'), Sub(data='s5')])
                ]
            )
        self.assert_sql_count(testing.db, go, 2)

