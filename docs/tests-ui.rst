===================
Client-side Testing
===================

Kuma has a suite of functional tests using `Selenium`_ and `pytest`_. This allows us
to emulate users interacting with a real browser. All these test suites live in
the /tests/ directory.

The tests directory comprises of:

* ``/functional`` contains pytest tests.
* ``/pages`` contains Python pypom page objects.
* ``/utils`` contains helper functions.

.. _`Selenium`: http://docs.seleniumhq.org/
.. _`pytest`: http://pytest.org/latest/

Setting up test virtual environment
===================================

#. In the terminal go to the directory where you have downloaded kuma

#. Create a virtual environment for the tests to run in (the example uses the
   name mdntests)::

   $ virtualenv mdntests

#. Activate the virtual environment::

   $ source mdntests/bin/activate

#. Make sure the version of pip in the virtual environment is high enough to support hashes::

   $ pip install "pip>=8"

#. Install the requirements the tests need to run::

   $ pip install -r requirements/test.txt

You may want to add your virtual environment folder to your local .gitignore
file.

Running the tests
=================

Before running the tests you will need to download the driver for the browser
you want to test in. Drivers are listed and linked to in the `pytest-selenium`_
documentation.

The minimum amount of information necessary to run the tests against the staging
server is the directory the tests are in and which driver to use.

This command will run all the tests in the suite that are marked as
nondestructive.

In the virtual environment run::

   $ py.test tests/functional/ --driver Chrome --driver-path /path/to/chromedriver

You will be prompted "Do you want the application 'python' to accept incoming
network connections?" The tests seem to run fine no matter how you answer.

This basic command can be modified to run subsets of the tests, use different
browsers, run the tests against a local environment, or run tests concurrently.

.. _`pytest-selenium`: http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#specifying-a-browser

Only running tests in one file
------------------------------

Add the name of the file to the test location::

   $ py.test tests/functional/test_search.py --driver Chrome --driver-path /path/to/chromedriver

Only running certain types of tests
-----------------------------------

Specify the desired marker using ``-m``::

   $ py.test tests/functional/ -m smoke --driver Chrome --driver-path /path/to/chromedriver

More information about the marks is below.

Run the tests against a different url
-------------------------------------

By default the tests will run against the staging server.

Pass the desired URL to the command with ``--base-url``::

   $ py.test tests/functional/ --base-url https://developer-local.allizom.org --driver Chrome --driver-path /path/to/chromedriver

Run the tests in parallel
-------------------------

By default the tests will run one after the other but you can run several at
the same time by specifying a value for ``-n``::

   $ py.test tests/functional/ -n auto --driver Chrome --driver-path /path/to/chromedriver

Run tests on SauceLabs
----------------------

Running the tests on SauceLabs will allow you to test browsers not on your host
machine.

#. `Signup for an account`_.

#. Log in and obtain your Remote Access Key from user settings.

#. Run a test specifying ``SauceLabs`` as your driver, and pass your credentials
   and the browser to test::

   $ SAUCELABS_USERNAME=thedude SAUCELABS_API_KEY=123456789 py.test tests/functional/ --driver SauceLabs --capability browsername MicrosoftEdge

Alternatively you can save your credentials `in a configuration file`_ so you
don't have to type them each time.

.. _`Signup for an account`: https://saucelabs.com/opensauce/
.. _`in a configuration file`: http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#sauce-labs

Marks
=====

* ``nondestructive``

  Tests are considered destructive unless otherwise indicated. Tests that
  create, modify, or delete data are considered destructive and should not be
  run in production.

* ``smoke``

  These tests should be the critical baseline functional tests.

* ``nodata``

  New instances of kuma have empty databases so only a subset of tests can be
  run against them. These tests are marked with ``nodata``.

* ``login``

  These tests require the testing accounts to exist on the target site. For
  security reasons these accounts will not be on production.

Guidelines for writing tests
============================

See `Bedrock`_ and the `Web QA Style Guide`_.

.. _`Bedrock`: http://bedrock.readthedocs.io/en/latest/testing.html#guidelines-for-writing-functional-tests
.. _`Web QA Style Guide`: https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide
