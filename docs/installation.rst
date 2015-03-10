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

* `Elasticsearch <http://elasticsearch.org/>`_ 0.90.9.

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

Start by creating a file named ``.env`` in the root folder of your kuma Git
clone.

Now you can override a few variables as defined in the ``settings/*`` files.

Database
--------

At a minimum, you will need to define a database connection. The default
database configuration is::

    DATABASE_URL = 'mysql://kuma:kuma@localhost:3306/kuma'

In other words, it uses MySQL default, the username and password of 'kuma'
when trying to access the database 'kuma'. We automatically use MySQL's InnoDB
storage engine if configured.

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

Kuma will automatically run in debug mode, with the ``DEBUG`` setting
turned to ``True``. That will make it serve images and have the pages
formatted with CSS automatically.

Setting ``DEBUG = False`` in your ``.env`` file will put the installation
in production mode and ask for minified assets.

In that case, you will need to generate CSS from stylus and compress resource::

    ./scripts/compile-stylesheets
    ./manage.py compress_assets

Configure Persona
-------------------

Add the following to your ``.env`` file so that Persona works with the
development instance::

    SITE_URL = 'http://localhost:8000'
    PROTOCOL = 'http://'
    DOMAIN = 'localhost'
    # only needed if the server is running on http:// (default)
    SESSION_COOKIE_SECURE = false

Secure Cookies
--------------

To prevent error messages like ``Forbidden (CSRF cookie not set.):``,
you need to set your ``.env`` file with the following::

    CSRF_COOKIE_SECURE = False

Testing it Out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``. If everything's working, you should see
the MDN home page!

You might need to first set ``LC_CTYPE`` in your ``.env`` file if you're on
Mac OS X until `bug 754728 <https://bugzil.la/754728>`_ is fixed::

    LC_CTYPE = en_US

What’s next?
============

See :doc:`development <development>` for further instructions.

Some site funcationaly require waffle flags.  Waffle flags include:

-  ``kumaediting``:  Allows creation, editing, and translating of documents
-  ``page_move``:  Allows moving of documents
-  ``revision-dashboard-newusers``:  Allows searching of new users through the revision dashboard
-  ``events_map``:  Allows display of map on the events page
-  ``elasticsearch``:  Enables elastic search for site search

To create or modify waffle flags, visit "/admin/" and click the "Waffle" link.

Last Steps
==========

Setting Up Search
-----------------

See the :doc:`search documentation <elasticsearch>` for steps to get Elasticsearch
search working.
