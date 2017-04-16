# mssql.py

"""Support for the Microsoft SQL Server database.

Connecting
----------

See the individual driver sections below for details on connecting.

Auto Increment Behavior
-----------------------

``IDENTITY`` columns are supported by using SQLAlchemy
``schema.Sequence()`` objects. In other words::

    from sqlalchemy import Table, Integer, Sequence, Column
    
    Table('test', metadata,
           Column('id', Integer,
                  Sequence('blah',100,10), primary_key=True),
           Column('name', String(20))
         ).create(some_engine)

would yield::

   CREATE TABLE test (
     id INTEGER NOT NULL IDENTITY(100,10) PRIMARY KEY,
     name VARCHAR(20) NULL,
     )

Note that the ``start`` and ``increment`` values for sequences are
optional and will default to 1,1.

Implicit ``autoincrement`` behavior works the same in MSSQL as it
does in other dialects and results in an ``IDENTITY`` column.

* Support for ``SET IDENTITY_INSERT ON`` mode (automagic on / off for
  ``INSERT`` s)

* Support for auto-fetching of ``@@IDENTITY/@@SCOPE_IDENTITY()`` on
  ``INSERT``

Collation Support
-----------------

MSSQL specific string types support a collation parameter that
creates a column-level specific collation for the column. The
collation parameter accepts a Windows Collation Name or a SQL
Collation Name. Supported types are MSChar, MSNChar, MSString,
MSNVarchar, MSText, and MSNText. For example::

    from sqlalchemy.dialects.mssql import VARCHAR
    Column('login', VARCHAR(32, collation='Latin1_General_CI_AS'))

When such a column is associated with a :class:`Table`, the
CREATE TABLE statement for this column will yield::

    login VARCHAR(32) COLLATE Latin1_General_CI_AS NULL

LIMIT/OFFSET Support
--------------------

MSSQL has no support for the LIMIT or OFFSET keysowrds. LIMIT is
supported directly through the ``TOP`` Transact SQL keyword::

    select.limit

will yield::

    SELECT TOP n

If using SQL Server 2005 or above, LIMIT with OFFSET
support is available through the ``ROW_NUMBER OVER`` construct. 
For versions below 2005, LIMIT with OFFSET usage will fail.

Nullability
-----------
MSSQL has support for three levels of column nullability. The default
nullability allows nulls and is explicit in the CREATE TABLE
construct::

    name VARCHAR(20) NULL

If ``nullable=None`` is specified then no specification is made. In
other words the database's configured default is used. This will
render::

    name VARCHAR(20)

If ``nullable`` is ``True`` or ``False`` then the column will be
``NULL` or ``NOT NULL`` respectively.

Date / Time Handling
--------------------
DATE and TIME are supported.   Bind parameters are converted
to datetime.datetime() objects as required by most MSSQL drivers,
and results are processed from strings if needed.
The DATE and TIME types are not available for MSSQL 2005 and
previous - if a server version below 2008 is detected, DDL
for these types will be issued as DATETIME.

Compatibility Levels
--------------------
MSSQL supports the notion of setting compatibility levels at the
database level. This allows, for instance, to run a database that
is compatibile with SQL2000 while running on a SQL2005 database
server. ``server_version_info`` will always return the database
server version information (in this case SQL2005) and not the
compatibiility level information. Because of this, if running under
a backwards compatibility mode SQAlchemy may attempt to use T-SQL
statements that are unable to be parsed by the database server.

Known Issues
------------

* No support for more than one ``IDENTITY`` column per table

"""
import datetime, decimal, inspect, operator, sys, re
import itertools

from sqlalchemy import sql, schema as sa_schema, exc, util
from sqlalchemy.sql import select, compiler, expression, \
                            operators as sql_operators, \
                            functions as sql_functions, util as sql_util
from sqlalchemy.engine import default, base, reflection
from sqlalchemy import types as sqltypes
from sqlalchemy import processors
from sqlalchemy.types import INTEGER, BIGINT, SMALLINT, DECIMAL, NUMERIC, \
                                FLOAT, TIMESTAMP, DATETIME, DATE, BINARY,\
                                VARBINARY, BLOB

from sqlalchemy.dialects.mssql import information_schema as ischema

MS_2008_VERSION = (10,)
MS_2005_VERSION = (9,)
MS_2000_VERSION = (8,)

RESERVED_WORDS = set(
    ['add', 'all', 'alter', 'and', 'any', 'as', 'asc', 'authorization',
     'backup', 'begin', 'between', 'break', 'browse', 'bulk', 'by', 'cascade',
     'case', 'check', 'checkpoint', 'close', 'clustered', 'coalesce',
     'collate', 'column', 'commit', 'compute', 'constraint', 'contains',
     'containstable', 'continue', 'convert', 'create', 'cross', 'current',
     'current_date', 'current_time', 'current_timestamp', 'current_user',
     'cursor', 'database', 'dbcc', 'deallocate', 'declare', 'default',
     'delete', 'deny', 'desc', 'disk', 'distinct', 'distributed', 'double',
     'drop', 'dump', 'else', 'end', 'errlvl', 'escape', 'except', 'exec',
     'execute', 'exists', 'exit', 'external', 'fetch', 'file', 'fillfactor',
     'for', 'foreign', 'freetext', 'freetexttable', 'from', 'full',
     'function', 'goto', 'grant', 'group', 'having', 'holdlock', 'identity',
     'identity_insert', 'identitycol', 'if', 'in', 'index', 'inner', 'insert',
     'intersect', 'into', 'is', 'join', 'key', 'kill', 'left', 'like',
     'lineno', 'load', 'merge', 'national', 'nocheck', 'nonclustered', 'not',
     'null', 'nullif', 'of', 'off', 'offsets', 'on', 'open', 'opendatasource',
     'openquery', 'openrowset', 'openxml', 'option', 'or', 'order', 'outer',
     'over', 'percent', 'pivot', 'plan', 'precision', 'primary', 'print',
     'proc', 'procedure', 'public', 'raiserror', 'read', 'readtext',
     'reconfigure', 'references', 'replication', 'restore', 'restrict',
     'return', 'revert', 'revoke', 'right', 'rollback', 'rowcount',
     'rowguidcol', 'rule', 'save', 'schema', 'securityaudit', 'select',
     'session_user', 'set', 'setuser', 'shutdown', 'some', 'statistics',
     'system_user', 'table', 'tablesample', 'textsize', 'then', 'to', 'top',
     'tran', 'transaction', 'trigger', 'truncate', 'tsequal', 'union',
     'unique', 'unpivot', 'update', 'updatetext', 'use', 'user', 'values',
     'varying', 'view', 'waitfor', 'when', 'where', 'while', 'with',
     'writetext',
    ])


class REAL(sqltypes.Float):
    """A type for ``real`` numbers."""

    __visit_name__ = 'REAL'

    def __init__(self):
        super(REAL, self).__init__(precision=24)

class TINYINT(sqltypes.Integer):
    __visit_name__ = 'TINYINT'


# MSSQL DATE/TIME types have varied behavior, sometimes returning
# strings.  MSDate/TIME check for everything, and always
# filter bind parameters into datetime objects (required by pyodbc,
# not sure about other dialects).

class _MSDate(sqltypes.Date):
    def bind_processor(self, dialect):
        def process(value):
            if type(value) == datetime.date:
                return datetime.datetime(value.year, value.month, value.day)
            else:
                return value
        return process

    _reg = re.compile(r"(\d+)-(\d+)-(\d+)")
    def result_processor(self, dialect, coltype):
        def process(value):
            if isinstance(value, datetime.datetime):
                return value.date()
            elif isinstance(value, basestring):
                return datetime.date(*[
                        int(x or 0) 
                        for x in self._reg.match(value).groups()
                    ])
            else:
                return value
        return process

class TIME(sqltypes.TIME):
    def __init__(self, precision=None, **kwargs):
        self.precision = precision
        super(TIME, self).__init__()

    __zero_date = datetime.date(1900, 1, 1)

    def bind_processor(self, dialect):
        def process(value):
            if isinstance(value, datetime.datetime):
                value = datetime.datetime.combine(
                                self.__zero_date, value.time())
            elif isinstance(value, datetime.time):
                value = datetime.datetime.combine(self.__zero_date, value)
            return value
        return process

    _reg = re.compile(r"(\d+):(\d+):(\d+)(?:\.(\d+))?")
    def result_processor(self, dialect, coltype):
        def process(value):
            if isinstance(value, datetime.datetime):
                return value.time()
            elif isinstance(value, basestring):
                return datetime.time(*[
                        int(x or 0) 
                        for x in self._reg.match(value).groups()])
            else:
                return value
        return process

class _DateTimeBase(object):
    def bind_processor(self, dialect):
        def process(value):
            if type(value) == datetime.date:
                return datetime.datetime(value.year, value.month, value.day)
            else:
                return value
        return process

class _MSDateTime(_DateTimeBase, sqltypes.DateTime):
    pass

class SMALLDATETIME(_DateTimeBase, sqltypes.DateTime):
    __visit_name__ = 'SMALLDATETIME'

class DATETIME2(_DateTimeBase, sqltypes.DateTime):
    __visit_name__ = 'DATETIME2'
    
    def __init__(self, precision=None, **kwargs):
        self.precision = precision


# TODO: is this not an Interval ?
class DATETIMEOFFSET(sqltypes.TypeEngine):
    __visit_name__ = 'DATETIMEOFFSET'
    
    def __init__(self, precision=None, **kwargs):
        self.precision = precision

class _StringType(object):
    """Base for MSSQL string types."""

    def __init__(self, collation=None):
        self.collation = collation

class TEXT(_StringType, sqltypes.TEXT):
    """MSSQL TEXT type, for variable-length text up to 2^31 characters."""

    def __init__(self, *args, **kw):
        """Construct a TEXT.

        :param collation: Optional, a column-level collation for this string
          value. Accepts a Windows Collation Name or a SQL Collation Name.

        """
        collation = kw.pop('collation', None)
        _StringType.__init__(self, collation)
        sqltypes.Text.__init__(self, *args, **kw)

class NTEXT(_StringType, sqltypes.UnicodeText):
    """MSSQL NTEXT type, for variable-length unicode text up to 2^30
    characters."""

    __visit_name__ = 'NTEXT'
    
    def __init__(self, *args, **kwargs):
        """Construct a NTEXT.

        :param collation: Optional, a column-level collation for this string
          value. Accepts a Windows Collation Name or a SQL Collation Name.

        """
        collation = kwargs.pop('collation', None)
        _StringType.__init__(self, collation)
        length = kwargs.pop('length', None)
        sqltypes.UnicodeText.__init__(self, length, **kwargs)


class VARCHAR(_StringType, sqltypes.VARCHAR):
    """MSSQL VARCHAR type, for variable-length non-Unicode data with a maximum
    of 8,000 characters."""

    def __init__(self, *args, **kw):
        """Construct a VARCHAR.

        :param length: Optinal, maximum data length, in characters.

        :param convert_unicode: defaults to False.  If True, convert
          ``unicode`` data sent to the database to a ``str``
          bytestring, and convert bytestrings coming back from the
          database into ``unicode``.

          Bytestrings are encoded using the dialect's
          :attr:`~sqlalchemy.engine.base.Dialect.encoding`, which
          defaults to `utf-8`.

          If False, may be overridden by
          :attr:`sqlalchemy.engine.base.Dialect.convert_unicode`.

        :param collation: Optional, a column-level collation for this string
          value. Accepts a Windows Collation Name or a SQL Collation Name.

        """
        collation = kw.pop('collation', None)
        _StringType.__init__(self, collation)
        sqltypes.VARCHAR.__init__(self, *args, **kw)

class NVARCHAR(_StringType, sqltypes.NVARCHAR):
    """MSSQL NVARCHAR type.

    For variable-length unicode character data up to 4,000 characters."""

    def __init__(self, *args, **kw):
        """Construct a NVARCHAR.

        :param length: Optional, Maximum data length, in characters.

        :param collation: Optional, a column-level collation for this string
          value. Accepts a Windows Collation Name or a SQL Collation Name.

        """
        collation = kw.pop('collation', None)
        _StringType.__init__(self, collation)
        sqltypes.NVARCHAR.__init__(self, *args, **kw)

class CHAR(_StringType, sqltypes.CHAR):
    """MSSQL CHAR type, for fixed-length non-Unicode data with a maximum
    of 8,000 characters."""

    def __init__(self, *args, **kw):
        """Construct a CHAR.

        :param length: Optinal, maximum data length, in characters.

        :param convert_unicode: defaults to False.  If True, convert
          ``unicode`` data sent to the database to a ``str``
          bytestring, and convert bytestrings coming back from the
          database into ``unicode``.

          Bytestrings are encoded using the dialect's
          :attr:`~sqlalchemy.engine.base.Dialect.encoding`, which
          defaults to `utf-8`.

          If False, may be overridden by
          :attr:`sqlalchemy.engine.base.Dialect.convert_unicode`.

        :param collation: Optional, a column-level collation for this string
          value. Accepts a Windows Collation Name or a SQL Collation Name.

        """
        collation = kw.pop('collation', None)
        _StringType.__init__(self, collation)
        sqltypes.CHAR.__init__(self, *args, **kw)

class NCHAR(_StringType, sqltypes.NCHAR):
    """MSSQL NCHAR type.

    For fixed-length unicode character data up to 4,000 characters."""

    def __init__(self, *args, **kw):
        """Construct an NCHAR.

        :param length: Optional, Maximum data length, in characters.

        :param collation: Optional, a column-level collation for this string
          value. Accepts a Windows Collation Name or a SQL Collation Name.

        """
        collation = kw.pop('collation', None)
        _StringType.__init__(self, collation)
        sqltypes.NCHAR.__init__(self, *args, **kw)

class IMAGE(sqltypes.LargeBinary):
    __visit_name__ = 'IMAGE'

class BIT(sqltypes.TypeEngine):
    __visit_name__ = 'BIT'
    

class MONEY(sqltypes.TypeEngine):
    __visit_name__ = 'MONEY'

class SMALLMONEY(sqltypes.TypeEngine):
    __visit_name__ = 'SMALLMONEY'

class UNIQUEIDENTIFIER(sqltypes.TypeEngine):
    __visit_name__ = "UNIQUEIDENTIFIER"

class SQL_VARIANT(sqltypes.TypeEngine):
    __visit_name__ = 'SQL_VARIANT'

# old names.
MSDateTime = _MSDateTime
MSDate = _MSDate
MSReal = REAL
MSTinyInteger = TINYINT
MSTime = TIME
MSSmallDateTime = SMALLDATETIME
MSDateTime2 = DATETIME2
MSDateTimeOffset = DATETIMEOFFSET
MSText = TEXT
MSNText = NTEXT
MSString = VARCHAR
MSNVarchar = NVARCHAR
MSChar = CHAR
MSNChar = NCHAR
MSBinary = BINARY
MSVarBinary = VARBINARY
MSImage = IMAGE
MSBit = BIT
MSMoney = MONEY
MSSmallMoney = SMALLMONEY
MSUniqueIdentifier = UNIQUEIDENTIFIER
MSVariant = SQL_VARIANT

ischema_names = {
    'int' : INTEGER,
    'bigint': BIGINT,
    'smallint' : SMALLINT,
    'tinyint' : TINYINT,
    'varchar' : VARCHAR,
    'nvarchar' : NVARCHAR,
    'char' : CHAR,
    'nchar' : NCHAR,
    'text' : TEXT,
    'ntext' : NTEXT,
    'decimal' : DECIMAL,
    'numeric' : NUMERIC,
    'float' : FLOAT,
    'datetime' : DATETIME,
    'datetime2' : DATETIME2,
    'datetimeoffset' : DATETIMEOFFSET,
    'date': DATE,
    'time': TIME,
    'smalldatetime' : SMALLDATETIME,
    'binary' : BINARY,
    'varbinary' : VARBINARY,
    'bit': BIT,
    'real' : REAL,
    'image' : IMAGE,
    'timestamp': TIMESTAMP,
    'money': MONEY,
    'smallmoney': SMALLMONEY,
    'uniqueidentifier': UNIQUEIDENTIFIER,
    'sql_variant': SQL_VARIANT,
}


class MSTypeCompiler(compiler.GenericTypeCompiler):
    def _extend(self, spec, type_):
        """Extend a string-type declaration with standard SQL
        COLLATE annotations.

        """

        if getattr(type_, 'collation', None):
            collation = 'COLLATE %s' % type_.collation
        else:
            collation = None

        if type_.length:
            spec = spec + "(%d)" % type_.length
        
        return ' '.join([c for c in (spec, collation)
            if c is not None])

    def visit_FLOAT(self, type_):
        precision = getattr(type_, 'precision', None)
        if precision is None:
            return "FLOAT"
        else:
            return "FLOAT(%(precision)s)" % {'precision': precision}

    def visit_REAL(self, type_):
        return "REAL"

    def visit_TINYINT(self, type_):
        return "TINYINT"

    def visit_DATETIMEOFFSET(self, type_):
        if type_.precision:
            return "DATETIMEOFFSET(%s)" % type_.precision
        else:
            return "DATETIMEOFFSET"

    def visit_TIME(self, type_):
        precision = getattr(type_, 'precision', None)
        if precision:
            return "TIME(%s)" % precision
        else:
            return "TIME"

    def visit_DATETIME2(self, type_):
        precision = getattr(type_, 'precision', None)
        if precision:
            return "DATETIME2(%s)" % precision
        else:
            return "DATETIME2"

    def visit_SMALLDATETIME(self, type_):
        return "SMALLDATETIME"

    def visit_unicode(self, type_):
        return self.visit_NVARCHAR(type_)
        
    def visit_unicode_text(self, type_):
        return self.visit_NTEXT(type_)
        
    def visit_NTEXT(self, type_):
        return self._extend("NTEXT", type_)

    def visit_TEXT(self, type_):
        return self._extend("TEXT", type_)

    def visit_VARCHAR(self, type_):
        return self._extend("VARCHAR", type_)

    def visit_CHAR(self, type_):
        return self._extend("CHAR", type_)

    def visit_NCHAR(self, type_):
        return self._extend("NCHAR", type_)

    def visit_NVARCHAR(self, type_):
        return self._extend("NVARCHAR", type_)

    def visit_date(self, type_):
        if self.dialect.server_version_info < MS_2008_VERSION:
            return self.visit_DATETIME(type_)
        else:
            return self.visit_DATE(type_)

    def visit_time(self, type_):
        if self.dialect.server_version_info < MS_2008_VERSION:
            return self.visit_DATETIME(type_)
        else:
            return self.visit_TIME(type_)
            
    def visit_large_binary(self, type_):
        return self.visit_IMAGE(type_)

    def visit_IMAGE(self, type_):
        return "IMAGE"

    def visit_boolean(self, type_):
        return self.visit_BIT(type_)

    def visit_BIT(self, type_):
        return "BIT"

    def visit_MONEY(self, type_):
        return "MONEY"

    def visit_SMALLMONEY(self, type_):
        return 'SMALLMONEY'

    def visit_UNIQUEIDENTIFIER(self, type_):
        return "UNIQUEIDENTIFIER"

    def visit_SQL_VARIANT(self, type_):
        return 'SQL_VARIANT'

class MSExecutionContext(default.DefaultExecutionContext):
    _enable_identity_insert = False
    _select_lastrowid = False
    _result_proxy = None
    _lastrowid = None
    
    def pre_exec(self):
        """Activate IDENTITY_INSERT if needed."""

        if self.isinsert:
            tbl = self.compiled.statement.table
            seq_column = tbl._autoincrement_column
            insert_has_sequence = seq_column is not None
            
            if insert_has_sequence:
                self._enable_identity_insert = \
                        seq_column.key in self.compiled_parameters[0]
            else:
                self._enable_identity_insert = False
            
            self._select_lastrowid = insert_has_sequence and \
                                        not self.compiled.returning and \
                                        not self._enable_identity_insert and \
                                        not self.executemany
            
            if self._enable_identity_insert:
                self.cursor.execute("SET IDENTITY_INSERT %s ON" % 
                    self.dialect.identifier_preparer.format_table(tbl))

    def post_exec(self):
        """Disable IDENTITY_INSERT if enabled."""
        
        if self._select_lastrowid:
            if self.dialect.use_scope_identity:
                self.cursor.execute(
                "SELECT scope_identity() AS lastrowid", ())
            else:
                self.cursor.execute("SELECT @@identity AS lastrowid", ())
            # fetchall() ensures the cursor is consumed without closing it
            row = self.cursor.fetchall()[0]
            self._lastrowid = int(row[0])

        if (self.isinsert or self.isupdate or self.isdelete) and \
                self.compiled.returning:
            self._result_proxy = base.FullyBufferedResultProxy(self)
            
        if self._enable_identity_insert:
            self.cursor.execute(
                        "SET IDENTITY_INSERT %s OFF" %  
                            self.dialect.identifier_preparer.
                                format_table(self.compiled.statement.table)
                        )
        
    def get_lastrowid(self):
        return self._lastrowid
        
    def handle_dbapi_exception(self, e):
        if self._enable_identity_insert:
            try:
                self.cursor.execute(
                        "SET IDENTITY_INSERT %s OFF" % 
                            self.dialect.identifier_preparer.\
                            format_table(self.compiled.statement.table)
                        )
            except:
                pass

    def get_result_proxy(self):
        if self._result_proxy:
            return self._result_proxy
        else:
            return base.ResultProxy(self)

class MSSQLCompiler(compiler.SQLCompiler):
    returning_precedes_values = True
    
    extract_map = util.update_copy(
        compiler.SQLCompiler.extract_map,
        {
        'doy': 'dayofyear',
        'dow': 'weekday',
        'milliseconds': 'millisecond',
        'microseconds': 'microsecond'
    })

    def __init__(self, *args, **kwargs):
        super(MSSQLCompiler, self).__init__(*args, **kwargs)
        self.tablealiases = {}

    def visit_now_func(self, fn, **kw):
        return "CURRENT_TIMESTAMP"
        
    def visit_current_date_func(self, fn, **kw):
        return "GETDATE()"
        
    def visit_length_func(self, fn, **kw):
        return "LEN%s" % self.function_argspec(fn, **kw)
        
    def visit_char_length_func(self, fn, **kw):
        return "LEN%s" % self.function_argspec(fn, **kw)
        
    def visit_concat_op(self, binary, **kw):
        return "%s + %s" % \
                (self.process(binary.left, **kw), 
                self.process(binary.right, **kw))
        
    def visit_match_op(self, binary, **kw):
        return "CONTAINS (%s, %s)" % (
                                        self.process(binary.left, **kw), 
                                        self.process(binary.right, **kw))
        
    def get_select_precolumns(self, select):
        """ MS-SQL puts TOP, it's version of LIMIT here """
        if select._distinct or select._limit:
            s = select._distinct and "DISTINCT " or ""
            
            if select._limit:
                if not select._offset:
                    s += "TOP %s " % (select._limit,)
            return s
        return compiler.SQLCompiler.get_select_precolumns(self, select)

    def limit_clause(self, select):
        # Limit in mssql is after the select keyword
        return ""

    def visit_select(self, select, **kwargs):
        """Look for ``LIMIT`` and OFFSET in a select statement, and if
        so tries to wrap it in a subquery with ``row_number()`` criterion.

        """
        if not getattr(select, '_mssql_visit', None) and select._offset:
            # to use ROW_NUMBER(), an ORDER BY is required.
            orderby = self.process(select._order_by_clause)
            if not orderby:
                raise exc.InvalidRequestError('MSSQL requires an order_by when '
                                              'using an offset.')

            _offset = select._offset
            _limit = select._limit
            select._mssql_visit = True
            select = select.column(
                sql.literal_column("ROW_NUMBER() OVER (ORDER BY %s)" \
                % orderby).label("mssql_rn")
                                   ).order_by(None).alias()

            limitselect = sql.select([c for c in select.c if
                                        c.key!='mssql_rn'])
            limitselect.append_whereclause("mssql_rn>%d" % _offset)
            if _limit is not None:
                limitselect.append_whereclause("mssql_rn<=%d" % 
                                            (_limit + _offset))
            return self.process(limitselect, iswrapper=True, **kwargs)
        else:
            return compiler.SQLCompiler.visit_select(self, select, **kwargs)

    def _schema_aliased_table(self, table):
        if getattr(table, 'schema', None) is not None:
            if table not in self.tablealiases:
                self.tablealiases[table] = table.alias()
            return self.tablealiases[table]
        else:
            return None

    def visit_table(self, table, mssql_aliased=False, **kwargs):
        if mssql_aliased:
            return super(MSSQLCompiler, self).visit_table(table, **kwargs)

        # alias schema-qualified tables
        alias = self._schema_aliased_table(table)
        if alias is not None:
            return self.process(alias, mssql_aliased=True, **kwargs)
        else:
            return super(MSSQLCompiler, self).visit_table(table, **kwargs)

    def visit_alias(self, alias, **kwargs):
        # translate for schema-qualified table aliases
        self.tablealiases[alias.original] = alias
        kwargs['mssql_aliased'] = True
        return super(MSSQLCompiler, self).visit_alias(alias, **kwargs)

    def visit_extract(self, extract, **kw):
        field = self.extract_map.get(extract.field, extract.field)
        return 'DATEPART("%s", %s)' % \
                        (field, self.process(extract.expr, **kw))

    def visit_rollback_to_savepoint(self, savepoint_stmt):
        return ("ROLLBACK TRANSACTION %s" 
                % self.preparer.format_savepoint(savepoint_stmt))

    def visit_column(self, column, result_map=None, **kwargs):
        if column.table is not None and \
            (not self.isupdate and not self.isdelete) or self.is_subquery():
            # translate for schema-qualified table aliases
            t = self._schema_aliased_table(column.table)
            if t is not None:
                converted = expression._corresponding_column_or_error(
                                        t, column)

                if result_map is not None:
                    result_map[column.name.lower()] = \
                                    (column.name, (column, ), 
                                                    column.type)

                return super(MSSQLCompiler, self).\
                                visit_column(converted, 
                                            result_map=None, **kwargs)

        return super(MSSQLCompiler, self).visit_column(column, 
                                                       result_map=result_map, 
                                                       **kwargs)

    def visit_binary(self, binary, **kwargs):
        """Move bind parameters to the right-hand side of an operator, where
        possible.

        """
        if (
            isinstance(binary.left, expression._BindParamClause) 
            and binary.operator == operator.eq
            and not isinstance(binary.right, expression._BindParamClause)
            ):
            return self.process(
                                expression._BinaryExpression(binary.right, 
                                                             binary.left, 
                                                             binary.operator), 
                                **kwargs)
        else:
            if (
                (binary.operator is operator.eq or 
                binary.operator is operator.ne) 
                and (
                    (isinstance(binary.left, expression._FromGrouping) 
                     and isinstance(binary.left.element, 
                                    expression._ScalarSelect)) 
                    or (isinstance(binary.right, expression._FromGrouping) 
                        and isinstance(binary.right.element, 
                                       expression._ScalarSelect)) 
                    or isinstance(binary.left, expression._ScalarSelect) 
                    or isinstance(binary.right, expression._ScalarSelect)
                    )
               ):
                op = binary.operator == operator.eq and "IN" or "NOT IN"
                return self.process(
                        expression._BinaryExpression(binary.left,
                                                     binary.right, op),
                                    **kwargs)
            return super(MSSQLCompiler, self).visit_binary(binary, **kwargs)

    def returning_clause(self, stmt, returning_cols):

        if self.isinsert or self.isupdate:
            target = stmt.table.alias("inserted")
        else:
            target = stmt.table.alias("deleted")
        
        adapter = sql_util.ClauseAdapter(target)
        def col_label(col):
            adapted = adapter.traverse(col)
            if isinstance(col, expression._Label):
                return adapted.label(c.key)
            else:
                return self.label_select_column(None, adapted, asfrom=False)
            
        columns = [
            self.process(
                col_label(c), 
                within_columns_clause=True, 
                result_map=self.result_map
            ) 
            for c in expression._select_iterables(returning_cols)
        ]
        return 'OUTPUT ' + ', '.join(columns)

    def label_select_column(self, select, column, asfrom):
        if isinstance(column, expression.Function):
            return column.label(None)
        else:
            return super(MSSQLCompiler, self).\
                            label_select_column(select, column, asfrom)

    def for_update_clause(self, select):
        # "FOR UPDATE" is only allowed on "DECLARE CURSOR" which 
        # SQLAlchemy doesn't use
        return ''

    def order_by_clause(self, select, **kw):
        order_by = self.process(select._order_by_clause, **kw)

        # MSSQL only allows ORDER BY in subqueries if there is a LIMIT
        if order_by and (not self.is_subquery() or select._limit):
            return " ORDER BY " + order_by
        else:
            return ""

class MSSQLStrictCompiler(MSSQLCompiler):
    """A subclass of MSSQLCompiler which disables the usage of bind
    parameters where not allowed natively by MS-SQL.
    
    A dialect may use this compiler on a platform where native
    binds are used.
    
    """
    ansi_bind_rules = True

    def visit_in_op(self, binary, **kw):
        kw['literal_binds'] = True
        return "%s IN %s" % (
                                self.process(binary.left, **kw), 
                                self.process(binary.right, **kw)
            )

    def visit_notin_op(self, binary, **kw):
        kw['literal_binds'] = True
        return "%s NOT IN %s" % (
                                self.process(binary.left, **kw), 
                                self.process(binary.right, **kw)
            )

    def visit_function(self, func, **kw):
        kw['literal_binds'] = True
        return super(MSSQLStrictCompiler, self).visit_function(func, **kw)

    def render_literal_value(self, value, type_):
        """
        For date and datetime values, convert to a string
        format acceptable to MSSQL. That seems to be the
        so-called ODBC canonical date format which looks
        like this:
        
            yyyy-mm-dd hh:mi:ss.mmm(24h)
        
        For other data types, call the base class implementation.
        """
        # datetime and date are both subclasses of datetime.date
        if issubclass(type(value), datetime.date):
            # SQL Server wants single quotes around the date string.
            return "'" + str(value) + "'"
        else:
            return super(MSSQLStrictCompiler, self).\
                                render_literal_value(value, type_)

class MSDDLCompiler(compiler.DDLCompiler):
    def get_column_specification(self, column, **kwargs):
        colspec = (self.preparer.format_column(column) + " " 
                   + self.dialect.type_compiler.process(column.type))

        if column.nullable is not None:
            if not column.nullable or column.primary_key:
                colspec += " NOT NULL"
            else:
                colspec += " NULL"
        
        if column.table is None:
            raise exc.InvalidRequestError(
                            "mssql requires Table-bound columns " 
                            "in order to generate DDL")
            
        seq_col = column.table._autoincrement_column

        # install a IDENTITY Sequence if we have an implicit IDENTITY column
        if seq_col is column:
            sequence = isinstance(column.default, sa_schema.Sequence) and \
                            column.default
            if sequence:
                start, increment = sequence.start or 1, \
                                    sequence.increment or 1
            else:
                start, increment = 1, 1
            colspec += " IDENTITY(%s,%s)" % (start, increment)
        else:
            default = self.get_column_default_string(column)
            if default is not None:
                colspec += " DEFAULT " + default

        return colspec

    def visit_drop_index(self, drop):
        return "\nDROP INDEX %s.%s" % (
            self.preparer.quote_identifier(drop.element.table.name),
            self.preparer.quote(
                        self._index_identifier(drop.element.name),
                        drop.element.quote)
            )


class MSIdentifierPreparer(compiler.IdentifierPreparer):
    reserved_words = RESERVED_WORDS

    def __init__(self, dialect):
        super(MSIdentifierPreparer, self).__init__(dialect, initial_quote='[', 
                                                   final_quote=']')

    def _escape_identifier(self, value):
        return value

    def quote_schema(self, schema, force=True):
        """Prepare a quoted table and schema name."""
        result = '.'.join([self.quote(x, force) for x in schema.split('.')])
        return result

class MSDialect(default.DefaultDialect):
    name = 'mssql'
    supports_default_values = True
    supports_empty_insert = False
    execution_ctx_cls = MSExecutionContext
    use_scope_identity = True
    max_identifier_length = 128
    schema_name = "dbo"

    colspecs = {
        sqltypes.DateTime : _MSDateTime,
        sqltypes.Date : _MSDate,
        sqltypes.Time : TIME,
    }

    ischema_names = ischema_names
    
    supports_native_boolean = False
    supports_unicode_binds = True
    postfetch_lastrowid = True
    
    server_version_info = ()
    
    statement_compiler = MSSQLCompiler
    ddl_compiler = MSDDLCompiler
    type_compiler = MSTypeCompiler
    preparer = MSIdentifierPreparer

    def __init__(self,
                 query_timeout=None,
                 use_scope_identity=True,
                 max_identifier_length=None,
                 schema_name=u"dbo", **opts):
        self.query_timeout = int(query_timeout or 0)
        self.schema_name = schema_name

        self.use_scope_identity = use_scope_identity
        self.max_identifier_length = int(max_identifier_length or 0) or \
                self.max_identifier_length
        super(MSDialect, self).__init__(**opts)
    
    def do_savepoint(self, connection, name):
        util.warn("Savepoint support in mssql is experimental and "
                  "may lead to data loss.")
        connection.execute("IF @@TRANCOUNT = 0 BEGIN TRANSACTION")
        connection.execute("SAVE TRANSACTION %s" % name)

    def do_release_savepoint(self, connection, name):
        pass
    
    def initialize(self, connection):
        super(MSDialect, self).initialize(connection)
        if self.server_version_info[0] not in range(8, 17):
            # FreeTDS with version 4.2 seems to report here
            # a number like "95.10.255".  Don't know what 
            # that is.  So emit warning.
            util.warn(
                "Unrecognized server version info '%s'.   Version specific "
                "behaviors may not function properly.   If using ODBC "
                "with FreeTDS, ensure server version 7.0 or 8.0, not 4.2, "
                "is configured in the FreeTDS configuration." %
                ".".join(str(x) for x in self.server_version_info) )
        if self.server_version_info >= MS_2005_VERSION and \
                    'implicit_returning' not in self.__dict__:
            self.implicit_returning = True
        
    def _get_default_schema_name(self, connection):
        user_name = connection.scalar("SELECT user_name() as user_name;")
        if user_name is not None:
            # now, get the default schema
            query = sql.text("""
            SELECT default_schema_name FROM
            sys.database_principals
            WHERE name = :name
            AND type = 'S'
            """)
            try:
                default_schema_name = connection.scalar(query, name=user_name)
                if default_schema_name is not None:
                    return unicode(default_schema_name)
            except:
                pass
        return self.schema_name


    def has_table(self, connection, tablename, schema=None):
        current_schema = schema or self.default_schema_name
        columns = ischema.columns
        if current_schema:
            whereclause = sql.and_(columns.c.table_name==tablename,
                                   columns.c.table_schema==current_schema)
        else:
            whereclause = columns.c.table_name==tablename
        s = sql.select([columns], whereclause)
        c = connection.execute(s)
        return c.first() is not None

    @reflection.cache
    def get_schema_names(self, connection, **kw):
        s = sql.select([ischema.schemata.c.schema_name],
            order_by=[ischema.schemata.c.schema_name]
        )
        schema_names = [r[0] for r in connection.execute(s)]
        return schema_names

    @reflection.cache
    def get_table_names(self, connection, schema=None, **kw):
        current_schema = schema or self.default_schema_name
        tables = ischema.tables
        s = sql.select([tables.c.table_name],
            sql.and_(
                tables.c.table_schema == current_schema,
                tables.c.table_type == u'BASE TABLE'
            ),
            order_by=[tables.c.table_name]
        )
        table_names = [r[0] for r in connection.execute(s)]
        return table_names

    @reflection.cache
    def get_view_names(self, connection, schema=None, **kw):
        current_schema = schema or self.default_schema_name
        tables = ischema.tables
        s = sql.select([tables.c.table_name],
            sql.and_(
                tables.c.table_schema == current_schema,
                tables.c.table_type == u'VIEW'
            ),
            order_by=[tables.c.table_name]
        )
        view_names = [r[0] for r in connection.execute(s)]
        return view_names

    # The cursor reports it is closed after executing the sp.
    @reflection.cache
    def get_indexes(self, connection, tablename, schema=None, **kw):
        current_schema = schema or self.default_schema_name
        col_finder = re.compile("(\w+)")
        full_tname = "%s.%s" % (current_schema, tablename)
        indexes = []
        s = sql.text("exec sp_helpindex '%s'" % full_tname)
        rp = connection.execute(s)
        if rp.closed:
            # did not work for this setup.
            return []
        for row in rp:
            if 'primary key' not in row['index_description']:
                indexes.append({
                    'name' : row['index_name'],
                    'column_names' : col_finder.findall(row['index_keys']),
                    'unique': 'unique' in row['index_description']
                })
        return indexes

    @reflection.cache
    def get_view_definition(self, connection, viewname, schema=None, **kw):
        current_schema = schema or self.default_schema_name
        views = ischema.views
        s = sql.select([views.c.view_definition],
            sql.and_(
                views.c.table_schema == current_schema,
                views.c.table_name == viewname
            ),
        )
        rp = connection.execute(s)
        if rp:
            view_def = rp.scalar()
            return view_def

    @reflection.cache
    def get_columns(self, connection, tablename, schema=None, **kw):
        # Get base columns
        current_schema = schema or self.default_schema_name
        columns = ischema.columns
        if current_schema:
            whereclause = sql.and_(columns.c.table_name==tablename,
                                   columns.c.table_schema==current_schema)
        else:
            whereclause = columns.c.table_name==tablename
        s = sql.select([columns], whereclause,
                        order_by=[columns.c.ordinal_position])
        c = connection.execute(s)
        cols = []
        while True:
            row = c.fetchone()
            if row is None:
                break
            (name, type, nullable, charlen, 
                numericprec, numericscale, default, collation) = (
                row[columns.c.column_name],
                row[columns.c.data_type],
                row[columns.c.is_nullable] == 'YES',
                row[columns.c.character_maximum_length],
                row[columns.c.numeric_precision],
                row[columns.c.numeric_scale],
                row[columns.c.column_default],
                row[columns.c.collation_name]
            )
            coltype = self.ischema_names.get(type, None)

            kwargs = {}
            if coltype in (MSString, MSChar, MSNVarchar, MSNChar, MSText, 
                           MSNText, MSBinary, MSVarBinary,
                           sqltypes.LargeBinary):
                kwargs['length'] = charlen
                if collation:
                    kwargs['collation'] = collation
                if coltype == MSText or \
                        (coltype in (MSString, MSNVarchar) and charlen == -1):
                    kwargs.pop('length')

            if coltype is None:
                util.warn(
                    "Did not recognize type '%s' of column '%s'" % 
                    (type, name))
                coltype = sqltypes.NULLTYPE

            if issubclass(coltype, sqltypes.Numeric) and \
                    coltype is not MSReal:
                kwargs['scale'] = numericscale
                kwargs['precision'] = numericprec

            coltype = coltype(**kwargs)
            cdict = {
                'name' : name,
                'type' : coltype,
                'nullable' : nullable,
                'default' : default,
                'autoincrement':False,
            }
            cols.append(cdict)
        # autoincrement and identity
        colmap = {}
        for col in cols:
            colmap[col['name']] = col
        # We also run an sp_columns to check for identity columns:
        cursor = connection.execute("sp_columns @table_name = '%s', "
                                    "@table_owner = '%s'" 
                                    % (tablename, current_schema))
        ic = None
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            (col_name, type_name) = row[3], row[5]
            if type_name.endswith("identity") and col_name in colmap:
                ic = col_name
                colmap[col_name]['autoincrement'] = True
                colmap[col_name]['sequence'] = dict(
                                    name='%s_identity' % col_name)
                break
        cursor.close()

        if ic is not None and self.server_version_info >= MS_2005_VERSION:
            table_fullname = "%s.%s" % (current_schema, tablename)
            cursor = connection.execute(
                "select ident_seed('%s'), ident_incr('%s')" 
                % (table_fullname, table_fullname)
                )

            row = cursor.first()
            if row is not None and row[0] is not None:
                colmap[ic]['sequence'].update({
                    'start' : int(row[0]),
                    'increment' : int(row[1])
                })
        return cols

    @reflection.cache
    def get_primary_keys(self, connection, tablename, schema=None, **kw):
        current_schema = schema or self.default_schema_name
        pkeys = []
        # information_schema.referential_constraints
        RR = ischema.ref_constraints
        # information_schema.table_constraints
        TC = ischema.constraints
        # information_schema.constraint_column_usage: 
        # the constrained column
        C  = ischema.key_constraints.alias('C') 
        # information_schema.constraint_column_usage: 
        # the referenced column                                                
        R  = ischema.key_constraints.alias('R') 

        # Primary key constraints
        s = sql.select([C.c.column_name, TC.c.constraint_type],
            sql.and_(TC.c.constraint_name == C.c.constraint_name,
                     C.c.table_name == tablename,
                     C.c.table_schema == current_schema)
        )
        c = connection.execute(s)
        for row in c:
            if 'PRIMARY' in row[TC.c.constraint_type.name]:
                pkeys.append(row[0])
        return pkeys

    @reflection.cache
    def get_foreign_keys(self, connection, tablename, schema=None, **kw):
        current_schema = schema or self.default_schema_name
        # Add constraints
        #information_schema.referential_constraints
        RR = ischema.ref_constraints
        # information_schema.table_constraints
        TC = ischema.constraints        
        # information_schema.constraint_column_usage: 
        # the constrained column
        C  = ischema.key_constraints.alias('C') 
        # information_schema.constraint_column_usage: 
        # the referenced column
        R  = ischema.key_constraints.alias('R') 

        # Foreign key constraints
        s = sql.select([C.c.column_name,
                        R.c.table_schema, R.c.table_name, R.c.column_name,
                        RR.c.constraint_name, RR.c.match_option,
                        RR.c.update_rule,
                        RR.c.delete_rule],
                       sql.and_(C.c.table_name == tablename,
                                C.c.table_schema == current_schema,
                                C.c.constraint_name == RR.c.constraint_name,
                                R.c.constraint_name ==
                                                RR.c.unique_constraint_name,
                                C.c.ordinal_position == R.c.ordinal_position
                                ),
                       order_by = [
                                    RR.c.constraint_name,
                                    R.c.ordinal_position])
        

        # group rows by constraint ID, to handle multi-column FKs
        fkeys = []
        fknm, scols, rcols = (None, [], [])
        
        def fkey_rec():
            return {
                'name' : None,
                'constrained_columns' : [],
                'referred_schema' : None,
                'referred_table' : None,
                'referred_columns' : []
            }

        fkeys = util.defaultdict(fkey_rec)
        
        for r in connection.execute(s).fetchall():
            scol, rschema, rtbl, rcol, rfknm, fkmatch, fkuprule, fkdelrule = r

            rec = fkeys[rfknm]
            rec['name'] = rfknm
            if not rec['referred_table']:
                rec['referred_table'] = rtbl

                if schema is not None or current_schema != rschema:
                    rec['referred_schema'] = rschema
            
            local_cols, remote_cols = \
                                        rec['constrained_columns'],\
                                        rec['referred_columns']
            
            local_cols.append(scol)
            remote_cols.append(rcol)

        return fkeys.values()

