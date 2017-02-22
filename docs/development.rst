===========
Development
===========

Pick an environment
===================
There are two development environments, and you need to install at
least one of them first.

* The :doc:`Docker containerized environment <installation>` is the
  preferred development environment. The Docker images are already provisioned,
  so setup is faster. It is a better model for the production environment, and
  after the planned rehost will be almost exactly the same. It does not yet
  have all of the features of the Vagrant environment, and it is currently
  slower for many development tasks.
* The :doc:`Vagrant-managed VM <installation-vagrant>` is the mature but
  deprecated development environment. It can be tricky to provision. It is
  often a poor model for the production environment, and can not be used to
  test infrastructure changes.

Docker and Vagrant can be used at the same time on the same "host machine" (your
laptop or desktop computer).

Basic Docker usage
------------------
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

Basic Vagrant usage
-------------------
Edit files as usual on your host machine; the current directory is
mounted via NFS at ``/home/vagrant/src`` within the VM. Updates should be
reflected without any action on your part. Useful vagrant sub-commands::

    vagrant ssh     # Connect to the VM via ssh
    vagrant suspend # Sleep the VM, saving state
    vagrant halt    # Shutdown the VM
    vagrant up      # Boot up the VM
    vagrant destroy # Destroy the VM

Run all commands in this doc on the VM after ``vagrant ssh``.

Running Kuma
============
When the Docker container environment is started (``make up`` or similar), all
of the services are also started. The development instance is available at
http://localhost:8000.

The Vagrant environment runs everything in a single VM. It runs MySQL,
ElasticSearch, Apache, and other "backend" services whenever the VM is running.
There are additional Kuma-specific services that are configured in
``Procfile``, and are run with::

    foreman start

The Vagrant development instance is then available at
https://developer-local.allizom.org.

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
See https://github.com/mozilla/kumascript.

Front-end Development and Compiling Sass files
==============================================
Sass files need to be compiled for changes to take effect, but don't worry,
the compilation is done automatically by Django (specifically django-pipeline).

When doing front-end development on your local machine, you'll probably
want to run (most likely in its own shell)::

    gulp

within the root directory of your local Kuma epository. It will watch for
changes to any source files under ``./kuma/static`` and move any changed files
to ``./static``, where they will be compiled on-demand (i.e., when requested by
a loading page). If you haven't already installed `Node.js`_  and `gulp`_ on
your local machine, see :ref:`frontend-development`.

By default ``DEBUG = True`` in ``docker-compose.yml``, and in that mode, as
mentioned above, source files are compiled on-demand. If for some reason you
want to run with ``DEBUG = False``, just remember that source files will no
longer be compiled on-demand. Instead, after every change to one or more source
files, you'll have to do the following::

    docker-compose exec web make collectstatic
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

Advanced configuration
======================
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

The Docker environment
----------------------
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

    version: "2"
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

.. _vagrant-config:

The Vagrant environment
-----------------------
It is easiest to configure Vagrant with a ``.env`` file, so that overrides are used
when ``vagrant up`` is called.  A sample ``.env`` could contain::

    VAGRANT_MEMORY_SIZE=4096
    VAGRANT_CPU_CORES=4
    # Comments are OK, for documentation and to disable settings
    # VAGRANT_ANSIBLE_VERBOSE=true

Configuration variables that are available for Vagrant:

- ``VAGRANT_NFS``

  Default: ``true`` (Windows: ``false``)
  Whether or not to use NFS for the synced folder.

- ``VAGRANT_MEMORY_SIZE``

  The size of the Virtualbox VM memory in MB. Default: ``2048``.

- ``VAGRANT_CPU_CORES``

  The number of virtual CPU core the Virtualbox VM should have. Default: ``2``.

- ``VAGRANT_IP``

  The static IP the Virtualbox VM should be assigned to. Default: ``192.168.10.55``.

- ``VAGRANT_GUI``

  Whether the Virtualbox VM should boot with a GUI. Default: ``false``.

- ``VAGRANT_ANSIBLE_VERBOSE``

  Whether the Ansible provisioner should print verbose output. Default: ``false``.

- ``VAGRANT_CACHIER``

  Whether to use the ``vagrant-cachier`` plugin to cache system packages
  between installs. Default: ``true``.

The database
------------
The database connection is defined by the environment variable
``DATABASE_URL``, with these defaults::

    DATABASE_URL=mysql://kuma:kuma@localhost:3306/kuma              # Vagrant
    DATABASE_URL=mysql://root:kuma@mysql:3306/developer_mozilla_org # Docker

The format is defined by the dj-database-url_ project::

    DATABASE_URL=mysql://user:password@host:port/database

If you configure a new database, override ``DATABASE_URL`` to connect to it. To
add an empty schema to a freshly created database::

    ./manage.py migrate

To connect to the database specified in ``DATABASE_URL``, use::

    ./manage.py dbshell

.. _dj-database-url: https://github.com/kennethreitz/dj-database-url

Asset generation
----------------
Kuma will automatically run in debug mode, with the ``DEBUG`` setting turned to
``True``. Setting ``DEBUG=False`` will put you in production mode and
generate/use minified (compressed) and versioned (hashed) assets. To
emulate production, and test compressed and hashed assets locally:

#. Set the environment variable ``DEBUG=false``.
#. Start (``docker-compose up -d``) or restart (``docker-compose restart`)
   your Docker services.
#. Run ``docker-compose exec web make build-static``.
#. Restart the web process using ``docker-compose restart web``.

Secure cookies
--------------
To prevent error messages like "``Forbidden (CSRF cookie not set.):``", set the
environment variable::

    CSRF_COOKIE_SECURE = false

This is the default in Docker, which does not support local development with
HTTPS.


Deis Workflow Demo instances
----------------
You can deploy a hosted demo instance of Kuma by following these steps:

#. Create a new branch, you cannot create a demo from the ``master`` branch.
#. from the Kuma project root directory, run the following command::

    make create-demo

#. Your demo will be accessible within about 10 minutes at::

    https://mdn-demo-<your_branch_name>.virginia.moz.works

#. Mozilla SRE's will periodically remove old instances

