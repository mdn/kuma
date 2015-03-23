Kuma via Vagrant
================

Core developers run Kuma in a `Vagrant`_-managed virtual machine so we can run
the entire MDN stack. (Django, KumaScript, Search, Celery, etc.)
If you're on Mac OS X or Linux and looking for a quick way to get started, you
should try these instructions.

.. note:: **If you have problems getting vagrant up**, check Errors_ below.

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

#. Visit `https://mdn-local.mozillademos.org <https://mdn-local.mozillademos.org>`_ and add an exception for the security certificate if prompted

#. Visit the homepage at `https://developer-local.allizom.org <https://developer-local.allizom.org/>`_

#. You've installed Kuma! If you want `the badge`_ ...

.. image:: https://badges.mozilla.org/media/uploads/badge/2/3/23fef80968a03f3ba32321a7f31ae1e2_image_1372816280_0238.png

`email a screenshot of your browser to mdn-dev at mozilla dot com <mailto:mdn-dev@mozilla.com?subject=Local%20MDN%20Screenshot>`_.

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
You'll need to use :doc:`feature toggles <feature-toggles>` to enable some
basic features.

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

GitHub auth is also (temporarily) behind a waffle flag. So, `add a waffle
flag`_ called ``github_login`` and set "Everyone" to "Yes".

Now you can sign in with GitHub at https://developer-local.allizom.org

.. _Add a django-allauth social app: https://developer-local.allizom.org/admin/socialaccount/socialapp/add/
.. _Register your own OAuth application on GitHub: https://github.com/settings/applications/new


Wiki Editing
~~~~~~~~~~~~

The central feature of MDN is wiki editing. We use a waffle flag called
``kumaediting`` to control edits to the wiki. So we can effectively put the
site into "read-only" and/or "write-by-staff-only" modes.

To enable wiki editing on your MDN vm, `add a waffle flag`_ called
``kumaediting`` and set "Everyone" to "Yes".

.. _add a waffle flag: https://developer-local.allizom.org/admin/waffle/flag/add/

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
the same slugs. Or you can email the `dev-mdn`_ list to get a .json file to
load in your local django admin interface as described in `this comment`_.

.. _constance config admin panel: https://developer-local.allizom.org/admin/constance/config/
.. _KumaScript auto-loaded modules: https://developer.mozilla.org/en-US/docs/MDN/Kuma/Introduction_to_KumaScript#Auto-loaded_modules
.. _this comment: https://github.com/mozilla/kuma/issues/2518#issuecomment-53665362

Create pages
------------

You can visit `https://developer-local.allizom.org/docs/new
<https://developer-local.allizom.org/docs/new>`_ to create new wiki pages as
needed.

Many core MDN contributors create a personal ``User:<username>`` page as a testing sandbox.


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

``vagrant up`` starts the virtual machine. The first time you run ``vagrant up`` it
also `provisions <https://docs.vagrantup.com/v2/cli/provision.html>`_ the vm -
i.e., it automatically installs and configures Kuma software on the vm. We
provision the vm with `puppet`_ manifests in the `puppet/manifests directory
<https://github.com/mozilla/kuma/tree/master/puppet/manifests>`_.

Sometimes we put puppet declarations in the wrong order. Which means some
errors can be fixed by simply provisioning the vm again::

       vagrant provision

In some rare occasions you might need to run this multiple times. If you find an
error that is fixed by running ``vagrant provision`` again, please email us the
error at dev-mdn@lists.mozilla.org and we'll see if we can fix it.

If you see the same error over and over, please ask for :ref:`more help <more-help>`.

kuma_south_migrate
~~~~~~~~~~~~~~~~~~

If you see errors like::

    notice: /Stage[main]/Kuma_config/Exec[kuma_south_migrate]

try to manually run database migrations in the vm. To do so::

    vagrant ssh
    python manage.py migrate

If you get an error, please ask for :ref:`more help <more-help>`.

Ubuntu
~~~~~~

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

If you have other problems during ``vagrant up``, please check
:ref:`Troubleshooting`.
