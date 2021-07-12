.. _Troubleshooting:

Troubleshooting
===============

Kuma has many components. Even core developers need reminders of how to keep
them all working together. This doc outlines some problems and potential
solutions running Kuma.

Kuma "Reset"
------------
These commands will reset your environment to a "fresh" version, with the
current third-party libraries, while retaining the database::

  cd /path/to/kuma
  docker-compose down
  make clean
  git submodule sync --recursive && git submodule update --init --recursive
  docker-compose pull
  docker-compose build --pull
  docker-compose up

Reset a corrupt database
------------------------
The Kuma database can become corrupted if the system runs out of disk space,
or is unexpectedly shutdown. MySQL can repair some issues, but sometimes you
have to start from scratch. When this happens, pass an extra argument
``--volumes`` to ``down``::

  cd /path/to/kuma
  docker-compose down --volumes
  make clean
  docker-compose pull
  docker-compose build --pull
  docker-compose up -d mysql
  sleep 20  # Wait for Postgres to initialize. See notes below
  docker-compose up

The ``--volumes`` flag will remove the named MySQL database volume, which will
be recreated when you run ``docker-compose up``.

Run alternate services
----------------------
Docker services run as containers. To change the commands or environments of
services, it is easiest to add an override configuration file, as documented in
:ref:`advanced_config_docker`.

Linux file permissions
----------------------
On Linux, it is common that files created inside a Docker container are owned
by the root user on the host system. This can cause problems when trying to
work with them after creation. We are investigating solutions to create files
as the developer's user.

In some cases, you can specify the host user ID when running commands::

    docker-compose run --rm --user $(id -u) web ./manage.py collectstatic

In other cases, the command requires root permissions inside the container, and
this trick can't be used.

Another option is to allow the files to be created as root, and then change
them to your user on the host system::

    find . -user root -exec sudo chown $(id -u):$(id -g) \{\} \;

.. _more-help:
