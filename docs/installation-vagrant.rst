Kuma via Vagrant
================

Core developers often run Kuma in a `Vagrant`_-managed virtual machine to
simplify :doc:`installation <installation>`. If you're on Mac OS X or Linux
and looking for a quick way to get started, you should try these instructions.

.. note:: **If you have problems using vagrant**, please paste any errors to `pastebin`_, and `email dev-mdn@lists.mozilla.org <mailto:dev-mdn@lists.mozilla.org?subject=vagrant%20issue>`_. After you email dev-mdn, you can also ask in `IRC`_

.. _vagrant: http://vagrantup.com/
.. _uses NFS to share the current working directory: http://docs.vagrantup.com/v2/synced-folders/nfs.html
.. _pastebin: http://pastebin.mozilla.org/
.. _IRC: irc://irc.mozilla.org:6697/#mdndev

Getting up and running
----------------------

#. Install VirtualBox 4.x from http://www.virtualbox.org/

#. (Windows) After installing VirtualBox you need to set the path
                PATH=C:\Program Files\Oracle\VirtualBox\VBoxManage.exe;

#. Install vagrant >= 1.6 using the installer from `vagrantup.com <http://vagrantup.com/>`_

#. Install the `vagrant-vbguest <https://github.com/dotless-de/vagrant-vbguest>`_
   plugin to keep the guest additions automatically up-to-date.

#. Fork the project into your own account. (If you need help, follow the instructions from `Webdev Bootcamp <http://mozweb.readthedocs.org/en/latest/git.html#working-on-projects>`_)

#. Clone your fork of Kuma and update submodules (If you have a local, non-vagrant kuma setup, **don't** try to use the same kuma working directory as the local kuma installation)::

       git clone git@github.com:<your_username>/kuma.git
       cd kuma
       git submodule update --init --recursive

#. Create a ``vagrantconfig_local.yaml`` file to configure your VM::

       cp vagrantconfig_local.yaml-dist vagrantconfig_local.yaml

#. Fire up the VM and install everything. (approx. 30 min on a fast net connection).::

      vagrant up

   VirtualBox creates VMs in your system drive. Kuma's VM is 3GB.
   If it won't fit on your system drive, you will need to `change that directory to another drive <http://emptysquare.net/blog/moving-virtualbox-and-vagrant-to-an-external-drive/>`_.


#. If the above process fails with an error, try running the Puppet setup
   again with the following command::

       vagrant provision

   In some rare occasions you might need to run this multiple times.

#. On Ubuntu, ``vagrant up`` might fail after being unable to mount NFS shared
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

#. Add some hostnames to the end of your hosts file with this shell command::

       echo '192.168.10.55 developer-local.allizom.org mdn-local.mozillademos.org' | sudo tee -a /etc/hosts

#. Everything should be working now, you should be able to log into a shell in the VM as the user
   ``vagrant``::

       vagrant ssh

#. Then you need to run ``foreman`` inside the VM in order to be able to work and access the site::

       foreman start

#. Visit the following address in your browser and add an exception for the security certificate if prompted::

       https://mdn-local.mozillademos.org

#. Visit the following address in your browser and you should see the homepage::

       https://developer-local.allizom.org/

#. You're done!


Enabling Important Site Features
--------------------------------

Some site functionality needs to be enabled before being used.

To enable KumaScript (Kuma's template system), log in, visit
"/admin/constance/config/", and change ``KUMASCRIPT_TIMEOUT`` to a non-zero
value.

Other site features are managed using Waffle flags. To enable these features,
log in, visit "/admin/waffle/flag/", and create one flag for each desired
feature. Be sure to choose "Yes" for the "Everyone" option. Some Waffle flags
include:

-  ``kumaediting``:  Allows creation, editing, and translating of documents
-  ``page_move``:  Allows moving of documents
-  ``events_map``:  Allows display of map on the events page


What’s next?
------------

Edit files as usual on your host machine; the current directory is
mounted via NFS at /home/vagrant/src within the VM. Updates should be
reflected without any action on your part.

Create an admin user
~~~~~~~~~~~~~~~~~~~~

-  After your first sign in, SSH into the vagrant box and add yourself as an admin::

      vagrant ssh
      mysql -uroot kuma
      UPDATE auth_user set is_staff = 1, is_active=1, is_superuser = 1 WHERE username = 'YOUR_USERNAME'

- Alternatively, you can simply issue the command in the host directory::

      ./manage.py createsuperuser

Create pages
~~~~~~~~~~~~

You can visit `https://developer-local.allizom.org/docs/new
<https://developer-local.allizom.org/docs/new>`_ to create new wiki pages as
needed or download a sanitised version of the ``devmo`` database.

- Download a dump of ``devmo_sanitized-latest.sql.bz2`` from `https://developer.allizom.org/landfill/ <https://developer.allizom.org/landfill/>`_, extract it in the host directory, and import it to your local database by running a command like the following in the VM::

     mysql -uroot kuma < /path/to/database/dump.sql

  You can then delete the extracted file.

-  Download a dump of the ``attachments-2014-06-13.tar.gz`` from
   `https://developer.allizom.org/landfill/
   <https://developer.allizom.org/landfill/>`_, extract it in "/media/attachments".


After configuration changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  You should occasionally re-run the Puppet setup, especially after
   updating code with major changes. This will ensure that the VM
   environment stays up to date with configuration changes and
   installation of additional services.

   -  On the Host::

          vagrant provision

   -  Inside the VM::

          sudo puppet apply /home/vagrant/src/puppet/manifests/dev-vagrant.pp


Developing with Vagrant
-----------------------

-  See :doc:`development <development>` for tips not specific to vagrant.

-  Useful vagrant sub-commands::

       vagrant ssh     # Connect to the VM via ssh
       vagrant suspend # Sleep the VM, saving state
       vagrant halt    # Shutdown the VM
       vagrant up      # Boot up the VM
       vagrant destroy # Destroy the VM


