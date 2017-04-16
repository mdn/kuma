========================
jsonpickle Documentation
========================

`jsonpickle <http://jsonpickle.github.com>`_ is a Python library for 
serialization and deserialization of complex Python objects to and from
JSON.  The standard Python libraries for encoding Python into JSON, such as
the stdlib's json, simplejson, and demjson, can only handle Python 
primitives that have a direct JSON equivalent (e.g. dicts, lists, strings, 
ints, etc.).  jsonpickle builds on top of these libraries and allows more
complex data structures to be serialized to JSON. jsonpickle is highly
configurable and extendable--allowing the user to choose the JSON backend
and add additional backends.

.. contents::

jsonpickle Usage
================

.. automodule:: jsonpickle


Download & Install
==================

The easiest way to get jsonpickle is via PyPi_ with easy_install::

    $ easy_install -U jsonpickle

or pip_::
  
    $ pip install -U jsonpickle

You can also download_ or :ref:`checkout <jsonpickle-contrib-checkout>` the
latest code and install from source::

    $ python setup.py install

.. _PyPi: http://pypi.python.org/pypi/jsonpickle
.. _pip: http://pypi.python.org/pypi/pip
.. _download: http://code.google.com/p/jsonpickle/downloads/list


API Reference
=============

.. toctree::
   :maxdepth: 3

   api

Contributing
============

.. _jsonpickle-contrib-checkout:

We welcome contributions from everyone.  Please fork jsonpickle on 
`github <http://github.com/jsonpickle/jsonpickle>`_::

    git clone git://github.com/jsonpickle/jsonpickle.git


Contact
=======

Please join our `mailing list <http://groups.google.com/group/jsonpickle>`_.
You can send email to *jsonpickle@googlegroups.com*.

Check http://github.com/jsonpickle/jsonpickle for project updates.


Authors
=======

 * John Paulett - john -at- paulett.org - http://github.com/johnpaulett
 * David Aguilar - davvid -at- gmail.com - http://github.com/davvid
 * Dan Buch - http://github.com/meatballhat
 * Ian Schenck - http://github.com/ianschenck

Change Log
==========

Version 0.3.1 - December 12, 2009
    * Include tests and docs directories in sdist for distribution packages.

Version 0.3.0 - December 11, 2009
    * Officially migrated to git from subversion. Project home now at 
      `<http://jsonpickle.github.com/>`_. Thanks to Michael Jone's 
      `sphinx-to-github <http://github.com/michaeljones/sphinx-to-github>`_.
    * Fortified jsonpickle against common error conditions.
    * Added support for:

     * List and set subclasses.
     * Objects with module references.
     * Newstyle classes with `__slots__`.
     * Objects implementing `__setstate__()` and `__getstate__()`
       (follows the :mod:`pickle` protocol).

    * Improved support for Zope objects via pre-fetch.
    * Support for user-defined serialization handlers via the
      jsonpickle.handlers registry.
    * Removed cjson support per John Millikin's recommendation.
    * General improvements to style, including :pep:`257` compliance and 
      refactored project layout.
    * Steps towards Python 2.3 and Python 3 support.
    * New contributors Dan Buch and Ian Schenck.
    * Thanks also to Kieran Darcy, Eoghan Murray, and Antonin Hildebrand
      for their assistance!

Version 0.2.0 - January 10, 2009
    * Support for all major Python JSON backends (including json in Python 2.6,
      simplejson, cjson, and demjson)
    * Handle several datetime objects using the repr() of the objects
      (Thanks to Antonin Hildebrand).
    * Sphinx documentation
    * Added support for recursive data structures
    * Unicode dict-keys support
    * Support for Google App Engine and Django
    * Tons of additional testing and bug reports (Antonin Hildebrand, Sorin,
      Roberto Saccon, Faber Fedor,
      `FirePython <http://github.com/darwin/firepython/tree/master>`_, and
      `Joose <http://code.google.com/p/joose-js/>`_)

Version 0.1.0 - August 21, 2008
    * Added long as basic primitive (thanks Adam Fisk)
    * Prefer python-cjson to simplejson, if available
    * Major API change, use python-cjson's decode/encode instead of
      simplejson's load/loads/dump/dumps
    * Added benchmark.py to compare simplejson and python-cjson

Version 0.0.5 - July 21, 2008
    * Changed prefix of special fields to conform with CouchDB
      requirements (Thanks Dean Landolt). Break backwards compatibility.
    * Moved to Google Code subversion
    * Fixed unit test imports

Version 0.0.3
    * Convert back to setup.py from pavement.py (issue found by spidaman)

Version 0.0.2
    * Handle feedparser's FeedParserDict
    * Converted project to Paver
    * Restructured directories
    * Increase test coverage

Version 0.0.1
    Initial release


License
=======

jsonpickle is provided under a
`New BSD license <http://github.com/jsonpickle/jsonpickle/raw/master/COPYING>`_,

Copyright (C) 2008-2009 John Paulett (john -at- paulett.org)
