Kuma in VirtualBox via Vagrant
==============================

This is an attempt to describe the bootstrap process to get Kuma running
in a Vagrant-managed virtual machine.

This is known to work on Mac OS X. It could possibly be made to work
under Linux and Windows, but few have tried. Bug reports and suggestions
are welcome. The main barrier to Windows is that this Vagrantfile `uses
NFS to share the current working directory`_ for performance reasons,
and also Vagrant support for Windows is not-so-great yet.

.. _uses NFS to share the current working directory: http://vagrantup.com/docs/nfs.html


Getting up and running
----------------------

-  Install VirtualBox 4 from http://www.virtualbox.org/
-  Install vagrant from a Terminal window, see vagrantup.com::

       gem update
       gem install vagrant

-  Clone Kuma, update submodules::

       git clone git://github.com/mozilla/kuma.git
       cd kuma
       git submodule update --init --recursive

-  Create a ``vagrantconfig_local.yaml`` file to configure your VM::

       cp vagrantconfig_local.yaml-dist vagrantconfig_local.yaml

   This may have some interesting settings for you to tweak, but the
   defaults should work fine.

-  Fire up the VM and install everything, go take a bike ride (approx.
   30 min on a fast net connection)::

       vagrant up

-  If the process fails with an error, try running the Puppet setup
   again::

       vagrant provision

   This often recovers from transient network issues or installation
   ordering problems.

-  Add developer-dev.mozilla.org to /etc/hosts::

       echo '192.168.10.55 developer-dev.mozilla.org' >> /etc/hosts

-  Everything should be working now, from the host side::

       curl 'http://developer-dev.mozilla.org'

-  You should be able to log into a shell in the VM as the user
   ``vagrant``::

       vagrant ssh

What’s next?
------------

-  Django and node.js web services must be started within the VM by
   hand, which makes them easier to restart during development. Details
   on this should be displayed via ``/etc/motd`` when you log in with
   ``vagrant ssh``

-  Edit files as usual on your host machine; the current directory is
   mounted via NFS at /vagrant within the VM. Update should be reflected
   without any action on your part.

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

          sudo puppet apply /vagrant/puppet/manifests/dev-vagrant-mdn.pp

-  **Experimental and Optional**: Download and import data extracted and
   sanitized from the production site. This can take a long while, since
   there’s over 500MB of data to download. ::

       vagrant ssh
       sudo puppet apply /vagrant/puppet/manifests/dev-vagrant-mdn-import.pp
       sudo puppet apply /vagrant/puppet/manifests/dev-vagrant.pp


