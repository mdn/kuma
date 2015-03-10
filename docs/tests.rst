======================
The Kuma Test Suite
======================

Kuma has a fairly comprehensive Python test suite. Changes should not break
tests--only change a test if there is a good reason to change the expected
behavior--and new code should come with tests.


Running the Test Suite
======================

If you followed the steps in :doc:`the installation docs <installation>`,
then all you should need to do to run the test suite is::

    ./manage.py test

However, that doesn't provide the most sensible defaults. Here is a good
command to alias to something short::

    ./manage.py test -s --noinput --logging-clear-handlers

The ``-s`` flag is important if you want to be able to drop into PDB from
within tests.

Some tests will fail.  See `Running a Subset`_ below for running the subset
that is expected to pass.

Some other helpful flags are:

``-x``:
  Fast fail. Exit immediately on failure. No need to run the whole test suite
  if you already know something is broken.
``--pdb``:
  Drop into PDB on an uncaught exception. (These show up as ``E`` or errors in
  the test results, not ``F`` or failures.)
``--pdb-fail``:
  Drop into PDB on a test failure. This usually drops you right at the
  assertion.


Running a Subset
----------------

You can run part of the test suite by specifying the apps you want to run,
like::

    ./manage.py test kuma

You can also exclude tests that match a regular expression with ``-e``::

    ./manage.py test -e "search"

To run the subset of tests that should pass::

    ./manage.py test kuma

See the output of ``./manage.py test --help`` for more arguments.


The Test Database
-----------------

The test suite will create a new database named ``test_%s`` where ``%s`` is
whatever value you have for ``settings.DATABASES['default']['NAME']``. Make
sure the user has ``ALL`` on the test database as well.

Adding Tests
============

Code should be written so it can be tested, and then there should be tests for
it.

When adding code to an app, tests should be added in that app that cover the
new functionality. All apps have a ``tests`` module where tests should go. They
will be discovered automatically by the test runner as long as the look like a
test.


Changing Tests
==============

Unless the current behavior, and thus the test that verifies that behavior is
correct, is demonstrably wrong, don't change tests. Tests may be refactored as
long as its clear that the result is the same.


Removing Tests
==============

On those rare, wonderful occasions when we get to remove code, we should remove
the tests for it, as well.

If we liberate some functionality into a new package, the tests for that
functionality should move to that package, too.
