Performance Testing with Locust
===============================

In 2015, as part of a "measure and improve performance" initiative, MDN staff
configured Locust for performance testing of MDN. The locust test files
simulate read traffic to MDN, fetching the top pages in roughly the same ratios
as they were fetched on MDN, and can be run against test environments to
measure changes in code, caching and settings.

These tests are not maintained or run during the current development process,
and the instructions have not been updated for the Docker development environment.

Running Tests
-------------
.. note:: **DO NOT RUN LOCUST TESTS AGAINST PRODUCTION**

1. Start locust from the development VM::

    vagrant ssh
    make locust

2. Go to `http://developer-local.allizom.org:8089/ <http://developer-local.allizom.org:8089/>`_ UI for controlling:

* number of users to simulate
* users spawned per second

See `Start locust
<http://docs.locust.io/en/latest/quickstart.html#start-locust>`_ for more.

Adding a Test Suite
-------------------

See `Writing a locustfile
<http://docs.locust.io/en/latest/writing-a-locustfile.html>`_ for more.
