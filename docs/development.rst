===========
Development
===========

We strongly suggest using a :doc:`Vagrant-managed VM <installation-vagrant>` if you can.
Or, you can use the :doc:`manual installation steps <installation>`.

Running Kuma in Vagrant VM
==========================

If you are using a :doc:`Vagrant-managed VM <installation-vagrant>`, you can start all
Kuma servers and services with::

    vagrant ssh
    foreman start

Running Kuma manually
=====================

If you are using :doc:`manual installation <installation>`, you can run the django server with::

    ./manage.py runserver

and the kumascript service with::

    node kumascript/run.js

Note: Before running kumascript, you need to install the node.js ``fibers`` module
by running ``npm install fibers``.


Log in
======

You can log into the wiki using Persona or via the django admin interface.
If you use the admin interface, you can log in as the user you created during installation
or on the vagrant VM use login ``admin`` with password ``admin``.

Set up permissions
==================

Some features are only available to privileged users. To manage permissions use the
Auth -> Users section of the django admin interface.

Compiling Stylus Files
======================

If you're updating the Stylus CSS files, you'll need to compile them before you can see your updates within the browser.  To compile stylus files, run the following from the command line::

	./scripts/compile-stylesheets

The relevant CSS files will be generated and placed within the `media/redesign/css` directory. You can add a ``-w`` flag to that call to compile stylesheets upon save.

Hacking on bleeding edge features
=================================
To hack on the features not yet ready for production you have to enable them first.

Enable Kumascript
-----------------

Kuma uses a separate nodejs-based service to process templates in wiki pages. Its
use is disabled by default, to enable: open the django admin interface and in the
Constance section change the value of ``KUMASCRIPT_TIMEOUT`` parameter to a positive
value (such as ``2.0`` seconds).

Running the Tests
=================

A great way to check that everything really is working is to run the test
suite.

Django tests
------------
If you're not using the vagrant VM, you'll need to add an extra grant in MySQL for
your database user::

    GRANT ALL ON test_NAME.* TO USER@localhost;

Where ``NAME`` and ``USER`` are the same as the values in your database
configuration.

The test suite will create and use this database, to keep any data in your
development database safe from tests.

Running the test suite is easy::

    ./manage.py test -s --noinput --logging-clear-handlers

Note that this will try (and fail) to run tests that depend on apps disabled
via ``INSTALLED_APPS``. You should run a subset of tests specified in
`scripts/build.sh <../scripts/build.sh>`_, at the bottom of the script.

For more information, see the :doc:`test documentation <tests>`.

.. _run the tests from the root folder: https://bugzilla.mozilla.org/show_bug.cgi?id=756536#c2

Kumascript tests
----------------

If you're changing Kumascript, be sure to run its tests too.
See https://github.com/mozilla/kumascript

Coding Conventions
==================

Tests
-----

* Avoid naming test files ``test_utils.py``, since we use a library with the
  same name. Use ``test__utils.py`` instead.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the ``TestCase``
  class.
