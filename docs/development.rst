===========
Development
===========

We only support developing MDN with the :doc:`Vagrant-managed VM <installation>`.

Running Kuma
============

You can start all Kuma servers and services with::

    vagrant ssh
    foreman start

Log in
======

You can log into MDN using Persona or GitHub. For GitHub, you must first enable
:ref:`GitHub Auth` as described in the installation instructions.

Set up permissions
==================

Some features are only available to privileged users. To manage permissions
use the Auth -> Users section of the Django admin interface.

Compiling Stylus Files
======================

If you're updating the Stylus CSS files, you'll need to compile them before
you can see your updates within the browser. To compile stylus files,
run the following from the command line::

    ./scripts/compile-stylesheets

The relevant CSS files will be generated and placed within the `media/css`
directory. You can add a ``-w`` flag to that call to compile stylesheets
upon save.

Hacking on bleeding edge features
=================================
To hack on the features not yet ready for production you have to enable them first.

Enable Kumascript
-----------------

Kuma uses a separate nodejs-based service to process templates in wiki pages. Its
use is disabled by default, to enable: open the django admin interface and in the
Constance section change the value of ``KUMASCRIPT_TIMEOUT`` parameter to a positive
value (such as ``2.0`` seconds).

Migrations
==========

Basically all apps are migrated using Django's migration system.

See the Django documentation for the
`migration workflow <https://docs.djangoproject.com/en/1.8/topics/migrations/#workflow>`_.

How to run the migrations
-------------------------

Run the migrations via the Django management command::

    python manage.py migrate

Running the Tests
=================

A great way to check that everything really is working is to run the test
suite.

Django tests
------------

Running the test suite is easy::

    ./manage.py test

Note that this will try (and fail) to run tests that depend on apps disabled
via ``INSTALLED_APPS``. You should run a subset of tests::

    ./manage.py test kuma

For more information, see the :doc:`test documentation <tests>`.

Kumascript tests
----------------

If you're changing Kumascript, be sure to run its tests too.
See https://github.com/mozilla/kumascript

Coding Conventions
==================

Tests
-----

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the ``TestCase``
  class.
