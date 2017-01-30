======================
The Kuma test suite
======================

Kuma has a fairly comprehensive Python test suite. Changes should not break
tests. Only change a test if there is a good reason to change the expected
behavior. New code should come with tests.

Commands should be run inside the development environment, after ``make bash``
with Docker, or ``vagrant ssh`` with Vagrant.

Setup
=====

Before you run the tests, you have to build assets::

    make compilejsi18n collectstatic

Running the test suite
======================
If you followed the steps in :doc:`the installation docs <installation>`,
then all you should need to do to run the test suite is::

    make test

The default options for running the test are in ``pytest.ini``. This is a
good set of defaults.

If you ever need to change the defaults, you can do so at the command
line by running what the Make task does behind the scenes::

    py.test kuma

Some helpful command line arguments to py.test (won't work on ``make test``):

``--pdb``:
  Drop into pdb on test failure.

``--create-db``:
  Create a new test database. This is required to apply a new schema or to
  apply migrations to the test database.

``--showlocals``:
  Shows local variables in tracebacks on errors.

``--exitfirst``:
  Exits on the first failure.

See ``py.test --help`` for more arguments.

Running subsets of tests and specific tests
-------------------------------------------
There are a bunch of ways to specify a subset of tests to run:

* only tests marked with the 'spam' marker::

    py.test -m spam

* all the tests but those marked with the 'spam' marker::

    py.test -m "not spam"

* all the tests but the ones in ``kuma/core``::

    py.test --ignore kuma/core

* all the tests that have "foobar" in their names::

    py.test -k foobar

* all the tests that don't have "foobar" in their names::

    py.test -k "not foobar"

* tests in a certain directory::

    py.test kuma/wiki/

* specific test::

    py.test kuma/wiki/tests/test_views.py::RedirectTests::test_redirects_only_internal

See http://pytest.org/latest/usage.html for more examples.

Showing test coverage
---------------------
While running the tests you can record which part of the code base is covered
by test cases. To show the results at the end of the test run use this command::

    make coveragetest

To generate an HTML coverage report, use::

    make coveragetesthtml

The test database
-----------------
The test suite will create a new database named ``test_%s`` where ``%s`` is
whatever value you have for ``settings.DATABASES['default']['NAME']``. Make
sure the user has ``ALL`` on the test database as well.

The first time the test database is created, the migrations are applied. This
includes the migration needed to apply the custom collation to the tag name
index, so the ``py.test`` option ``--no-migrations`` will cause one or more
tag tests to fail. On later runs, the same test database is used without being
recreated from scratch, which speeds up tests considerably.

When the schema and migrations change, the database will need to be recreated.
This command will appear to pause for one or two minutes as it recreates the
test database::

    py.test --create-db kuma/core


Markers
=======
See::

    py.test --markers


for the list of available markers.

To add a marker, add it to the ``pytest.ini`` file.

To use a marker, add a decorator to the class or function. Examples::

    import pytest

    @pytest.mark.spam
    class SpamTests(TestCase):
        ...

    class OtherSpamTests(TestCase):
        @pytest.mark.spam
        def test_something(self):
            ...


Adding tests
============
Code should be written so that it can be tested, and then there should be tests for
it.

When adding code to an app, tests should be added in that app that cover the
new functionality. All apps have a ``tests`` module where tests should go. They
will be discovered automatically by the test runner as long as the look like a
test.

If you're expecting ``reverse`` to return locales in the URL
(``/en-US/docs/Mozilla`` versus ``/docs/Mozilla``), use ``LocalizingClient``
instead of the default client for the ``TestCase`` class.

Changing tests
==============
Unless the current behavior, and thus the test that verifies that behavior is
correct, is demonstrably wrong, don't change tests. Tests may be refactored as
long as it's clear that the result is the same.


Removing tests
==============
On those rare, wonderful occasions when we get to remove code, we should remove
the tests for it, as well.

If we liberate some functionality into a new package, the tests for that
functionality should move to that package, too.
