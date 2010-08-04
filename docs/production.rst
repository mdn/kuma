================================
Extra Information for Production
================================

There are a few small steps we need to take for production:


Environment
-----------

Requirements
^^^^^^^^^^^^

The full list of requirements is:

* Python 2.6

* `setuptools <http://pypi.python.org/pypi/setuptools#downloads>`_

* `Hunspell <http://hunspell.sourceforge.net/>`_ (Specifically, headers for
  `PyHunspell <http://code.google.com/p/pyhunspell/>`_.)

  * With Hunspell, you will also need dictionaries, either from Hunspell or
    MySpell, to provide spelling suggestions on search queries.

  * Note that Hunspell is required even if no dictionaries are installed.

* MySQL headers (for the Python-MySQL connector).

* `virtualenv <http://pypi.python.org/pypi/virtualenv>`_

* `mod_wsgi <http://code.google.com/p/modwsgi>`_

* Apache HTTPD Server

* RabbitMQ

* libjpeg or a similar library for JPEG support that works with
  `PIL <http://www.pythonware.com/products/pil/>`

* The Python packages in the ``requirements.txt`` file.


Settings
^^^^^^^^

Settings in ``settings.py`` can be overridden in a file named
``settings_local.py`` in the same directory. ``settings_local.py`` should
start with::
  
    from settings import *

and below that line, you can override the defaults.

The following settings may need to be set:

``DEBUG`` and ``TEMPLATE_DEBUG``
  Set both of these to ``False`` for production environments.
``DATABASES``
  Tells Django what databases to talk to. The ``ENGINE`` should probably
  be ``django.db.backends.mysql``. Set the database named ``default`` to
  the master, and you can add additional databases to the ``DATABASES``
  dict to use as slaves. (See ``SLAVE_DATABASES`` below.)
``SLAVE_DATABASES``
  If you've added additional databases to the ``DATABASES`` dict above,
  you should specify which ones are slaves by putting their names in
  the ``SLAVE_DATABASES`` list. (Eg:
  ``SLAVE_DATABASES = ['slave-1', 'slave-2']``)
``CACHE_BACKEND``
  Set to ``caching.backends.memcached://host-1:port;host-2:port``.
``CACHE_PREFIX``
  Something to differentiate from other data on the same memcache instance.
  We recommend ``CACHE_PREFIX = 'sumo:'`` if anything.
``SECRET_KEY``
  Set this to something long, random, and secret.
``DICT_DIR``
  If MySpell dictionaries are not installed in ``/usr/share/myspell/``, you
  can set this to their location. (The directory should include files named
  ``%LOCALE%.dic`` and ``%LOCALE%.aff``
``SPHINX_HOST``
  Point to the Sphinx host.
``SPHINX_PORT``
  Much like ``SPHINX_HOST``.
``SPHINX_INDEXER``, ``SPHINX_SEARCHD``, and ``SPHINX_CONFIG_PATH``
  These only need to be set for running tests. You can ignore them.
``JAVA_BIN``
  If the system java binary is not at ``/usr/bin/java``, you should set
  this. (It's only used for running the ``compress_assets`` command. See
  below.)
``CELERY_ALWAYS_EAGER``
  This should be set to ``False`` to actually use Rabbit/Celery.
``BROKER_*``
  These should be set to allow Kitsune to talk to your RabbitMQ server.


Concat and Minify
-----------------

When running with ``DEBUG=False``, Kitsune will try to use compressed
JavaScript and CSS. To generate the compressed files, just run::
    
    ./manage.py compress_assests

and new files will be created in the /media/ directory.
