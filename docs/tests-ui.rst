===================
Client-side testing
===================

Kuma has a suite of functional tests using `Selenium`_ and `pytest`_. This allows us
to emulate users interacting with a real browser. All these test suites live in
the /tests/ directory.

The tests directory comprises of:

* ``/functional`` contains pytest tests.
* ``/pages`` contains Python `PyPOM`_ page objects.
* ``/utils`` contains helper functions.
* ``/headless`` contains tests that don't require a browser

.. _`Selenium`: http://docs.seleniumhq.org/
.. _`pytest`: http://pytest.org/latest/
.. _`PyPOM`: https://pypom.readthedocs.io/en/latest/

Setting up test virtual environment
===================================

#. In the terminal go to the directory where you have downloaded kuma.

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
server is the directory the tests are in, which driver to use, and the
subset of tests to run (by specifying a marker or marker expression like
``-m "not login"``, for more information see `Markers`_). Currently, all of the
tests except the tests marked "login" should run successfully against the staging
server.

In the virtual environment run::

   $ pytest -m "not login" tests --driver Chrome --driver-path /path/to/chromedriver

You will be prompted "Do you want the application 'python' to accept incoming
network connections?" The tests seem to run fine no matter how you answer.

This basic command can be modified to use different browsers, to run the tests
against a local environment, or to run tests concurrently.

.. _`pytest-selenium`: http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#specifying-a-browser

Only running tests in one file
------------------------------

Add the name of the file to the test location::

   $ pytest -m "not login" tests/functional/test_search.py --driver Chrome --driver-path /path/to/chromedriver


Run the tests against a different url
-------------------------------------

By default the tests will run against the staging server. If you'd like to run
the tests against a different URL (e.g., your local environment) pass the
desired URL to the command with ``--base-url``::

   $ pytest -m "not login" tests --base-url http://localhost:8000 --driver Chrome --driver-path /path/to/chromedriver

Only running headless tests
---------------------------

Headless tests do not require Selenium or markers::

   $ pytest tests/headless --base-url http://localhost:8000

Run the tests in parallel
-------------------------

By default the tests will run one after the other but you can run several at
the same time by specifying a value for ``-n``::

   $ pytest -m "not login" tests -n auto --driver Chrome --driver-path /path/to/chromedriver

Run the tests against a server configured in maintenance mode
-------------------------------------------------------------

By default the tests will run against a server assumed to be configured
normally. If you'd like to run them against a server configured in
maintenance mode, simply add ``--maintenance-mode`` to the ``pytest`` command
line. For example, if you've configured your local environment to run in
maintenance mode::

   $ pytest --maintenance-mode -m "not search" tests --base-url http://localhost:8000 --driver Chrome --driver-path /path/to/chromedriver

Note that the tests marked "search" were excluded assuming you've loaded the
sample database. If you've loaded a full copy of the production database, you
can drop the ``-m "not search"``.

The ``--maintenance-mode`` command-line switch does two things. It will skip
any tests that don't make sense in maintenance mode (e.g., making sure the
signin link works), and include the tests that only make sense in maintenance
mode (e.g., making sure that endpoints related to editing redirect to the
maintenance-mode page).

Run tests on SauceLabs
----------------------

Running the tests on SauceLabs will allow you to test browsers not on your host
machine.

#. `Signup for an account`_.

#. Log in and obtain your Remote Access Key from user settings.

#. Run a test specifying ``SauceLabs`` as your driver, and pass your credentials
   and the browser to test::

   $ SAUCELABS_USERNAME=thedude SAUCELABS_API_KEY=123456789 pytest -m "not login" tests/functional/ --driver SauceLabs --capability browsername MicrosoftEdge

Alternatively you can save your credentials `in a configuration file`_ so you
don't have to type them each time.

.. _`Signup for an account`: https://saucelabs.com/opensauce/
.. _`in a configuration file`: http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#sauce-labs

Run tests on MDN's Continuous Integration (CI) infrastructure
-------------------------------------------------------------

If you have commit rights on the `mozilla/kuma GitHub repository`_
you can run the UI tests using the `MDN CI Infrastructure`_. Just force push
to `mozilla/kuma@stage-integration-tests`_ to run the tests
against https://developer.allizom.org.

You can check the status, progress, and logs of the
test runs at `MDN's Jenkins-based multi-branch pipeline`_.

.. _`mozilla/kuma GitHub repository`: https://github.com/mozilla/kuma
.. _`mozilla/kuma@stage-integration-tests`: https://github.com/mozilla/kuma/tree/stage-integration-tests
.. _`MDN's Jenkins-based multi-branch pipeline`: https://ci.us-west.moz.works/blue/organizations/jenkins/mdn_multibranch_pipeline/branches/

MDN CI Infrastructure
=====================

The MDN CI infrastructure is a Jenkins-based, multi-branch pipeline. The
pipelines for all branches are defined by the `Jenkinsfile`_ and the files
under the `Jenkinsfiles directory`_. The basic idea is that every branch may
have its own custom pipeline steps and configuration.

Jenkins will auto-discover the steps and configuration by checking within the
`Jenkinsfiles directory`_ for a Groovy (``.groovy``) and/or YAML (``.yml``)
file with the same name as the branch. For example, the
"stage-integration-tests" branch has a
`Jenkinsfiles/stage-integration-tests.yml`_ file which will be
loaded as configuration and used to determine what to do next (load and
run the Groovy script specified by its ``pipeline.script`` setting -
`Jenkinsfiles/integration-tests.groovy`_ - and the script, in turn, will use
the dictionary of values provided by the ``job`` setting defined within the
configuration).

Note that the YAML files for the integration-test branches provide settings
for configuring things like the version of Selenium to use, the number of
Selenium nodes to spin-up, the Dockerfile to use to build the container,
the URL to test against, and which subset of integration tests to run
(via a pytest marker expression, see `Markers`_).

The integration-test Groovy files use a number of global Jenkins functions
that were developed to make the building, running and pushing of
Docker containers seamless (as well as other cool stuff, see
`mozmar/jenkins-pipeline`_). They allow us to better handle situations that
have been painful in the past, like the stopping of background Docker
containers.

The "prod-integration-tests" branch also has its own
`Jenkinsfiles/prod-integration-tests.yml`_ file. It's identical to the YAML
file for the "stage-integration-tests" branch except that it specifies that
the tests should be run against the production server rather than the staging
server (via its ``job.base_url`` setting).

Similarly, the "master" branch has it's own pipeline, but instead of being
configured by a YAML file, the entire pipeline is defined within its
`Jenkinsfiles/master.groovy`_ file.

The pipeline for any other branch which does not provide its own Groovy and/or
YAML file will follow that defined by the `Jenkinsfiles/default.groovy`_ file.

You can check the status, progress, and logs of any pipeline runs via
`MDN's Jenkins-based multi-branch pipeline`_.

.. _`mozmar/jenkins-pipeline`: https://github.com/mozmar/jenkins-pipeline
.. _`Jenkinsfile`: https://github.com/mozilla/kuma/blob/master/Jenkinsfile
.. _`Jenkinsfiles directory`: https://github.com/mozilla/kuma/tree/master/Jenkinsfiles
.. _`Jenkinsfiles/master.groovy`: https://github.com/mozilla/kuma/blob/master/Jenkinsfiles/master.groovy
.. _`Jenkinsfiles/default.groovy`: https://github.com/mozilla/kuma/blob/master/Jenkinsfiles/default.groovy
.. _`Jenkinsfiles/integration-tests.groovy`: https://github.com/mozilla/kuma/blob/master/Jenkinsfiles/integration-tests.groovy
.. _`Jenkinsfiles/prod-integration-tests.yml` : https://github.com/mozilla/kuma/blob/master/Jenkinsfiles/prod-integration-tests.yml
.. _`Jenkinsfiles/stage-integration-tests.yml` : https://github.com/mozilla/kuma/blob/master/Jenkinsfiles/stage-integration-tests.yml

Markers
=======

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
  security reasons these accounts will not be on production. Exclude these tests
  with ``-m "not login"``

Guidelines for writing tests
============================

See `Bedrock`_ and the `Web QA Style Guide`_.

.. _`Bedrock`: http://bedrock.readthedocs.io/en/latest/testing.html#guidelines-for-writing-functional-tests
.. _`Web QA Style Guide`: https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide
