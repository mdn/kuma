"""Tests exceptions and DB-API exception wrapping."""


from sqlalchemy import exc as sa_exceptions
from sqlalchemy.test import TestBase

# Py3K 
#StandardError = BaseException 
# Py2K
from exceptions import StandardError, KeyboardInterrupt, SystemExit
# end Py2K


class Error(StandardError):
    """This class will be old-style on <= 2.4 and new-style on >=
    2.5."""


class DatabaseError(Error):
    pass


class OperationalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    def __str__(self):
        return '<%s>' % self.bogus


class OutOfSpec(DatabaseError):
    pass


class WrapTest(TestBase):

    def test_db_error_normal(self):
        try:
            raise sa_exceptions.DBAPIError.instance('', [],
                    OperationalError())
        except sa_exceptions.DBAPIError:
            self.assert_(True)

    def test_tostring(self):
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message'
                    , None, OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc) \
                == "(OperationalError)  'this is a message' None"

    def test_tostring_large_dict(self):
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message'
                    , 
                {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h':
                8, 'i': 9, 'j': 10, 'k': 11,
                }, OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc).startswith("(OperationalError)  'this is a "
                    "message' {")

    def test_tostring_large_list(self):
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message', 
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,], OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc).startswith("(OperationalError)  'this is a "
                    "message' [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]")

    def test_tostring_large_executemany(self):
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message', 
                [{1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, 
                {1: 1}, {1:1}, {1: 1}, {1: 1},], 
                OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc) \
                == "(OperationalError)  'this is a message' [{1: 1}, "\
                "{1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: "\
                "1}, {1: 1}, {1: 1}]", str(exc)
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message', [
                {1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, {1: 1}, 
                {1:1}, {1: 1}, {1: 1}, {1: 1},
                ], OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc) \
                == "(OperationalError)  'this is a message' [{1: 1}, "\
                "{1: 1}] ... and a total of 11 bound parameter sets"
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message', 
                [
                (1, ), (1, ), (1, ), (1, ), (1, ), (1, ), (1, ), (1, ), (1, ),
                (1, ),
                ], OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc) \
                == "(OperationalError)  'this is a message' [(1,), "\
                "(1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,)]"
        try:
            raise sa_exceptions.DBAPIError.instance('this is a message', [
                (1, ), (1, ), (1, ), (1, ), (1, ), (1, ), (1, ), (1, ), (1, ),
                (1, ), (1, ),
                ], OperationalError())
        except sa_exceptions.DBAPIError, exc:
            assert str(exc) \
                == "(OperationalError)  'this is a message' [(1,), "\
                "(1,)] ... and a total of 11 bound parameter sets"

    def test_db_error_busted_dbapi(self):
        try:
            raise sa_exceptions.DBAPIError.instance('', [],
                    ProgrammingError())
        except sa_exceptions.DBAPIError, e:
            self.assert_(True)
            self.assert_('Error in str() of DB-API' in e.args[0])

    def test_db_error_noncompliant_dbapi(self):
        try:
            raise sa_exceptions.DBAPIError.instance('', [], OutOfSpec())
        except sa_exceptions.DBAPIError, e:
            self.assert_(e.__class__ is sa_exceptions.DBAPIError)
        except OutOfSpec:
            self.assert_(False)

        # Make sure the DatabaseError recognition logic is limited to
        # subclasses of sqlalchemy.exceptions.DBAPIError

        try:
            raise sa_exceptions.DBAPIError.instance('', [],
                    sa_exceptions.ArgumentError())
        except sa_exceptions.DBAPIError, e:
            self.assert_(e.__class__ is sa_exceptions.DBAPIError)
        except sa_exceptions.ArgumentError:
            self.assert_(False)

    def test_db_error_keyboard_interrupt(self):
        try:
            raise sa_exceptions.DBAPIError.instance('', [],
                    KeyboardInterrupt())
        except sa_exceptions.DBAPIError:
            self.assert_(False)
        except KeyboardInterrupt:
            self.assert_(True)

    def test_db_error_system_exit(self):
        try:
            raise sa_exceptions.DBAPIError.instance('', [],
                    SystemExit())
        except sa_exceptions.DBAPIError:
            self.assert_(False)
        except SystemExit:
            self.assert_(True)
