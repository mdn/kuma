===========
Development
===========

Basic Docker usage
==================
Edit files as usual on your host machine; the current directory is mounted
via Docker host mounting at ``/app`` within various
Kuma containers. Useful docker sub-commands::

    docker-compose exec web bash     # Start an interactive shell
    docker-compose logs web          # View logs from the web container
    docker-compose logs -f           # Continuously view logs from all containers
    docker-compose restart web       # Force a container to reload
    docker-compose stop              # Shutdown the containers
    docker-compose up -d             # Start the containers
    docker-compose rm                # Destroy the containers

There are ``make`` shortcuts on the host for frequent commands, such as::

    make up         # docker-compose up -d
    make bash       # docker-compose exec web bash
    make shell_plus # docker-compose exec web ./manage.py shell_plus

Run all commands in this doc in the ``web`` service container after ``make bash``.

Running Kuma
============
When the Docker container environment is started (``make up`` or similar), all
of the services are also started. The development instance is available at
http://localhost:8000.

Running the tests
=================
One way to confirm that everything is working, or to pinpoint what is broken,
is to run the test suite.

Django tests
------------
Run the Django test suite::

    make test

For more information, see the :doc:`test documentation <tests>`.

Functional tests
----------------
To run the functional tests, see
:doc:`Client-side Testing <tests-functional>`.


Database migrations
===================
Apps are migrated using Django's migration system. To run the migrations::

    ./manage.py migrate



Coding conventions
==================
See CONTRIBUTING.md_ for details of the coding style on Kuma.

New code is expected to have test coverage.  See the
:doc:`Test Suite docs <tests>` for tips on writing tests.

.. _CONTRIBUTING.md: https://github.com/mdn/kuma/blob/master/CONTRIBUTING.md

Managing dependencies
=====================

Python dependencies
-------------------

Kuma uses `Poetry`_ for dependency management. Poetry is configured in the
``pyproject.toml`` file at the root of the repository, and exact versions of
dependencies (along with hashes) are stored in the ``poetry.lock`` file.

Please refer to the Poetry docs on `adding`_ and `updating`_ dependencies.

A few examples:

* Use ``poetry update`` to update and re-lock all dependencies to their latest
  compatible versions, according to constraints in ``pyproject.toml``.

* Use ``poetry update <name>`` to update only a single dependency to its latest
  compatible version, according to constraints in ``pyproject.toml``. For
  example ``poetry update pytz``.

* To update a package to the very latest and not just what matches what's
  currently in ``pyproject.toml``, add ``@latest``. For example
  ``poetry update pytz@latest``.

* Use ``poetry add <name>`` to modify or add new entries inside of
  ``pyproject.toml``, for example, ``poetry add django~2.2`` or ``poetry add
  flake8@latest``.

* Use ``poetry lock`` to regenerate the ``poetry.lock``, for example, after
  manually editing ``pyproject.toml``.

* Use ``poetry show`` to report on the project's dependencies.

In brief, ``update`` alters the lockfile, but does not modify entries within
``pyproject.toml``. The ``add`` command changes both.

You may wish to run these commands inside of Docker::

    docker-compose exec web poetry update --dry-run

Using Poetry directly on your host computer is also fine; the resulting
``pyproject.toml`` and ``poetry.lock`` files should be the same either way.

.. _Poetry: https://python-poetry.org/
.. _adding: https://python-poetry.org/docs/cli/#add
.. _updating: https://python-poetry.org/docs/cli/#update

.. _front-end-asset-dependencies:




Customizing with environment variables
======================================
`Environment variables`_ are used to change the way different components work.
There are a few ways to change an environment variables:

* Exporting in the shell, such as::

    export DEBUG=True;
    ./manage.py runserver

* A one-time override, such as::

    DEBUG=True ./manage.py runserver

* Changing the ``environment`` list in ``docker-compose.yml``.
* Creating a ``.env`` file in the repository root directory.

One variable you may wish to alter for local development is ``DEBUG_TOOLBAR``,
which, when set to ``True``, will enable the Django Debug Toolbar::

    DEBUG_TOOLBAR=True

Note that enabling the Debug Toolbar can severely impact response time, adding
around 4 seconds to page load time.

.. _Environment variables: http://12factor.net/config

Customizing number of workers
=============================

The ``docker-compose.yml`` in git comes with a default setting of
4 ``celery`` workers and 4 ``gunicorn`` workers. That's pretty resource
intensive since they prefork. To change the number of ``gunicorn``
and ``celery`` workers, consider setting this in your ``.env`` file::

    CELERY_WORKERS=2
    GUNICORN_WORKERS=3

In that example, it will only start 2 ``celery`` workers and 3 ``gunicorn``
workers just for your environment.

.. _advanced_config_docker:

Customizing the Docker environment
==================================
Running docker-compose_ will create and run several containers, and each
container's environment and settings are configured in ``docker-compose.yml``.
The settings are "baked" into the containers created by ``docker-compose up``.

To override a container's settings for development, use a local override file.
For example, the ``web`` service runs in a container with the
default command
"``gunicorn -w 4 --bind 0.0.0.0:8000 --timeout=120 kuma.wsgi:application``".
(The container has a name that begins with ``kuma_web_1_`` and
ends with a string of random hex digits. You can look up the name of
your particular container with ``docker ps | grep kuma_web``. You'll
need this container name for some of the commands described below.)
A useful alternative for debugging is to run a single-threaded process that
loads the Werkzeug debugger on exceptions (see docs for runserver_plus_), and
that allows for stepping through the code with a debugger.
To use this alternative, create an override file ``docker-compose.override.yml``::

    version: "2.1"
    services:
      web:
        command: ./manage.py runserver_plus 0.0.0.0:8000
        stdin_open: true
        tty: true


This is similar to "``docker run -it <container> ./manage.py runserver_plus``",
using all the other configuration items in ``docker-compose.yml``.
Apply the custom setting with::

    docker-compose up -d

You can then add ``pdb`` breakpoints to the code
(``import pdb; pdb.set_trace``) and connect to the debugger with::

    docker attach <container>

A similar method can be used to override environment variables in containers,
run additional services, or make other changes.  See the docker-compose_
documentation for more ideas on customizing the Docker environment.

.. _docker-compose: https://docs.docker.com/compose/overview/
.. _pdb: https://docs.python.org/2/library/pdb.html
.. _runserver_plus: http://django-extensions.readthedocs.io/en/latest/runserver_plus.html

Customizing the database
========================
The database connection is defined by the environment variable
``DATABASE_URL``, with this default::

    DATABASE_URL=postgresql://kuma:kuma@postgres:5432/developer_mozilla_org

The format is defined by the dj-database-url_ project::

    DATABASE_URL=mysql://user:password@host:port/database

If you configure a new database, override ``DATABASE_URL`` to connect to it. To
add an empty schema to a freshly created database::

    ./manage.py migrate

To connect to the database specified in ``DATABASE_URL``, use::

    ./manage.py dbshell

.. _dj-database-url: https://github.com/kennethreitz/dj-database-url

.. _generating-production-assets:

Using secure cookies
====================
To prevent error messages like "``Forbidden (CSRF cookie not set.):``", set the
environment variable::

    CSRF_COOKIE_SECURE = false

This is the default in Docker, which does not support local development with
HTTPS.

.. _maintenance-mode:

Maintenance mode
================
Maintenance mode is a special configuration for running Kuma in read-only mode,
where all operations that would write to the database are blocked. As the name
suggests, it's intended for those times when we'd like to continue to serve
documents from a read-only copy of the database, while performing maintenance
on the master database.

For local Docker-based development in maintenance mode:

#. If you haven't already, create a read-only user for your local MySQL
   database::

    docker-compose up -d
    docker-compose exec web mysql -h mysql -u root -p
    (when prompted for the password, enter "kuma")
    mysql> source ./scripts/create_read_only_user.sql
    mysql> quit

#. Create a ``.env`` file in the repository root directory, and add these
   settings::

    MAINTENANCE_MODE=True
    DATABASE_USER=kuma_ro

   Using a read-only database user is not required in maintenance mode. You can run
   in maintenance mode just fine with only this setting::

    MAINTENANCE_MODE=True

   and going with a database user that has write privileges. The read-only database
   user simply provides a level of safety as well as notification (for example, an
   exception will be raised if an attempt to write the database slips through).

#. Update your local Docker instance::

    docker-compose up -d

#. You may need to recompile your static assets and then restart::

    docker-compose exec web make build-static
    docker-compose restart web

You should be good to go!

There is a set of integration tests for maintenance mode. If you'd like to run
them against your local Docker instance, first do the following:

#. Load the latest sample database (see :ref:`provision-the-database`).
#. Ensure that the test document "en-US/docs/User:anonymous:uitest" has been
   rendered (all of its macros have been executed). You can check this by
   browsing to http://localhost:8000/en-US/docs/User:anonymous:uitest. If
   there is no message about un-rendered content, you are good to go. If there
   is a message about un-rendered content, you will have to put your local
   Docker instance back into non-maintenance mode, and render the document:

   * Configure your ``.env`` file for non-maintenance mode::

       MAINTENANCE_MODE=False
       DATABASE_USER=root

   * ``docker-compose up -d``
   * Using your browser, do a shift-reload on
     http://localhost:8000/en-US/docs/User:anonymous:uitest

   and then put your local Docker instance back in maintenance mode:

   * Configure your ``.env`` file for maintenance mode::

       MAINTENANCE_MODE=True
       DATABASE_USER=kuma_ro

   * ``docker-compose up -d``

#. Configure your environment with DEBUG=False because the maintenance-mode
   integration tests check for the non-debug version of the not-found page::

       DEBUG=False
       MAINTENANCE_MODE=True
       DATABASE_USER=kuma_ro

   This, in turn, will also require you to recompile your static assets::

       docker-compose up -d
       docker-compose exec web ./manage.py compilejsi18n
       docker-compose exec web ./manage.py collectstatic
       docker-compose restart web

Now you should be ready for a successful test run::

    py.test --maintenance-mode -m "not search" tests/functional --base-url http://localhost:8000 --driver Chrome --driver-path /path/to/chromedriver

Note that the "search" tests are excluded. This is because the tests marked
"search" are not currently designed to run against the sample database.


.. _`Django Admin for Sites`: http://localhost:8000/admin/sites/site/

Enabling ``PYTHONWARNINGS``
===========================

Python `ignores some warnings`_ by default, including ``DeprecationWarning``.
To see these warnings, you can set the `PYTHONWARNINGS`_ environment variable
in your ``.env`` file. For example::

    # Show every warning, every time it occurs
    PYTHONWARNINGS=always

Or alternatively::

    # Show every warning, but ignore repeats
    PYTHONWARNINGS=default

Note: Explicitly setting ``PYTHONWARNINGS=default`` will not do what you expect.
It actually *disables* the default filters, ensuring that *every* warning gets
displayed, but only the first time it occurs on a given line.

See the `PYTHONWARNINGS`_ docs for more information on possible values.

.. _`ignores some warnings`: https://docs.python.org/3/library/warnings.html#default-warning-filter
.. _`PYTHONWARNINGS`: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONWARNINGS
