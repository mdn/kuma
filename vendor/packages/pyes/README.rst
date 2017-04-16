=============================
 pyes - Python ElasticSearch
=============================

:Web: http://pypi.python.org/pypi/pyes/
:Download: http://pypi.python.org/pypi/pyes/
:Source: http://github.com/aparo/pyes/
:Keywords: search, elastisearch, distribute search

--

pyes is a connector to use elasticsearch from python.

This version requires elasticsearch 0.15 or above.

Features
========

- Thrift/HTTP protocols
- Bulk insert/delete
- Index management
- Every search query types
- Facet Support
- Geolocalization support
- Highlighting
- River support

Connecting
==========

These function are taken from pycassa.

Import the module:

    >>> import pyes

pyes is able to use standard http or thrift protocol. If your port starts with "92" http protocol is used, otherwise thrift.


For a single connection (which is _not_ thread-safe), pass a list of servers.

For thrift:

    >>> conn = pyes.ES() # Defaults to connecting to the server at '127.0.0.1:9500'
    >>> conn = pyes.ES(['127.0.0.1:9500'])

For http:

    >>> conn = pyes.ES(['127.0.0.1:9200'])

Connections are robust to server failures. Upon a disconnection, it will attempt to connect to each server in the list in turn. If no server is available, it will raise a NoServerAvailable exception.

Timeouts are also supported and should be used in production to prevent a thread from freezing while waiting for the server to return.

    >>> conn = pyes.ES(timeout=3.5) # 3.5 second timeout
    (Make some pyes calls and the connection to the server suddenly becomes unresponsive.)

    Traceback (most recent call last):
    ...
    pyes.connection.NoServerAvailable

Note that this only handles socket timeouts. 


Usage
=====

Creating a connection:

    >>> from pyes import *
    >>> conn = ES('127.0.0.1:9500')

Deleting an index:

    >>> try:
    >>>     conn.delete_index("test-index")
    >>> except:
    >>>     pass

(an exception is fored if the index is not present)

Create an index:

    >>> conn.create_index("test-index")

Creating a mapping:

    >>> mapping = { u'parsedtext': {'boost': 1.0,
    >>>                  'index': 'analyzed',
    >>>                  'store': 'yes',
    >>>                  'type': u'string',
    >>>                  "term_vector" : "with_positions_offsets"},
    >>>          u'name': {'boost': 1.0,
    >>>                     'index': 'analyzed',
    >>>                     'store': 'yes',
    >>>                     'type': u'string',
    >>>                     "term_vector" : "with_positions_offsets"},
    >>>          u'title': {'boost': 1.0,
    >>>                     'index': 'analyzed',
    >>>                     'store': 'yes',
    >>>                     'type': u'string',
    >>>                     "term_vector" : "with_positions_offsets"},
    >>>          u'pos': {'store': 'yes',
    >>>                     'type': u'integer'},
    >>>          u'uuid': {'boost': 1.0,
    >>>                    'index': 'not_analyzed',
    >>>                    'store': 'yes',
    >>>                    'type': u'string'}}
    >>> conn.put_mapping("test-type", {'properties':mapping}, ["test-index"])

Index some documents:

    >>> conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "uuid":"11111", "position":1}, "test-index", "test-type", 1)
    >>> conn.index({"name":"Bill Baloney", "parsedtext":"Joe Testere nice guy", "uuid":"22222", "position":2}, "test-index", "test-type", 2)

Refresh an index:

    >>> conn.refresh(["test-index"])

Execute a query

    >>> q = TermQuery("name", "joe")
    >>> result = self.conn.search(query = q)

For more examples looks at the tests.


Changelog
=========

Note for next release - the order of geolocation parameters expected by
elasticsearch changed between ES 0.14.4 and ES 0.15, from [lat, lon] to [lon,
lat].  Clients will need to update accordingly, or use an object with named
parameters.

v. 0.16.0:

           Updated documentation.

           Added TextQuery and some clean up of code.

           Added percolator (matterkkila).

           Added date_histogram facet (zebuline).

           Added script fields to Search object, also add "fields" to TermFacet  (aguereca).

           Added analyze_wildcard param to StringQuery (available for ES 0.16.0) (zebuline).

           Add ScriptFields object used as parameter script_fields of Search object (aguereca).

           Add IdsQuery, IdsFilter and deleteByQuery (aguereca).

           Bulk delete (acdha).

v. 0.15.0:
	
           Only require simplejson for python < 2.6 (matterkkila)

           Added basic version support to ES.index and Search (merrellb)

           Added scan method to ES.  This is only supported on ES Master (pre 0.16) (merrellb)

           Added GeoPointField to mapping types (merrellb)

           Disable thrift in setup.py. 

           Added missing _routing property in ObjectField 

           Added ExistsFilter 

           Improved HasChildren 

           Add min_similarity and prefix_length to flt. 

           Added _scope to HasChildQuery. (andreiz)

           Added parent/child document in test indexing. Added _scope to HasChildFilter. 

           Added MissingFilter as a subclass of TermFilter 

           Fixed error in checking TermsQuery (merrellb)

           If an analyzer is set on a field, the returned mapping will have an analyzer 

           Add a specific error subtype for mapper parsing exceptions (rboulton)

           Add support for Float numeric field mappings (rboulton)

           ES.get() now accepts "fields" as well as other keyword arguments (eg "routing") (rboulton)

           Allow dump_curl to be passed a filehandle (or still a filename), don't for filenames to be in /tmp, and add a basic test of it. 

           Add alias handling (rboulton)

           Add ElasticSearchIllegalArgumentException - used for example when writing to an alias which refers to more than one index. (rboulton)

           Handle errors produced by deleting a missing document, and add a test for it. (rboulton)

           Split Query object into a Search object, for the search specific parts, and a Query base class.  Allow ES.search() to take a query or a search object.  Make some of the methods of Query base classes chainable, where that is an obviously reasonable thing to do. (rboulton)

v. 0.14.0: Added delete of mapping type.

           Embedded urllib3 to be buildout safe and for users sake.

           Some code cleanup.

           Added reindex by query (usable only with my elasticsearch git branch).

           Added contrib with mailman indexing.

           Autodetect if django is available and added related functions.

           Code cleanup and PEP8.

           Reactivated the morelikethis query.

           Fixed river support plus unittest. (Tavis Aitken)

           Added autorefresh to sync search and write.

           Added QueryFilter.

           Forced name attribute in multifield declaration.

           Added is_empty to ConstantScoreQuery and fixed some bad behaviour.

           Added CustomScoreQuery.

           Added parent/children indexing.

           Added dump commands in a script file "curl" way.

           Added a lot of fix from Richard Boulton.

v. 0.13.1: Added jython support (HTTP only for now).

v. 0.13.0: API Changes: errors -> exceptions.
           
           Splitting of query/filters.
           
           Added open/close of index.

           Added the number of retries if server is down.

           Refactory Range query. (Andrei)

           Improved HTTP connection timeout/retries. (Sandymahalo)

           Cleanup some imports. (Sandymahalo)

v. 0.12.1: Added collecting server info.

           Version 0.12 or above requirement.

           Fixed attachment plugin. 

           Updated bulk insert to use new api. 

           Added facet support (except geotypes).

           Added river support. 

           Cleanup some method.

           Added default_indexes variable.

           Added datetime deserialization.

           Improved performance and memory usage in bulk insert replacing list with StringIO.

           Initial propagation of elasticsearch exception to python.

v. 0.12.0: added http transport, added autodetect of transport, updated thrift interface. 

v. 0.10.3: added bulk insert, explain and facet. 

v. 0.10.2: added new geo query type. 

v. 0.10.1: added new connection pool system based on pycassa one.

v. 0.10.0: initial working version.


TODO
----

- more docs
- more tests
- cleanup
- add coverage
- add jython native client protocol

License
=======

This software is licensed under the ``New BSD License``. See the ``LICENSE``
file in the top distribution directory for the full license text.

.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround
