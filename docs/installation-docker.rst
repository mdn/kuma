=======================
Installation via Docker
=======================

Kuma has experimental support for `Docker`_ as an alternative to the
Vagrant set up.

.. _Docker: https://www.docker.com/

Docker setup
============

#. Ensure you have cloned the kuma Git repository and it is your current
   working directory::

        git clone git@github.com:mozilla/kuma.git
        cd kuma

#. Install the `Docker Toolbox`_. This will install the Docker engine,
   along with Docker Compose and Docker Machine.

   .. _Docker Toolbox: https://www.docker.com/products/docker-toolbox

#. Create the virtual machine that Docker will run within::

        docker-machine create --driver virtualbox --virtualbox-memory 4096 kuma

#. Configure the environment variables::

        eval "$(docker-machine env kuma)"
        export COMPOSE_PROJECT_NAME=kuma  # String prepended to every container.

#. Add the Docker VM to your hosts::

        sudo sh -c "echo $(docker-machine ip kuma 2>/dev/null)  kuma.dev >> /etc/hosts"

#. Pull and build the containers::

        docker-compose pull
        docker-compose build

#. Start the containers::

        docker-compose up -d

At this point everything is running but we haven't set up the database
yet. You either need to import a data dump or run the Django migrations to
create the database and tables.

If you have a data dump you can connect to the "web" container and import
the data dump::

    mysql --default-character-set=utf8 -h mysql -ukuma -pkuma kuma < kuma.sql

Or run the migrations::

    docker exec -ti kuma_web_1 /bin/bash
    ./manage.py migrate


Interacting with the containers
===============================

You can connect to a running container to run commands if need be. For
example, you can connect to the "web" container::

        docker exec -ti kuma_web_1 /bin/bash

Once connected you can run the tests or interact with the database.

Stopping the containers and shutting down the VM
================================================

To stop the containers::

        docker-compose stop

To shut down the VM::

        docker-machine stop kuma
