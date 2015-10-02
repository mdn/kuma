Client-side Testing with Intern
===============================

We use `Intern <https://theintern.github.io/>`_ for client-side testing. It uses Selenium WebDriver API which lets us write automated testing via JavaScript. Intern is an open source project created and maintained by `SitePen <http://sitepen.com>`_.

Installing Dependencies
-----------------------

1. Go to the ``tests/ui/`` directory::

    cd tests/ui

2. Use ``npm`` to install Intern::

    npm install intern@^3.0

.. warning:: Do *not* install Intern globally -- path issues may occur.

Running Tests
-------------

On your machine
~~~~~~~~~~~~~~~

1. Install `JDK <http://www.oracle.com/technetwork/java/javase/downloads/index.html>`_

2. Download the most current `release of Selenium <http://selenium-release.storage.googleapis.com/index.html>`_ standalone server. (It's the ``.jar`` file.)

.. note:: Firefox should work out of the box. You need to install `Chrome <https://sites.google.com/a/chromium.org/chromedriver/>`_ and `Safari <https://code.google.com/p/selenium/wiki/SafariDriver>`_ drivers yourself.

3. From the command line, start WebDriver::

    # Substitute your WebDriver version in the `#` chars
    java -jar /path/to/selenium-server-standalone-#.#.#.jar

4. Go to the ``tests/ui/`` directory::

    cd tests/ui

5. Run intern with the ``intern-local`` config file (omit the ``.js``)::

    ./node_modules/.bin/intern-runner config=intern-local b=firefox

The above tries to run the entire suite of tests. You can change the behavior with `command line arguments`_. E.g., ::

    node_modules/.bin/intern-runner config=intern-local b=firefox,chrome t=auth,homepage d=developer-local.allizom.org u=someone@somewhere.com p=8675309 wd='Web' destructive=true

The user credentials must be Persona-only (not GMail or Mozilla LDAP lookups).  User credentials are the only required custom command line arguments.

Safari requires some special configuration to ensure tests run correctly:

1.  Open your Safari browser's preferences dialog and disable the popup blocker

2.  You must download and manually install the `Safari Selenium Extension <https://github.com/SeleniumHQ/selenium/blob/master/javascript/safari-driver/prebuilt/SafariDriver.safariextz>`_.  Once downloaded, drag the extension into the Safari extensions list within the Preferences dialog.

On a Cloud Provider
~~~~~~~~~~~~~~~~~~~

We have tested running the Intern test suite with BrowserStack and SauceLabs.
We have better luck with BrowserStack, and it's the provider MDN staff devs
use.

1. Sign up for either `BrowserStack <http://www.browserstack.com/>`_ or `SauceLabs <https://saucelabs.com/>`_.

2. Go to the ``tests/ui/`` directory::

    cd tests/ui

3. Set the `appropriate environment variables
   <https://theintern.github.io/intern/#hosted-selenium>`_ with your provider credentials.
   E.g., ::

    export BROWSERSTACK_USERNAME='fakeuser'
    export BROWSERSTACK_ACCESS_KEY='fakeaccesskey'

3. Run intern with the appropriate config file (omitting the ``.js``). E.g., ::

    ./node_modules/.bin/intern-runner config=intern-browserstack

.. _command line arguments:

Command-Line Arguments
~~~~~~~~~~~~~~~~~~~~~~

* ``b`` - browsers to run (e.g., ``b=chrome,firefox``)
* ``t`` - test suites to run (e.g., ``t=wiki,homepage``)
* ``d`` - domain to run against (e.g., ``d=developer.allizom.org``)
* ``u`` - username for Persona (e.g., ``u=testuser@example.com``)
* ``p`` - password for Persona (e.g., ``p=testpass``)
* ``wd`` - slug of existing article to test (e.g., ``wd=My_Test_Doc``)
* ``destructive=true`` - create real docs (do not run this on production)

Adding a Test Suite
-------------------

To add a test suite, place your JavaScript file within the `tests/ui/tests` directory. Use the following as a template for your test suite code::

    define([
        'intern!object',
        'intern/chai!assert',
        'base/_config'
    ], function(registerSuite, assert, config) {

        registerSuite({

            // Unique, short name for test suite
            name: '',

            // Anything to run before each test (setup)
            before: function() {

            },

            // Text decribing what the test is testing
            '': function() {

            }
        });

    });


To run your new tests with, add the new suite path to the `tests/ui/_tests.js` file.

Identifying Test Failures
-------------------------

Tests are run for each browser cited in the config's `environments` setting. A sample output with error may look like::

    $ ./node_modules/.bin/intern-runner config=intern-local

    Listening on 0.0.0.0:9000
    Starting tunnel...
    Initialised firefox 31.0 on MAC
    Test main - home - Ensure homepage is displaying search form and accepts text FAILED on firefox 31.0 on MAC:
    AssertionError: fake test failure: expected false to be truthy
      at new CompatCommand  <node_modules/intern/runner.js:208:14>
      at CompatCommand.Command.then  <node_modules/intern/node_modules/leadfoot/Command.js:525:10>
      at Test.registerSuite.Ensure homepage is displaying search form and accepts text [as test]  <tests/homepage.js:18:26>
      at Test.run  <node_modules/intern/lib/Test.js:169:19>
      at <node_modules/intern/lib/Suite.js:237:13>
      at signalListener  <node_modules/intern/node_modules/dojo/Deferred.js:37:21>
      at Promise.then.promise.then  <node_modules/intern/node_modules/dojo/Deferred.js:258:5>
      at runTest  <node_modules/intern/lib/Suite.js:236:46>
      at <node_modules/intern/lib/Suite.js:249:7>
      at process._tickCallback  <node.js:419:13>

    =============================== Coverage summary ===============================
    Statements   : 100% ( 1/1 )
    Branches     : 100% ( 0/0 )
    Functions    : 100% ( 0/0 )
    Lines        : 100% ( 1/1 )
    ================================================================================
    firefox 31.0 on MAC: 1/5 tests failed

    ----------------------|-----------|-----------|-----------|-----------|
    File                  |   % Stmts |% Branches |   % Funcs |   % Lines |
    ----------------------|-----------|-----------|-----------|-----------|
       ui/                |       100 |       100 |       100 |       100 |
          intern-local.js |       100 |       100 |       100 |       100 |
    ----------------------|-----------|-----------|-----------|-----------|
    All files             |       100 |       100 |       100 |       100 |
    ----------------------|-----------|-----------|-----------|-----------|

    TOTAL: tested 1 platforms, 1/5 tests failed

At present time, `SitePen is looking to pretty up the console output <https://github.com/theintern/intern/issues/258>`_.
