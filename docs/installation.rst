============
Installation
============

Core developers run Kuma in a `Vagrant`_-managed virtual machine so we can run
the entire MDN stack. (Django, KumaScript, Search, Celery, etc.)
If you're on Mac OS X or Linux and looking for a quick way to get started, you
should try these instructions.

.. note:: **If you have problems getting vagrant up**, check Errors_ below.

.. _vagrant: http://vagrantup.com/
.. _uses NFS to share the current working directory: http://docs.vagrantup.com/v2/synced-folders/nfs.html

Install and run everything
==========================

#. Install VirtualBox >= 4.2.x from http://www.virtualbox.org/

   .. note:: (Windows) After installing VirtualBox you need to set
              ``PATH=C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe;``

#. Install vagrant >= 1.7 using the installer from `vagrantup.com <http://vagrantup.com/>`_

#. Install `Ansible <http://docs.ansible.com/>`_ on your machine so that
   Vagrant is able to set up the VM the way we need it.

   See the `Ansible Installation docs <http://docs.ansible.com/intro_installation.html>`_
   for which way to use on your computer's platform.

   The most common platforms:

   Mac OS X::

       brew install ansible

   or if you have a globally installed pip::

       sudo pip install ansible

   Ubuntu::

       $ sudo apt-get install software-properties-common
       $ sudo apt-add-repository ppa:ansible/ansible
       $ sudo apt-get update
       $ sudo apt-get install ansible

   Fedora / RPM-based distribution::

       $ sudo dnf install ansible.noarch

   For previous versions based on yum, use::

       $ sudo yum install ansible.noarch

   Windows:

   Installation on Windows is complicated but we strive to make it easier
   in the future. Until then see this blog post for how to
   `Run Vagrant with Ansible Provisioning on Windows <http://www.azavea.com/blogs/labs/2014/10/running-vagrant-with-ansible-provisioning-on-windows/>`_

#. Fork the project. (See `GitHub <https://help.github.com/articles/fork-a-repo#step-1-fork-the-spoon-knife-repository>`)

#. Clone your fork of Kuma and update submodules::

       git clone git@github.com:<your_username>/kuma.git
       cd kuma
       git submodule update --init --recursive

#. Start the VM and install everything. (approx. 15 minutes on a fast net connection).::

      vagrant up

   .. note::

    VirtualBox creates VMs in your system drive. Kuma's VM is
    approx. 2GB. If it won't fit on your system drive, you will need
    to `change that directory to another drive <http://emptysquare.net/blog/moving-virtualbox-and-vagrant-to-an-external-drive/>`_.

   At the end, you should see::

      Finished catalog run in .... seconds

   If the above process fails with an error, check `Errors`_.

#. Log into the VM with ssh::

       vagrant ssh

#. Use ``foreman`` inside the VM to start all site services::

       foreman start

   You should see output like::

       20:32:59 web.1        | started with pid 2244
       20:32:59 celery.1     | started with pid 2245
       20:32:59 kumascript.1 | started with pid 2246
       20:32:59 stylus.1     | started with pid 2247
       ...

#. Visit `https://mdn-local.mozillademos.org/ <https://mdn-local.mozillademos.org/>`_ and add an exception for the security certificate if prompted.

#. Visit the homepage at `https://developer-local.allizom.org <https://developer-local.allizom.org/>`_

#. You've installed Kuma!

   If you want `the badge`_ please `email a screenshot of your browser <mailto:mdn-dev@mozilla.com?subject=Local%20MDN%20Screenshot>`_ to receive the badge.

   .. image:: https://badges.mozilla.org/media/uploads/badge/2/3/23fef80968a03f3ba32321a7f31ae1e2_image_1372816280_0238.png

.. _the badge: https://badges.mozilla.org/badges/badge/Installed-and-ran-Kuma

Dependencies
============

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

Configuration
=============

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

The kuma project
----------------

Start by creating a file named ``settings_local.py``, and putting this line in
it::

    from settings import *

Now you can copy and modify any settings from ``settings.py`` into
``settings_local.py`` and the value will override the default.

.. note::

   For some basic features you'll need to use
   :doc:`feature toggles <feature-toggles>` to enable them.

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

Setting ``DEBUG = False`` will put the installation in production mode
and ask for minified assets. In that case, you will need to generate
CSS from stylus and compress resource::

    ./scripts/compile-stylesheets
    ./manage.py compress_assets

.. _enable KumaScript:

KumaScript
~~~~~~~~~~

To enable KumaScript (Kuma's template system):

#. Sign in
#. Visit the `constance config admin panel`_
#. Change ``KUMASCRIPT_TIMEOUT`` to 600
#. Click "Save" at the bottom

KumaScript is now enabled. You will also want to import the `KumaScript auto-loaded modules`_.
You can simply copy & paste them from the production site to your local site at
the same slugs. Or you can email the dev-mdn@lists.mozilla.org list to get a .json file to
load in your local django admin interface as described in `this comment`_.

.. _constance config admin panel: https://developer-local.allizom.org/admin/constance/config/
.. _KumaScript auto-loaded modules: https://developer.mozilla.org/en-US/docs/MDN/Kuma/Introduction_to_KumaScript#Auto-loaded_modules
.. _this comment: https://github.com/mozilla/kuma/issues/2518#issuecomment-53665362

Mozilla Product Details
~~~~~~~~~~~~~~~~~~~~~~~

One of the packages Kuma uses, Django Mozilla Product Details, needs to
fetch JSON files containing historical Firefox version data and write them
to disk. To set this up, just run::

    ./manage.py update_product_details

...to do the initial fetch or run it again to update it.

.. _GitHub Auth:

GitHub Auth
~~~~~~~~~~~

To enable GitHub authentication ...

`Register your own OAuth application on GitHub`_:

* Application name: MDN (<username>)
* Homepage url: https://developer-local.allizom.org/docs/MDN/Contribute/Howto/Create_an_MDN_account
* Application description: My own GitHub app for MDN!
* Authorization callback URL: https://developer-local.allizom.org/users/github/login/callback/

`Add a django-allauth social app`_ for GitHub:

* Provider: GitHub
* Name: developer-local.allizom.org
* Client id: <your GitHub App Client ID>
* Secret key: <your GitHub App Client Secret>
* Sites: example.com -> Chosen sites

Now you can sign in with GitHub at https://developer-local.allizom.org/

.. _Add a django-allauth social app: https://developer-local.allizom.org/admin/socialaccount/socialapp/add/
.. _Register your own OAuth application on GitHub: https://github.com/settings/applications/new

Persona Auth
~~~~~~~~~~~~

Add the following to ``settings_local.py`` so that Persona works with the
development instance::

    SITE_URL = 'http://localhost:8000'
    PROTOCOL = 'http://'
    DOMAIN = 'localhost'
    PORT = 8000
    SESSION_COOKIE_SECURE = False # needed if the server is running on http://
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False

The ``SESSION_EXPIRE_AT_BROWSER_CLOSE`` setting is not strictly necessary, but
it's convenient for development.

Secure Cookies
~~~~~~~~~~~~~~

To prevent error messages like ``Forbidden (CSRF cookie not set.):``, you need to
set your ``settings_local.py`` with the following::

    CSRF_COOKIE_SECURE = False

Testing it Out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``. If everything's working, you should see
the MDN home page!

You might need to first set ``LC_CTYPE`` if you're on Mac OS X until
`bug 754728 <https://bugzilla.mozilla.org/show_bug.cgi?id=754728>`_ is fixed::

    export LC_CTYPE=en_US

Create an admin user
--------------------

You will want to make yourself an admin user to enable important site features.

#. Sign up/in with Persona

#. After you sign in, SSH into the VM and make yourself an admin (exchange
   ``<< YOUR_USERNAME >>`` with the username you used when signing up for
   Persona)::

    vagrant ssh
    mysql -ukuma -pkuma kuma -e "UPDATE auth_user set is_staff = 1, is_active=1, is_superuser = 1 WHERE username = '<< YOUR_USERNAME >>';"

   You should see::

      Query OK, 1 row affected (0.01 sec)
      Rows matched: 1  Changed: 1  Warnings: 0

Create pages
------------

You can visit `https://developer-local.allizom.org/docs/new
<https://developer-local.allizom.org/docs/new>`_ to create new wiki pages as
needed.

Many core MDN contributors create a personal ``User:<username>`` page as a
testing sandbox.

Developing with Vagrant
-----------------------

Edit files as usual on your host machine; the current directory is
mounted via NFS at ``/home/vagrant/src`` within the VM. Updates should be
reflected without any action on your part.

-  See :doc:`development <development>` for tips not specific to vagrant.

-  Useful vagrant sub-commands::

    vagrant ssh     # Connect to the VM via ssh
    vagrant suspend # Sleep the VM, saving state
    vagrant halt    # Shutdown the VM
    vagrant up      # Boot up the VM
    vagrant destroy # Destroy the VM

.. _Errors:

Errors during `vagrant up`
--------------------------

``vagrant up`` starts the virtual machine. The first time you run
``vagrant up`` it also `provisions <https://docs.vagrantup.com/v2/cli/provision.html>`_
the VM - i.e., it automatically installs and configures Kuma software in the
VM. We provision the VM with `Ansible`_ roles in the `provisioning directory
<https://github.com/mozilla/kuma/tree/master/provisioning>`_.

Sometimes we put Ansible roles in the wrong order. Which means some
errors can be fixed by simply provisioning the VM again::

    vagrant provision

In some rare occasions you might need to run this multiple times. If you find an
error that is fixed by running ``vagrant provision`` again, please email us the
error at dev-mdn@lists.mozilla.org and we'll see if we can fix it.

If you see the same error over and over, please ask for :ref:`more help <more-help>`.

.. _Ansible: http://docs.ansible.com/

Django database migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see errors that have "Django database migrations" in their
title try to manually run them in the VM to see more about them.
To do so::

    vagrant ssh
    python manage.py migrate

If you get an error, please ask for :ref:`more help <more-help>`.

Ubuntu
~~~~~~

On Ubuntu, ``vagrant up`` might fail after being unable to mount NFS shared
folders. First, make sure you have the nfs-common and nfs-server packages
installed and also note that you can't export anything via NFS inside an
encrypted volume or home dir. On Windows NFS won't be used ever by the way.

If that doesn't help you can disable NFS by setting the ``VAGRANT_NFS``
configration value in a ``.env`` file. See the :ref:`Vagrant configuration
<vagrant-config>` options for more info.

If you have other problems during ``vagrant up``, please check
:doc:`Troubleshooting <troubleshooting>`.
