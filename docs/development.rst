===========
Development
===========

Basic Docker usage
==================
Edit files as usual on your host machine; the current directory is mounted
via Docker host mounting at ``/app`` within the ``kuma_web_1`` and
other containers. Useful docker sub-commands::

    docker exec -it kuma_web_1 bash  # Start an interactive shell
    docker logs kuma_web_1           # View logs from the web container
    docker-compose logs -f           # Continuously view logs from all containers
    docker restart kuma_web_1        # Force a container to reload
    docker-compose stop              # Shutdown the containers
    docker-compose up -d             # Start the containers
    docker-compose rm                # Destroy the containers

There are ``make`` shortcuts on the host for frequent commands, such as::

    make up         # docker-compose up -d
    make bash       # docker exec -it kuma_web_1 bash
    make shell_plus # docker exec -it kuma_web_1 ./manage.py shell_plus

Run all commands in this doc in the ``kuma_web_1`` container after ``make bash``.

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

Front-end tests
---------------
To run the front-end (selenium) tests, see
:doc:`Client-side Testing <tests-ui>`.

Kumascript tests
----------------
If you're changing Kumascript, be sure to run its tests too.
See https://github.com/mdn/kumascript.

Front-end Development and Compiling Sass files
==============================================
Sass files need to be compiled for changes to take effect, but don’t worry,
with DEBUG=True (which is the default for local development), the compilation
can be done automatically by Gulp.

When doing front-end development on your local machine, run the following in its
own shell from the root directory of your local Kuma repository::

    gulp

This ``gulp`` command will do two things. First, it will watch *all* files
under ``./kuma/static``, and any changed file that is *not* a Sass file
(``.scss`` or ``.sass``) under ``./kuma/static/styles``, will be copied to
``./static`` as is (no compilation will be done).

Second, it will watch *all* files with a ``.scss`` extension under
``./kuma/static/styles``, and any change will trigger a ``stylelint``
of the changed file, as well as a recompile of *all* top-level ``.scss`` files.
All of the resulting compiled files will then be copied to ``./static``, and
immediately available to your local server.

.. note::

  It is currently faster for local development to compile Sass using
  ``gulp-sass`` instead of Django Pipeline. This may change in the future.

If you'd like to manually run ``stylelint`` locally on all ``.scss`` files under
``./kuma/static/styles``, do this::

    gulp css:lint

If you haven't already installed `Node.js`_  and `gulp`_ on
your local machine, see :ref:`frontend-development`.

By default ``DEBUG=True`` in ``docker-compose.yml``, and in that mode, as
mentioned above, source files are compiled on-demand. If for some reason you
want to run with ``DEBUG = False``, just remember that source files will no
longer be compiled on-demand. Instead, after every change to one or more source
files, you'll have to do the following::

    docker-compose exec web ./manage.py collectstatic
    docker-compose restart web

in order for your changes to be visible.

.. _gulp: http://gulpjs.com/
.. _`Node.js`: https://nodejs.org/

Database migrations
===================
Apps are migrated using Django's migration system. To run the migrations::

    manage.py migrate

If your changes include schema modifications, see the Django documentation for
the `migration workflow`_.

.. _migration workflow: https://docs.djangoproject.com/en/1.8/topics/migrations/#workflow

Coding conventions
==================
See CONTRIBUTING.md_ for details of the coding style on Kuma.

New code is expected to have test coverage.  See the
:doc:`Test Suite docs <tests>` for tips on writing tests.

.. _CONTRIBUTING.md: https://github.com/mozilla/kuma/blob/master/CONTRIBUTING.md

Managing dependencies
=====================

Python dependencies
-------------------
Kuma tracks its Python dependencies with pip_.  See the
`README in the requirements folder`_ for details.

.. _pip: https://pip.pypa.io/
.. _README in the requirements folder: https://github.com/mozilla/kuma/tree/master/requirements

Front-end dependencies
----------------------
Front-end dependencies are managed by Bower_ and checked into the repository.
Follow these steps to add or upgrade a dependency:

#. On the host, update ``bower.json``.
#. (*Docker only*) In the container, install ``git`` (``apt-get install -y git``).
#. (*Docker only*) In the container, install ``bower-installer`` (``npm install -g bower-installer``).
#. In the VM or container, install the dependency (``bower-installer``).
#. On the host, prepare the dependency to be committed (``git add path/to/dependency``).

Front-end dependencies that are not already managed by Bower should begin using
this approach the next time they're upgraded.

.. _Bower: http://bower.io

Customizing with Environment Variables
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

.. _advanced_config_docker:

Customizing the Docker Environment
==================================
Running docker-compose_ will create and run several containers, and each
container's environment and settings are configured in ``docker-compose.yml``.
The settings are "baked" into the containers created by ``docker-compose up``.

To override a container's settings for development, use a local override file.
For example, the ``web`` service runs in container ``kuma_web_1`` with the
default command
"``gunicorn -w 4 --bind 0.0.0.0:8000 --timeout=120 kuma.wsgi:application``".
A useful alternative for debugging is to run a single-threaded process that
loads the Werkzeug debugger on exceptions (see docs for runserver_plus_), and
that allows for stepping through the code with a debugger.
To use this alternative, create an override file ``docker-compose.dev.yml``::

    version: "2.1"
    services:
      web:
        command: ./manage.py runserver_plus 0.0.0.0:8000
        stdin_open: true
        tty: true


This is similar to "``docker run -it <image> ./manage.py runserver_plus``",
using all the other configuration items in ``docker-compose.yml``.
Apply the custom setting with::

    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

You can then add ``pdb`` breakpoints to the code
(``import pdb; pdb.set_trace``) and connect to the debugger with::

    docker attach kuma_web_1

To always include the override compose file, add it to your ``.env`` file::

    COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml

A similar method can be used to override environment variables in containers,
run additional services, or make other changes.  See the docker-compose_
documentation for more ideas on customizing the Docker environment.

.. _docker-compose: https://docs.docker.com/compose/overview/
.. _pdb: https://docs.python.org/2/library/pdb.html
.. _runserver_plus: http://django-extensions.readthedocs.io/en/latest/runserver_plus.html

Customizing The database
========================
The database connection is defined by the environment variable
``DATABASE_URL``, with this default::

    DATABASE_URL=mysql://root:kuma@mysql:3306/developer_mozilla_org

The format is defined by the dj-database-url_ project::

    DATABASE_URL=mysql://user:password@host:port/database

If you configure a new database, override ``DATABASE_URL`` to connect to it. To
add an empty schema to a freshly created database::

    ./manage.py migrate

To connect to the database specified in ``DATABASE_URL``, use::

    ./manage.py dbshell

.. _dj-database-url: https://github.com/kennethreitz/dj-database-url

Generating Production Assets
============================
Kuma will automatically run in debug mode, with the ``DEBUG`` setting turned to
``True``. Setting ``DEBUG=False`` will put you in production mode and
generate/use minified (compressed) and versioned (hashed) assets. To
emulate production, and test compressed and hashed assets locally:

#. Set the environment variable ``DEBUG=false``.
#. Start (``docker-compose up -d``) or restart (``docker-compose restart``)
   your Docker services.
#. Run ``docker-compose exec web make build-static``.
#. Restart the web process using ``docker-compose restart web``.

Using Secure cookies
====================
To prevent error messages like "``Forbidden (CSRF cookie not set.):``", set the
environment variable::

    CSRF_COOKIE_SECURE = false

This is the default in Docker, which does not support local development with
HTTPS.


Deis Workflow Demo instances
============================
You can deploy a hosted demo instance of Kuma by following these steps:

#. Create a new branch, you cannot create a demo from the ``master`` branch.
#. from the Kuma project root directory, run the following command::

    make create-demo

#. Your demo will be accessible within about 10 minutes at::

    https://mdn-demo-<your_branch_name>.portland.moz.works

#. Mozilla SRE's will periodically remove old instances

#. Connecting to the demo database instance

If you have access to Kubernetes, you can run the following command to connect
to the MySQL instance::

    MY_GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    DEMO_MYSQL_POD=$(kubectl -n "mdn-demo-${MY_GIT_BRANCH}" get pods | grep "^mysql" | awk '{ print $1 }')
    kubectl -n "mdn-demo-${MY_GIT_BRANCH}" exec -it ${DEMO_MYSQL_POD} bash

    mysql -p developer_mozilla_org

**Note**: if you copy and paste the code above into a bash terminal and are
wondering why the commands don't appear in your bash history, it's because there's
whitespace at the beginning of the line.

.. _maintenance-mode:

Maintenance Mode
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

