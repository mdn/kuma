Kuma via Vagrant
================

Core developers run Kuma in a `Vagrant`_-managed virtual machine so we can run
the entire MDN stack. (Django, KumaScript, Search, Celery, etc.)
If you're on Mac OS X or Linux and looking for a quick way to get started, you
should try these instructions.

At the end, you'll earn `the badge`_:

.. image:: https://badges.mozilla.org/media/uploads/badge/2/3/23fef80968a03f3ba32321a7f31ae1e2_image_1372816280_0238.png

.. note:: **If you have problems using vagrant**, check Troubleshooting_ below

.. _vagrant: http://vagrantup.com/
.. _uses NFS to share the current working directory: http://docs.vagrantup.com/v2/synced-folders/nfs.html

Install and run everything
--------------------------

#. Install VirtualBox 4.x from http://www.virtualbox.org/

   .. note:: (Windows) After installing VirtualBox you need to set
              PATH=C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe;

#. Install vagrant >= 1.6 using the installer from `vagrantup.com <http://vagrantup.com/>`_

#. Install the `vagrant-vbguest <https://github.com/dotless-de/vagrant-vbguest>`_
   plugin.

#. Fork the project. (See `GitHub <https://help.github.com/articles/fork-a-repo#step-1-fork-the-spoon-knife-repository>`_ and `Webdev Bootcamp <http://mozweb.readthedocs.org/en/latest/git.html#working-on-projects>`_)

#. Clone your fork of Kuma and update submodules::

       git clone git@github.com:<your_username>/kuma.git
       cd kuma
       git submodule update --init --recursive

#. Copy a ``vagrantconfig_local.yaml`` file for your VM::

       cp vagrantconfig_local.yaml-dist vagrantconfig_local.yaml

#. Start the VM and install everything. (approx. 30 min on a fast net connection).::

      vagrant up

   .. note:: VirtualBox creates VMs in your system drive. Kuma's VM is 3GB.
             If it won't fit on your system drive, you will need to `change that directory to another drive <http://emptysquare.net/blog/moving-virtualbox-and-vagrant-to-an-external-drive/>`_.

   At the end, you should see::

      => default: notice: Finished catalog run in .... seconds


   If the above process fails with an error, check `Troubleshooting`_.


#. Add the hostnames to the end of your hosts file with this shell command::

       echo '192.168.10.55 developer-local.allizom.org mdn-local.mozillademos.org' | sudo tee -a /etc/hosts

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

#. Visit the following address in your browser and add an exception for the security certificate if prompted::

       https://mdn-local.mozillademos.org

#. Go to the homepage::

       https://developer-local.allizom.org/

#. You've installed Kuma! If you want `the badge`_, send a screenshot of your
   browser to luke dot crouch at gmail dot com.

.. _the badge: https://badges.mozilla.org/badges/badge/Installed-and-ran-Kuma

Create an admin user
--------------------

You will want to make yourself an admin user to enable important site features.

#. Sign up/in with Persona

#. After you sign in, SSH into the vm and make yourself an admin::

      vagrant ssh
      mysql -uroot kuma
      UPDATE auth_user set is_staff = 1, is_active=1, is_superuser = 1 WHERE username = 'YOUR_USERNAME';

   You should see::

      Query OK, 1 row affected (0.01 sec)
      Rows matched: 1  Changed: 1  Warnings: 0

Enable Important Site Features
------------------------------

Some site features are controlled using `django-waffle <http://waffle.readthedocs.org/en/latest/>`_.
You control these features in the `waffle admin
<https://developer-local.allizom.org/admin/waffle/>`_.

Some site features are controlled using `constance
<https://github.com/comoga/django-constance>`_. You control these features in
the `constance config admin panel`_.

Wiki Editing
~~~~~~~~~~~~

The central feature of MDN is wiki editing. We use a waffle flag called
``kumaediting`` to control edits to the wiki. So we can effectively put the
site into "read-only" and/or "write-by-staff-only" modes.

To enable wiki editing on your MDN vm, `add a waffle flag`_ called
``kumaediting`` and set "Everyone" to "Yes".

.. _add a waffle flag: https://developer-local.allizom.org/admin/waffle/flag/add/

KumaScript
~~~~~~~~~~

To enable KumaScript (Kuma's template system):

#. Sign in
#. Visit the `constance config admin panel`_
#. Change ``KUMASCRIPT_TIMEOUT`` to 600
#. Click "Save" at the bottom

.. _constance config admin panel: https://developer-local.allizom.org/admin/constance/config/

Create pages
------------

You can visit `https://developer-local.allizom.org/docs/new
<https://developer-local.allizom.org/docs/new>`_ to create new wiki pages as
needed.

Many core MDN contributors create a personal ``User:<username>`` page as a testing sandbox.

Import the entire MDN wiki
--------------------------

MDN content and code are inter-dependent - a.k.a., tightly-coupled. :(

To work on Kuma code with a fully-functioning, anonymized copy of the MDN
database.

#. Download `devmo_sanitized-latest.sql.bz2 <https://developer.allizom.org/landfill/devmo_sanitized-latest.sql.bz2>`_ (400 MB) from `landfill <https://developer.allizom.org/landfill/>`_

#. Extract it in your kuma directory::

    bunzip devmo_sanitized-latest.sql.bz2

#. Import the unzip'd .sql to your local database::

     vagrant ssh
     mysql -uroot kuma < /path/to/database/dump.sql

#. (Optional) Download the ``attachments-....tar.gz`` from
   `landfill <https://developer.allizom.org/landfill/>`_ and extract it into
   "/media/attachments".


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



.. _Troubleshooting:

Troubleshooting
---------------

Errors during `vagrant up`
~~~~~~~~~~~~~~~~~~~~~~~~~~

``vagrant up`` starts the virtual machine. The first time you run ``vagrant up`` it
also `provisions <https://docs.vagrantup.com/v2/cli/provision.html>`_ the vm -
i.e., it automatically installs and configures Kuma software on the vm. We
provision the vm with `puppet`_ manifests in the `puppet/manifests directory
<https://github.com/mozilla/kuma/tree/master/puppet/manifests>`_.

Sometimes we put puppet declarations in the wrong order. Which means some
errors can be fixed by simply provisioning the vm again::

       vagrant provision

In some rare occasions you might need to run this multiple times. If you see
the same error over and over, please ask for `more help`_.

On Ubuntu, ``vagrant up`` might fail after being unable to mount NFS shared
folders. First, make sure you have the nfs-common and nfs-server packages
installed and also note that you can't export anything via NFS inside an
encrypted volume or home dir.

If that doesn't help you can disable nfs by setting the nfs flag in the
vagrantconfig_local.yaml file you just created.

::

   nfs: false

Note: If you decide to run ``nfs: false``, the system will be a lot slower.
There is also the potential of running into weird issues with puppet,
since the current puppet configurations do not currently support
``nfs: false``.

If you have other problems during ``vagrant up``, please ask for `more help`_.

Errors after switching branches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  You should occasionally re-run the Puppet setup, especially after
   updating code with major changes. This will ensure that the VM
   environment stays up to date with configuration changes and
   installation of additional services.

   -  On the Host::

          vagrant provision

   -  Inside the VM::

          sudo puppet apply /home/vagrant/src/puppet/manifests/dev-vagrant.pp

.. _more help:

Getting more help
~~~~~~~~~~~~~~~~~

If you have more problems using vagrant, please:

#. Paste errors to `pastebin`_
#. `email dev-mdn@lists.mozilla.org <mailto:dev-mdn@lists.mozilla.org?subject=vagrant%20issue>`_.
#. After you email dev-mdn, you can also ask in `IRC`_

.. _pastebin: http://pastebin.mozilla.org/
.. _IRC: irc://irc.mozilla.org:6697/#mdndev
.. _puppet: http://puppetlabs.com/puppet/puppet-open-source
