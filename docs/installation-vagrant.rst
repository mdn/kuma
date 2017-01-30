========================
Installation via Vagrant
========================
Since 2011, staff developers ran a model of the entire MDN stack in a
Vagrant_-managed virtual machine. This included backing services like a
database, caching server, and search engine, as well as the application
services like Django, KumaScript, and Celery.

Vagrant started out closely aligned with production, but over the years the
Vagrant environment evolved to make development easier, and the production
configuration was maintained by the operations team. For example, Vagrant
switched the operating system from CentOS_ to Ubuntu_, and the provisioning
system from Puppet_ to Ansible_. The Puppet scripts used to maintain the
production infrastructure have evolved, and can not be published or reused for
development due to configuration secrets. Both systems work, but it is less
likely that the development environment can be used to reproduce production
issues, or that the development environment can be used as a testbed for
infrastructure changes.

Starting in 2011, Kuma is moving to Docker for development, testing, and
deployment. Docker is now the primary development environment, and the
:doc:`Docker setup instructions <installation>` should be used by new
developers.

Until the transition is complete, we cover development with both the Docker and
the Vagrant environments. We do not plan to keep feature parity between the
environments, and will only fix critical errors in Vagrant provisioning.

There are common issues encountered when provisioning Vagrant, or maintaining a
long-lived installation. See the `Errors`_ section for tips and tricks, as well
as the :doc:`Troubleshooting page <troubleshooting>`.

.. _vagrant: http://vagrantup.com/
.. _CentOS: https://www.centos.org
.. _Ubuntu: http://www.ubuntu.com
.. _Puppet: https://puppet.com
.. _Ansible: http://docs.ansible.com/

Install and run everything
==========================

#. Install VirtualBox >= 5.0.x from http://www.virtualbox.org/

   .. note:: (Windows) After installing VirtualBox you need to set
              ``PATH=C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe;``

#. Install Vagrant >= 1.7 using the installer from `vagrantup.com <http://vagrantup.com/>`_.

#. Install `Ansible <http://docs.ansible.com/>`_ >= 1.9.x on your machine so that
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
   `Run Vagrant with Ansible Provisioning on Windows <http://www.azavea.com/blogs/labs/2014/10/running-vagrant-with-ansible-provisioning-on-windows/>`_.

#. Fork the project. (See `GitHub <https://help.github.com/articles/fork-a-repo#step-1-fork-the-spoon-knife-repository>`_)

#. Clone your fork of Kuma and update submodules::

       git clone git@github.com:<your_username>/kuma.git
       cd kuma
       git submodule update --init --recursive

#. Start the VM and install everything. (approx. 15 minutes on a fast net connection)::

      vagrant up

   .. note::

    VirtualBox creates VMs in your system drive. Kuma's VM is
    approx. 2GB. If it won't fit on your system drive, you will need
    to `change that directory to another drive <http://emptysquare.net/blog/moving-virtualbox-and-vagrant-to-an-external-drive/>`_.

   At the end, you should see something like::

      PLAY RECAP ********************************************************************
      developer-local            : ok=147  changed=90   unreachable=0    failed=0

      ==> developer-local: Configuring cache buckets...

   If the above process fails with an error, check `Errors`_.

#. Log into the VM with ssh::

       vagrant ssh

#. Use ``foreman`` inside the VM to start all site services::

       foreman start

   You should see output like::

       20:32:59 web.1        | started with pid 2244
       20:32:59 celery.1     | started with pid 2245
       20:32:59 kumascript.1 | started with pid 2246
       20:32:59 sass.1       | started with pid 2247
       ...

#. Visit https://mdn-local.mozillademos.org/ and add an exception for the security certificate if prompted.

#. Visit the homepage at https://developer-local.allizom.org

#. You've installed Kuma!

   Continue reading to create an admin user and enable the wiki.

.. _create a user:

Create an admin user
====================

You will want to make yourself an admin user to enable important site features.

#. Sign up/in with Persona.

#. After you sign in, SSH into the VM and make yourself an admin (exchange
   ``<< YOUR_USERNAME >>`` with the username you used when signing up for
   Persona)::

      vagrant ssh
      python manage.py ihavepower "<< YOUR_USERNAME >>"

   You should see::

      Done!

Enable the wiki
===============

By default, the wiki is disabled with a :doc:`feature toggle <feature-toggles>`.
So, you need to create an admin user, sign in, and then use
`the Django admin site`_ to enable the wiki so you can create pages.

#. As the admin user you just created, visit the `waffle section`_ of the admin
   site.

#. Click "`Add flag`_".

#. Enter "kumaediting" for the Name.

#. Set "Everyone" to "Yes"

#. Click "Save".

.. _the Django admin site: https://developer-local.allizom.org/admin/
.. _waffle section: https://developer-local.allizom.org/admin/waffle/
.. _Add flag: https://developer-local.allizom.org/admin/waffle/flag/add/

You can now visit `https://developer-local.allizom.org/docs/new
<https://developer-local.allizom.org/docs/new>`_ to create new wiki pages as
needed.

Many core MDN contributors create a personal ``User:<username>`` page as a
testing sandbox.

.. _enable KumaScript:

(Advanced) Enable KumaScript
============================

By default, `KumaScript`_ is also disabled with a :doc:`feature toggle <feature-toggles>`.
To enable KumaScript:

#. Sign in as the admin user.
#. Visit the `constance config admin panel`_.
#. Change ``KUMASCRIPT_TIMEOUT`` to 600.
#. Click "Save" at the bottom.
#. Import the `KumaScript auto-loaded modules`_::

    vagrant ssh
    python manage.py import_kumascript_modules

.. note:: You must `create a user`_ to import kumascript modules.

.. _KumaScript: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Tools/KumaScript
.. _constance config admin panel: https://developer-local.allizom.org/admin/constance/config/
.. _KumaScript auto-loaded modules: https://developer.mozilla.org/en-US/docs/MDN/Kuma/Introduction_to_KumaScript#Auto-loaded_modules

.. _GitHub Auth:

(Advanced) Enable GitHub Auth
=============================

To enable GitHub authentication,
`register your own OAuth application on GitHub`_:

* Application name: MDN (<username>).
* Homepage url: https://developer-local.allizom.org/docs/MDN/Contribute/Howto/Create_an_MDN_account.
* Application description: My own GitHub app for MDN!
* Authorization callback URL: https://developer-local.allizom.org/users/github/login/callback/.

As the admin user, `add a django-allauth social app`_ for GitHub:

* Provider: GitHub.
* Name: developer-local.allizom.org.
* Client id: <your GitHub App Client ID>.
* Secret key: <your GitHub App Client Secret>.
* Sites: example.com -> Chosen sites.

Now you can sign in with GitHub at https://developer-local.allizom.org/

.. _add a django-allauth social app: https://developer-local.allizom.org/admin/socialaccount/socialapp/add/
.. _register your own OAuth application on GitHub: https://github.com/settings/applications/new


.. _Errors:

Errors during Installation
==========================

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

Django database migrations
--------------------------

If you see errors that have "Django database migrations" in their
title try to manually run them in the VM to see more about them.
To do so::

    vagrant ssh
    python manage.py migrate

If you get an error, please ask for :ref:`more help <more-help>`.

Ubuntu
------

On Ubuntu, ``vagrant up`` might fail after being unable to mount NFS shared
folders. First, make sure you have the nfs-common and nfs-server packages
installed and also note that you can't export anything via NFS inside an
encrypted volume or home dir. On Windows NFS won't be used ever by the way.

If ``vagrant up`` works but you get the error ``IOError: [Errno 37] No locks
available``, that indicates that the host machine isn't running rpc.statd or
statd. This has been seen to affect Ubuntu >= 15.04 (running systemd). To enable
it, run the following commands::

       vagrant halt
       sudo systemctl start rpc-statd.service
       sudo systemctl enable rpc-statd.service
       vagrant up

If that doesn't help you can disable NFS by setting the ``VAGRANT_NFS``
configuration value in a ``.env`` file. See the :ref:`Vagrant configuration
<vagrant-config>` options for more info.

If you have other problems during ``vagrant up``, please check
:doc:`Troubleshooting <troubleshooting>`.
