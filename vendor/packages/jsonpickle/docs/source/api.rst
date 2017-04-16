.. _jsonpickle-api:

==============
jsonpickle API
==============

.. testsetup:: *

    import jsonpickle
    import jsonpickle.pickler
    import jsonpickle.unpickler
    import jsonpickle.handlers
    import jsonpickle.util

.. contents::

:mod:`jsonpickle` -- High Level API
===================================

.. autofunction:: jsonpickle.encode

.. autofunction:: jsonpickle.decode

Choosing and Loading Backends
-----------------------------

jsonpickle allows the user to specify what JSON backend to use 
when encoding and decoding. By default, jsonpickle will try to use, in
the following order, `simplejson <http://simplejson.googlecode.com/svn/tags/simplejson-2.0.9/docs/index.html>`_, 
:mod:`json`, and `demjson <http://deron.meranda.us/python/demjson/>`_. 
The prefered backend can be set via :func:`jsonpickle.set_preferred_backend`.  
Additional JSON backends can be used via :func:`jsonpickle.load_backend`.

For example, users of `Django <http://www.djangoproject.com/>`_ can use the
version of simplejson that is bundled in Django::

    jsonpickle.load_backend('django.util.simplejson')
    jsonpickle.set_preferred_backend('django.util.simplejson')

.. autofunction:: jsonpickle.set_preferred_backend

.. autofunction:: jsonpickle.load_backend

.. autofunction:: jsonpickle.remove_backend

.. autofunction:: jsonpickle.set_encoder_options

:mod:`jsonpickle.handlers` -- Custom Serialization Handlers
-----------------------------------------------------------

The `jsonpickle.handlers.registry` allows plugging in custom
serialization handlers at run-time.  This is useful when
jsonpickle is unable to serialize objects that are not
under your direct control.

.. automodule:: jsonpickle.handlers
    :members:
    :undoc-members:

Low Level API
=============

Typically this low level functionality is not needed by clients.

:class:`jsonpickle.JSONPluginMgr` -- Management of JSON Backends
----------------------------------------------------------------

.. autoclass:: jsonpickle.JSONPluginMgr
    :members:

:mod:`jsonpickle.pickler` -- Python to JSON
-------------------------------------------

.. automodule:: jsonpickle.pickler
    :members:
    :undoc-members:


:mod:`jsonpickle.unpickler` -- JSON to Python
---------------------------------------------

.. automodule:: jsonpickle.unpickler
    :members:
    :undoc-members:


:mod:`jsonpickle.util` -- Helper functions
------------------------------------------

.. automodule:: jsonpickle.util
    :members:
    :undoc-members:
