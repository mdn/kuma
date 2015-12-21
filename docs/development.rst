===========
Development
===========

First, make sure you are running the :doc:`Vagrant-managed VM <installation>`.

Developing with Vagrant
=======================

Edit files as usual on your host machine; the current directory is
mounted via NFS at ``/home/vagrant/src`` within the VM. Updates should be
reflected without any action on your part. Useful vagrant sub-commands::

    vagrant ssh     # Connect to the VM via ssh
    vagrant suspend # Sleep the VM, saving state
    vagrant halt    # Shutdown the VM
    vagrant up      # Boot up the VM
    vagrant destroy # Destroy the VM

Run all commands in this doc on the vm after ``vagrant ssh``.

Running Kuma
============

You can start all Kuma servers and services on the vm with::

    foreman start

Running the Tests
=================

A great way to check that everything really is working is to run the test
suite.

Django tests
------------

Running the kuma Django test suite is easy::

    python manage.py test kuma

For more information, see the :doc:`test documentation <tests>`.

Front-end tests
---------------

To run the front-end (selenium) tests, see :doc:`Client-side Testing with
Intern <tests-ui>`.

Kumascript tests
----------------

If you're changing Kumascript, be sure to run its tests too.
See https://github.com/mozilla/kumascript

Compiling Stylus Files
======================

Stylus files need to be compiled for changes to take effect. Vagrant will
automatically compile Stylus files when they change, but compilation can also be
run manually::

    compile-stylesheets

The relevant CSS files will be generated and placed within the
`build/assets/css` directory. You can add a ``-w`` flag to that call to compile
stylesheets upon save.

Database Migrations
===================

Basically all apps are migrated using Django's migration system.

See the Django documentation for the
`migration workflow <https://docs.djangoproject.com/en/1.8/topics/migrations/#workflow>`_.

How to run the migrations
-------------------------

Run the migrations via the Django management command::

    python manage.py migrate

Coding Conventions
==================

Tests
-----

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the ``TestCase``
  class.

(Advanced) Managing Dependencies
================================

Python dependencies
-------------------

Kuma tracks its Python dependencies with pip_ and peep_.

The ``requirements`` directory contains the plaintext requirements files
that are used in the Vagrant VM, during automatic tests with Travis-CI
and duriing deployment to stage and prod.

Here's what that folder contains:

- ``compiled.txt`` - contains dependencies that require a compiler and may
  need to be treated differently dependending on environment

- ``default.txt`` - contains the default dependencies that are used in all
  environments

- ``docs.txt`` - contains dependencies that are required to build the docs

- ``tests.txt`` - a file for tests dependencies, both local and automatic

- ``travis.txt`` - a file used by the ``.travis.yml`` config file when
  running automatic testing

Adding a requirement
~~~~~~~~~~~~~~~~~~~~

To add a dependency you have to add it to the appropriate requirement file
in the ``requirements`` folder. To do that we'll use peep_ to get the hash
of the distribution file you'd like to install.

First SSH into the Vagrant VM::

    vagrant ssh

Add the requirement with the exact version specifier to the requirements
file most appropriate to the use of the dependency, e.g.
``requirements/default.txt``::

    django-pipeline==1.6.0

Then download a distribution file from PyPI_ or whatever source you deem
safe of the dependency you added above, e.g.::

    wget https://pypi.python.org/packages/source/d/django-pipeline/django-pipeline-1.6.0.tar.gz

Check if the file you downloaded contains what you expect and then use peep
to calculate a hash of the file you downloaded::

    script/peep.py django-pipeline-1.6.0.tar.gz

This will print out a hash in the form of::

    # sha256: paFCZIUSX_kQWjcNx9em6npTILXRgCcjA9QppD-BL-U

Add this string above the line of the requirement string in the requirements
file, e.g.::

    # sha256: paFCZIUSX_kQWjcNx9em6npTILXRgCcjA9QppD-BL-U
    django-pipeline==1.6.0

Then verify if the hash stil matches and install the new dependency in the VM::

    script/peep.py install -r requirements/default.txt

Updating a requirement
~~~~~~~~~~~~~~~~~~~~~~

Follow the same steps as when adding a requirement but replace the old peep
hash in the requirements file. Don't forget to run afterwards::

    script/peep.py install -r requirements/default.txt

Front-end dependencies
----------------------

Front-end dependencies are managed by Bower and checked into the repository.

Follow these steps to add or upgrade a dependency:

#. Update *bower.json*
#. Enter the virtual machine (``vagrant ssh``)
#. Install the dependency (``bower-installer``)
#. Exit the virtual machine (``exit``)
#. Prepare the dependency to be committed (``git add path/to/dependency``)

Front-end dependencies that are not already managed by Bower should begin using
this approach the next time they're upgraded.

(Advanced) Configuration
========================

.. _vagrant-config:

Vagrant
-------

If you'd like to change the way Vagrant works, we've added a few
configuration values that may be worthwhile to look at. In case something
doesn't suffice for your machine, please let us know!

To change the config values, simply create a dotenv_ file (``.env``) in the
directory (``/home/vagrant/src/.env`` in the Vagrant VM) and write
``<KEY>=<VALUE>`` for each configuration variable you'd like to set.

Here's the configuration variables that are available for Vagrant:

- ``VAGRANT_NFS``

  Default: true (Windows: false)
  Whether or not to use NFS for the synced folder.

- ``VAGRANT_MEMORY_SIZE``

  The size of the Virtualbox VM memory in MB. Default: 2048

- ``VAGRANT_CPU_CORES``

  The number of virtual CPU core the Virtualbox VM should have. Default: 2

- ``VAGRANT_IP``

  The static IP the Virtualbox VM should be assigned to. Default: 192.168.10.55

- ``VAGRANT_GUI``

  Whether the Virtualbox VM should boot with a GUI. Default: false

- ``VAGRANT_ANSIBLE_VERBOSE``

  Whether the Ansible provisioner should print verbose output. Default: false

A possible ``/home/vagrant/src/.env`` file could look like this for example::

    VAGRANT_MEMORY_SIZE=4096
    VAGRANT_CPU_CORES=4
    VAGRANT_ANSIBLE_VERBOSE=true

.. _dotenv: http://12factor.net/config

Database
~~~~~~~~

At a minimum, you will need to define a database connection. An example
configuration is::

    DATABASES = {
        'default': {
            'NAME': 'kuma',
            'ENGINE': 'django.db.backends.mysql',
            'HOST': 'localhost',
            'PORT': '3306',
            'USER': 'kuma',
            'PASSWORD': 'kuma',
            'OPTIONS': {
                'sql_mode': 'TRADITIONAL',
                'charset': 'utf8',
                'init_command': 'SET '
                    'storage_engine=INNODB,'
                    'character_set_connection=utf8,'
                    'collation_connection=utf8_general_ci',
            },
            'ATOMIC_REQUESTS': True,
            'TEST': {
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
            },
        },
    }

Note the two values ``CHARSET`` and ``COLLATION`` of the ``TEST`` setting.
Without these, the test suite will use MySQL's (moronic) defaults when
creating the test database (see below) and lots of tests will fail. Hundreds.

Once you've set up the database, you can generate the schema with Django's
``migrate`` command::

    ./manage.py migrate

This will generate an empty database, which will get you started!

Assets
~~~~~~

If you want to see images and have the pages formatted with CSS you need to
set your ``settings_local.py`` with the following::

    DEBUG = True
    TEMPLATE_DEBUG = DEBUG
    SERVE_MEDIA = True

Production assets
*****************

Assets are compressed on production. To emulate production and test compressed
assets locally, follow these steps:

#. In settings_local.py, set ``DEBUG = False``
#. In settings_local.py, set ``DEV = False``
#. Run ``vagrant ssh`` to enter the virtual machine
#. Run ``compile-stylesheets``
#. Run ``./manage.py compilejsi18n``
#. Run ``./manage.py collectstatic``
#. Stop ``foreman`` if it's already running
#. Run ``foreman start``


Mozilla Product Details
~~~~~~~~~~~~~~~~~~~~~~~

One of the packages Kuma uses, Django Mozilla Product Details, needs to
fetch JSON files containing historical Firefox version data and write them
to disk. To set this up, just run::

    ./manage.py update_product_details

...to do the initial fetch or run it again to update it.


Secure Cookies
~~~~~~~~~~~~~~

To prevent error messages like ``Forbidden (CSRF cookie not set.):``, you need to
set your ``settings_local.py`` with the following::

    CSRF_COOKIE_SECURE = False

.. _pip: https://pip.pypa.io/
.. _peep: https://pypi.python.org/pypi/peep
