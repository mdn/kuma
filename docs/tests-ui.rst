Client-side Testing with Intern
===============================

The client-side testing tool for the MDN front-end is `Intern <https://theintern.github.io/>`_, a Selenium WebDriver API which allows developers to write automated testing via JavaScript. Intern is an open source project created and maintained by `SitePen <http://sitepen.com>`_.

Installing Dependencies
-----------------------

1. Install `JDK <http://www.oracle.com/technetwork/java/javase/downloads/index.html>`_

2. Download the most current release of Selenium `WebDriver <http://selenium-release.storage.googleapis.com/index.html>`_. Download the current standalone version which is a `.jar` file.

3. From the `tests/ui/` directory, use NPM or another package manager to install Intern::

    npm install intern

Do *not* install Intern globally -- path issues may occur.

Firefox appears to work out of the box, but `Chrome <https://code.google.com/p/selenium/wiki/ChromeDriver>`_ and `Safari <https://code.google.com/p/selenium/wiki/SafariDriver>`_ drivers must be downloaded and installed separately.

Running Tests
-------------

1. From the command line, start WebDriver::

    # Substitute your WebDriver version in the `#` chars
    java -jar /path/to/selenium-server-standalone-#.#.#.jar

2. From within the `tests/ui/` directory, run intern on your local intern config file (omitting the `.js`)::

    node_modules/.bin/intern-runner config=intern-local

The above runs the entire suite of tests. Custom functionality has been added to allow for command line arguments to be passed to modify configuration, namely:

* `b` to set which browsers to run in (ex: `b=chrome,firefox`)
* `t` for which test suites to run (ex: `t=wiki,home`)
* `u` to provide a username for Persona
* `p` to provide a password for Persona
* `d` for which domain to run on (ex: `developer.allizom.org`)
* `descructive=true` to signal real docs can be created (do not run this on production)
* `wd` which represents the slug of an existing article to test (ex: `My_Test_Doc`)

An example::

    node_modules/.bin/intern-runner config=intern-local b=firefox,chrome t=auth,homepage d=developer-local.allizom.org u=someone@somewhere.com p=8675309 wd='TestDoc'

The user credentials must be Persona-only (not GMail or Mozilla LDAP lookups).  User credentials are the only required custom command line arguments.

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
