Performance testing
===================

In 2015, as part of a "measure and improve performance" initiative, MDN staff
configured Locust for performance testing of MDN. The locust test files
simulate read traffic to MDN, fetching the top pages in roughly the same ratios
as they were fetched on MDN, and can be run against test environments to
measure changes in code, caching and settings.

These tests are not maintained or run during the current development process.
Some of the common URLs are not included in the sample database.

Running tests
-------------
.. note:: **DO NOT RUN LOCUST TESTS AGAINST PRODUCTION**

#. Create a file ``docker-compose.locust.yml`` in the root folder (same folder
   as ``docker-compose.yml``) with the contents::

    version: "2.1"
    services:
      locust:
        build: ./tests/performance
        depends_on:
          - web
        environment:
          - LOCUST_MODE=standalone
          - TARGET_URL=http://web:8000
        volumes:
          - ./tests/performance/:/tests
        ports:
          - "8089:8089"

#. Edit ``.env`` to update docker-compose::

    COMPOSE_FILE=docker-compose.yml:docker-compose.locust.yml

#. Restart with ``make up``

#. Load the Locust UI at http://localhost:8089, and select:

   * number of users to simulate
   * users spawned per second

See `Start locust
<http://docs.locust.io/en/latest/quickstart.html#start-locust>`_ for more.

Adding a test suite
-------------------

See `Writing a locustfile
<http://docs.locust.io/en/latest/writing-a-locustfile.html>`_ for more.
