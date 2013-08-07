============
Development
============

After you have completed the :doc:`manual installation steps <installation>`
or set up the :doc:`Vagrant-managed VM <installation-vagrant>`), and are able
to run Kuma using ``./manage.py runserver``, you can start contributing.

Running Kuma
============

In addition to running the django app using ``./manage.py runserver``, you can run
the kumascript service to enable wiki templates processing::

    node kumascript/run.js

...and :doc:`celery <celery>` to enable background task processing (such as sending
the e-mail notifications).
Note that, before running the kumascript, you need to install the node.js ``fibers`` module
by running ``npm install fibers``.

Log in
------

You can log into the wiki using Persona or via the django admin interface.
If you use the admin interface, you can log in as the user you created during installation
or on the vagrant VM use login ``admin`` with password ``admin``.

Set up permissions
------------------

Some features are only available to privileged users. To manage permissions use the
Auth -> Users section of the django admin interface.

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

When using the vagrant VM you must `run the tests from the root folder`_, not from
``/vagrant``::

    (cd / && /vagrant/manage.py test ...)

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
