============
Installation
============

Requirements
============

To run everything and make all the tests pass locally, you'll need the
following things (in addition to Git, of course).

* Python 2.6.

* `setuptools <http://pypi.python.org/pypi/setuptools#downloads>`_
  or `pip <http://pip.openplans.org/>`_.

* MySQL Server and client headers.

* Memcached Server.

* `Sphinx <http://sphinxsearch.com/>`_ 0.9.9, compiled with the
  ``--enable-id64`` flag.

* RabbitMQ.

* ``libxml`` and headers.

* ``libxslt`` and headers.

* ``libjpeg`` and headers.

* ``zlib`` and headers.

* ``libmagic`` and headers.

* Several Python packages. See `Installing the Packages`_.

Installation for these is very system dependent. Using a package manager, like
yum, aptitude, or brew, is encouraged.


Additional Requirements
-----------------------

If you want to use Apache, instead of the dev server (not strictly required but
it's more like our production environment) you'll also need:

* Apache HTTPD Server.

* ``mod_wsgi``

See the documentation on `WSGI <wsgi.rst>`_ for more information and
instructions.


Getting the Source
==================

Grab the source from Github using::

    git clone git://github.com/mozilla/kuma.git
    cd kuma
    git submodule update --init --recursive

Installing the Packages
=======================

Compiled Packages
-----------------

There are a small number of compiled packages, including the MySQL Python
client. You can install these using ``pip`` (if you don't have ``pip``, you
can get it with ``easy_install pip``) or via a package manager.
To use ``pip``, you only need to do this::

    sudo pip install -r requirements/compiled.txt


Python Packages
---------------

All of the pure-Python requirements are available in a git repository, known as
a vendor library. This allows them to be available on the Python path without
needing to be installed in the system, allowing multiple versions for multiple
projects simultaneously.

Configuration
=============

Start by creating a file named ``settings_local.py``, and putting this line in
it::

    from settings import *

Now you can copy and modify any settings from ``settings.py`` into
``settings_local.py`` and the value will override the default.


Database
--------

At a minimum, you will need to define a database connection. An example
configuration is::

    DATABASES = {
        'default': {
            'NAME': 'kuma',
            'ENGINE': 'django.db.backends.mysql',
            'HOST': 'localhost',
            'USER': 'kuma',
            'PASSWORD': '',
            'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_unicode_ci',
        },
    }

Note the two settings ``TEST_CHARSET`` and ``TEST_COLLATION``. Without these,
the test suite will use MySQL's (moronic) defaults when creating the test
database (see below) and lots of tests will fail. Hundreds.

Once you've set up the database, you can generate the schema with Django's
``syncdb`` command::

    ./manage.py syncdb
    ./manage.py migrate

This will generate an empty database, which will get you started!

If you run into a "No such file or directory" error for
../product_details_json just create this folder::

    mkdir ../product_details_json

and run::

    ./manage.py update_product_details

Media
-----

If you want to see images and have the pages formatted with CSS you need to
set your ``settings_local.py`` with the following::

    DEBUG = True
    TEMPLATE_DEBUG = DEBUG
    SERVE_MEDIA = True

Testing it Out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``. If everything's working, you should see
the MDN home page!


Running the Tests
-----------------

A great way to check that everything really is working is to run the test
suite. You'll need to add an extra grant in MySQL for your database user::

    GRANT ALL ON test_NAME.* TO USER@localhost;

Where ``NAME`` and ``USER`` are the same as the values in your database
configuration.

The test suite will create and use this database, to keep any data in your
development database safe from tests.

Running the test suite is easy::

    ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the `test documentation <tests.rst>`_.


Last Steps
==========

Initializing Mozilla Product Details
------------------------------------

One of the packages Kuma uses, Django Mozilla Product Details, needs to
fetch JSON files containing historical Firefox version data and write them
within its package directory. To set this up, just run
``./manage.py update_product_details`` to do the initial fetch.


Setting Up Search
-----------------

See the `search documentation <search.rst>`_ for steps to get Sphinx search
working.
