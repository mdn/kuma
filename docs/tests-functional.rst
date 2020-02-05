===================
Client-side testing
===================

Kuma has a suite of functional tests using `pytest`_. All these test suites live
in the /tests/ directory.

The tests directory comprises of:

* ``/headless`` contains tests that don't require a browser
* ``/utils`` contains helper functions.

.. _`pytest`: http://pytest.org/latest/

Setting up test environment
===========================

#. In the terminal go to the directory where you have downloaded kuma.

#. Install the requirements the tests need to run::

   $ poetry install

Running the tests
=================

The minimum amount of information necessary to run the tests against the staging
server is the directory the tests are in. Currently, all of the tests should run
successfully against the staging server.::

   $ poetry run pytest tests

This basic command can be modified to run the tests against a local environment,
or to run tests concurrently.

Only running tests in one file
------------------------------

Add the name of the file to the test location::

   $ poetry run pytest tests/headless/test_cdn.py

Run the tests against a different url
-------------------------------------

By default the tests will run against the staging server. If you'd like to run
the tests against a different URL (e.g., your local environment) pass the
desired URL to the command with ``--base-url``::

   $ poetry run pytest tests --base-url http://mdn.localhost:8000

Run the tests in parallel
-------------------------

By default the tests will run one after the other but you can run several at
the same time by specifying a value for ``-n``::

   $ poetry run pytest tests -n auto

Using Alternate Environments
============================

Run tests on MDN's Continuous Integration (CI) infrastructure
-------------------------------------------------------------

If you have commit rights on the `mdn/kuma GitHub repository`_ you can
run the functional tests using the `MDN CI Infrastructure`_. Just force push
to `mdn/kuma@stage-integration-tests`_ to run the tests
against https://developer.allizom.org.

You can check the status, progress, and logs of the
test runs at `MDN's Jenkins-based multi-branch pipeline`_.

.. _`mdn/kuma GitHub repository`: https://github.com/mdn/kuma
.. _`mdn/kuma@stage-integration-tests`: https://github.com/mdn/kuma/tree/stage-integration-tests
.. _`MDN's Jenkins-based multi-branch pipeline`: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches/

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
for configuring things like the Dockerfile to use to build the container,
and the URL to test against.

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
.. _`Jenkinsfile`: https://github.com/mdn/kuma/blob/master/Jenkinsfile
.. _`Jenkinsfiles directory`: https://github.com/mdn/kuma/tree/master/Jenkinsfiles
.. _`Jenkinsfiles/master.groovy`: https://github.com/mdn/kuma/blob/master/Jenkinsfiles/master.groovy
.. _`Jenkinsfiles/default.groovy`: https://github.com/mdn/kuma/blob/master/Jenkinsfiles/default.groovy
.. _`Jenkinsfiles/integration-tests.groovy`: https://github.com/mdn/kuma/blob/master/Jenkinsfiles/integration-tests.groovy
.. _`Jenkinsfiles/prod-integration-tests.yml` : https://github.com/mdn/kuma/blob/master/Jenkinsfiles/prod-integration-tests.yml
.. _`Jenkinsfiles/stage-integration-tests.yml` : https://github.com/mdn/kuma/blob/master/Jenkinsfiles/stage-integration-tests.yml

Markers
=======

* ``nondestructive``

  Tests are considered destructive unless otherwise indicated. Tests that
  create, modify, or delete data are considered destructive and should not be
  run in production.

* ``smoke``

  These tests should be the critical baseline functional tests.

Guidelines for writing tests
============================

See `Bedrock`_ and the `Web QA Style Guide`_.

.. _`Bedrock`: http://bedrock.readthedocs.io/en/latest/testing.html#guidelines-for-writing-functional-tests
.. _`Web QA Style Guide`: https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide
