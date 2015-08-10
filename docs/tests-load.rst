Load Testing with Locust
========================

We use Locust for load-testing MDN. We write locust test files for different
behavior patterns on MDN, and run the tests to simulate those behaviors
against other environments.

.. note:: **DO NOT RUN LOCUST TESTS AGAINST PRODUCTION**

Running Tests
-------------

.. note:: **DO NOT RUN LOCUST TESTS AGAINST PRODUCTION**

1. Start locust from the development vm::

    vagrant ssh
    make load-smoke-test

2. Go to `http://developer-local.allizom.org:8089/ <http://developer-local.allizom.org:8089/>`_ UI for controlling:

  * number of users to simulate
  * users spawned per second

See `Start locust
<http://docs.locust.io/en/latest/quickstart.html#start-locust>`_ for more.

Adding a Test Suite
-------------------

See `Writing a locustfile
<http://docs.locust.io/en/latest/writing-a-locustfile.html>`_ for more.
