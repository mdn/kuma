============
Installation
============

This page describes the manual installation procedure. If you can, you
should set up the :doc:`vagrant-managed virtual machine <installation-vagrant>`
instead.

Requirements
============

To run everything and make all the tests pass locally, you'll need the
following things (in addition to Git, of course).

* Python 2.6.

* `setuptools <http://pypi.python.org/pypi/setuptools#downloads>`_
  or `pip <http://pip.openplans.org/>`_.

* MySQL Server and client headers.

* Memcached Server and ``libmemcached``.

* `Sphinx <http://sphinxsearch.com/>`_ 0.9.9, compiled with the
  ``--enable-id64`` flag.

* RabbitMQ.

* ``libxml`` and headers.

* ``libxslt`` and headers.

* ``libjpeg`` and headers.

* ``zlib`` and headers.

* ``libmagic`` and headers.

* ``libtidy`` and headers

* Several Python packages. See `Installing the Packages`_.

Installation for these is very system dependent. Using a package manager, like
yum, aptitude, or brew, is encouraged.


Additional Requirements
-----------------------

If you want to use Apache, instead of the dev server (not strictly required but
it's more like our production environment) you'll also need:

* Apache HTTPD Server.

* ``mod_wsgi``

See the documentation on :doc:`WSGI <wsgi>` for more information and
instructions.


Getting the Source
==================

First, to follow the instructions from `Webdev Bootcamp <http://mozweb.readthedocs.org/en/latest/git.html#working-on-projects>`_,
fork the project into your own account. Then get the source using::

    mkdir mdn # you probably want to do this, since you'll have to create
    cd mdn    # product_details_json/ as a sibling of kuma/ later.
    git clone git@github.com:<your_username>/kuma.git
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

    mkdir ../product_details_json
    ./manage.py syncdb
    ./manage.py migrate

This will generate an empty database, which will get you started!


Initializing Mozilla Product Details
------------------------------------

One of the packages Kuma uses, Django Mozilla Product Details, needs to
fetch JSON files containing historical Firefox version data and write them
within its package directory. To set this up, just run::

    ./manage.py update_product_details

...to do the initial fetch.


Media
-----

If you want to see images and have the pages formatted with CSS you need to
set your ``settings_local.py`` with the following::

    DEBUG = True
    TEMPLATE_DEBUG = DEBUG
    SERVE_MEDIA = True

Setting ``DEBUG = False`` will put the installation in production mode
and ask for minified assets. In that case, you will need to generate
CSS from stylus and compress resource::

    ./scripts/compile_stylesheets
    ./manage.py compress_assets

Configure Persona
-------------------

Add the following to ``settings_local.py`` so that Persona works with the
development instance::

    SITE_URL = 'http://localhost:8000'
    PROTOCOL = 'http://'
    DOMAIN = 'localhost'
    PORT = 8000
    SESSION_COOKIE_SECURE = False # needed if the server is running on http://
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False

The ``SESSION_EXPIRE_AT_BROWSER_CLOSE`` setting is not strictly necessary, but
it's convenient for development.

Secure Cookies
--------------

To prevent error messages like ``Forbidden (CSRF cookie not set.):``, you need to
set your ``settings_local.py`` with the following::

    CSRF_COOKIE_SECURE = False


Testing it Out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``. If everything's working, you should see
the MDN home page!

You might need to first set ``LC_CTYPE`` if you're on Mac OS X until
`bug 754728 <https://bugzilla.mozilla.org/show_bug.cgi?id=754728>`_ is fixed::

    export LC_CTYPE=en_US

What’s next?
============

See :doc:`development <development>` for further instructions.

Some site funcationaly require waffle flags.  Waffle flags include:

-  ``kumaediting``:  Allows creation, editing, and translating of documents
-  ``page_move``:  Allows moving of documents
-  ``revision-dashboard-newusers``:  Allows searching of new users through the revision dashboard
-  ``events_map``:  Allows display of map on the events page
-  ``elasticsearch``:  Enables elastic search for site search
-  ``redesign``:  Enables the latest MDN redesign styles and layouts (run ``./scripts/compile-stylesheets`` to compile stylesheets)

To create or modify waffle flags, visit "/admin/" and click the "Waffle" link.

Last Steps
==========

Setting Up Search
-----------------

See the :doc:`search documentation <sphinx-search>` for steps to get Sphinx
search working.
