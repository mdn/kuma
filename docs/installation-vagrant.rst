Kuma via Vagrant
================

The core developers run Kuma in a `Vagrant`_-managed virtual machine to
simplify :doc:`installation <installation>`. If you're on Mac OS X or Linux
and looking for a quick way to get started, you should try these instructions.

.. _vagrant: http://vagrantup.com/
.. _uses NFS to share the current working directory: http://docs.vagrantup.com/v2/synced-folders/nfs.html

Getting up and running
----------------------

#. Install VirtualBox 4.x from http://www.virtualbox.org/

#. Install vagrant using the installer from `vagrantup.com <http://vagrantup.com/>`_

#. To follow the instructions from `Webdev Bootcamp <http://mozweb.readthedocs.org/en/latest/git.html#working-on-projects>`_,
   fork the project into your own account.

#. Clone your fork of Kuma and update submodules (**don't** try to use the same working
   directory as for the local installation)::

       git clone git@github.com:<your_username>/kuma.git
       cd kuma
       git submodule update --init --recursive

#. Create a ``vagrantconfig_local.yaml`` file to configure your VM::

       cp vagrantconfig_local.yaml-dist vagrantconfig_local.yaml

   This may have some interesting settings for you to tweak, but the
   defaults should work fine.

#. The next step is to fire up the VM and install everything.
   By default, VirtualBox creates VMs in your system drive and kuma's VM
   weighs 3GB; so you might need to change that directory to another drive
   following `that tutorial <http://emptysquare.net/blog/moving-virtualbox-and-vagrant-to-an-external-drive/>`_.
   When you are ready, use the following command and go take a bike ride
   (approx. 30 min on a fast net connection).::

      vagrant up

#. If the above process fails with an error, try running the Puppet setup
   again with the following command::

       vagrant provision

   This often recovers from transient network issues or installation
   ordering problems. However, In some rare occasions you might need
   to run this multiple times

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

#. Everything should be working now, from the host side::

       curl 'https://developer-local.allizom.org'

#. You should be able to log into a shell in the VM as the user
   ``vagrant``::

       vagrant ssh

What’s next?
------------

-  See :doc:`development <development>` for tips not specific to vagrant.

-  Django and node.js web services must be started within the VM by
   hand, which makes them easier to restart during development. Details
   on this should be displayed via ``/etc/motd`` when you log in with
   ``vagrant ssh``

-  Edit files as usual on your host machine; the current directory is
   mounted via NFS at /home/vagrant/src within the VM. Update should be
   reflected without any action on your part.

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

Important Waffle Flags
----------------------

Some site funcationaly require waffle flags.  Waffle flags include:

-  ``kumaediting``:  Allows creation, editing, and translating of documents
-  ``page_move``:  Allows moving of documents
-  ``revision-dashboard-newusers``:  Allows searching of new users through the revision dashboard
-  ``events_map``:  Allows display of map on the events page
-  ``elasticsearch``:  Enables elastic search for site search
-  ``redesign``:  Enables the latest MDN redesign styles and layouts

To create or modify waffle flags, visit "/admin/" and click the "Waffle" link.

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
