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

#. Install vagrant using the installer from `vagrantup.com <http://vagrantup.com/>`_

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

#. You're done! Visit the following address in your browser and you should see the homepage::

       https://developer-local.allizom.org


What’s next?
------------

-  See :doc:`development <development>` for tips not specific to vagrant.

-  Useful vagrant sub-commands::

       vagrant ssh     # Connect to the VM via ssh
       vagrant suspend # Sleep the VM, saving state
       vagrant halt    # Shutdown the VM
       vagrant up      # Boot up the VM
       vagrant destroy # Destroy the VM

-  You should occasionally re-run the Puppet setup, especially after
   updating code with major changes. This will ensure that the VM
   environment stays up to date with configuration changes and
   installation of additional services.

   -  On the Host::

          vagrant provision

   -  Inside the VM::

          sudo puppet apply /home/vagrant/src/puppet/manifests/dev-vagrant.pp

-  After your first sign in, SSH into the vagrant box and add yourself as an admin::

      vagrant ssh
      mysql -uroot kuma
      UPDATE auth_user set is_staff = 1, is_active=1, is_superuser = 1 WHERE username = 'YOUR_USERNAME'

- Alternatively, you can simply issue the command::

      ./manage.py createsuperuser

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


Developing with Vagrant
-----------------------

-  Edit files as usual on your host machine; the current directory is
   mounted via NFS at /home/vagrant/src within the VM. Update should be
   reflected without any action on your part.

-  Visit `https://developer-local.allizom.org/docs/new
   <https://developer-local.allizom.org/docs/new>`_ to create new wiki pages as
   needed. Alternatively, download a dump of the ``devmo`` database from
   `https://developer.allizom.org/landfill/
   <https://developer.allizom.org/landfill/>`_ or `Amazon S3
   <https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/vagrant/mdn/devmo_sanitized-latest.sql.gz>`_ (587 mb), extract it, and import it to
   your local database by running a command like the following in the VM::

     cat devmo_sanitized-latest.sql.gz | gzip -dc | mysql -uroot kuma


AWS and Rackspace
-----------------

The kuma's Vagrant configuration also optionally supports using other backends
for Vagrant. Right now there are three supported:

#. Vmware Fusion (for Mac OS) and Workstation (Windows and Linux)

   Vagrant has commercial support for this alternative virtual machine
   system from VMware that is known to provide improved speed and better
   Linux and Windows support for the host systems.

   The necessary Vagrant plugin for that is commercially available at
   http://www.vagrantup.com/vmware. Please follow the instructions there
   if you want to make use of this.

   Then make sure you run the above mentioned ``vagrant up`` command with
   the appropriate ``--provider`` option. For VMware Fusion (Mac OS)::

     vagrant up --provider=vmware_fusion

   for VMware Workstation (Windows and Linux)::

     vagrant up --provider=vmware_workstation

   For further information see Vagrant documentation about using VMware:

     http://docs.vagrantup.com/v2/vmware/

#. Amazon Web Services (EC2 and VPC)

   First, install the AWS Vagrant plugin from Github:

    https://github.com/mitchellh/vagrant-aws

   Then make sure you've modified all the ``aws_*`` configuration options
   in your ``vagrantconfig_local.yaml``. Then run::

     vagrant up --provider=aws

#. Rackspace Cloud

   First install the Rackspace Cloud Vagrant plugin from Github:

    https://github.com/mitchellh/vagrant-rackspace

   Then modified all ``rs_*`` configuration options in your
   ``vagrantconfig_local.yaml``. Then run::

     vagrant up --provider=rackspace

