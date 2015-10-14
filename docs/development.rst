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

Pure Python Packages
--------------------

All of the pure Python dependencies are included in the git repository,
in the ``vendor`` subdirectory. This allows them to be available on the
Python path without needing to be installed in the system, allowing multiple
versions for multiple projects simultaneously.

Compiled Python Packages
------------------------

There are a small number of compiled packages, including the MySQL Python
client. You can install these using ``pip`` or via a package manager.
To use ``pip``, you only need to do the following.

First SSH into the Vagrant VM::

    vagrant ssh

Then disable the virtualenv that is auto-enabled and install the compiled
dependencies::

    deactivate
    sudo pip install -r requirements/compiled.txt

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
#. Run ``./manage.py collectstatic``
#. Edit the file /etc/apache2/sites-enabled/kuma.conf and uncomment any lines
   pertaining to hosting static files
#. Run ``sudo service apache2 restart``


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

