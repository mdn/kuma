.. _Troubleshooting:

Troubleshooting
===============
Kuma has many components. Even core developers need reminders of how to keep
them all working together. This doc outlines some problems and potential
solutions running Kuma.

Fixing Docker issues
********************
The Docker development environment is evolving rapidly. You may need to reset
your containers with each change. As we gain experience with Docker, we'll
have more and targeted advice for issues with this development environment.

Kuma "Reset"
------------
These commands will reset your environment to a "fresh" version, while
retaining the database::

  cd /path/to/kuma
  docker-compose down
  make clean
  git submodule sync --recursive && git submodule update --init --recursive
  docker-compose pull
  docker-compose build --pull
  docker-compose up


Reset a corrupt database
------------------------
The Kuma database can become corrupted if the system runs out of disk space,
or is unexpectedly shutdown. MySQL can repair some issues, but sometimes you
have to start from scratch. When this happens, pass an extra argument
``--volumes`` to ``down``::

  cd /path/to/kuma
  docker-compose down --volumes
  make clean
  git submodule sync --recursive && git submodule update --init --recursive
  docker-compose pull
  docker-compose build --pull
  docker-compose up -d mysql
  sleep 20  # Wait for MySQL to initialize. See notes below
  docker-compose up

The ``--volumes`` flag will remove the named MySQL database volume, which will
be recreated when you run ``docker-compose up``.

The ``mysql`` container will take longer to start up as it recreates an empty
database, and the ``kuma`` container will fail until the ``mysql`` container
is ready for connections. The 20 second ``sleep`` should be sufficient, but
if it is not, you may need to cancel and run ``docker-compose up`` again.

Once ``mysql`` is ready for connections, follow the
:doc:`installation instructions <installation>`, starting at
:ref:`Provisioning a database <provision-the-database>`,
to configure your now empty database.

Run alternate services
----------------------
Docker services run as containers. To change the commands or environments of
services, it is easiest to add an override configuration file, as documented in
:ref:`advanced_config_docker`.

Linux file permissions
----------------------
On Linux, it is common that files created inside a Docker container are owned
by the root user on the host system. This can cause problems when trying to
work with them after creation. We are investigating solutions to create files
as the developer's user.

In some cases, you can specify the host user ID when running commands::

    docker-compose run --rm --user $(id -u) web ./manage.py collectstatic

In other cases, the command requires root permissions inside the container, and
this trick can't be used.

Another option is to allow the files to be created as root, and then change
them to your user on the host system::

    find . -user root -exec sudo chown $(id -u):$(id -g) \{\} \;

Fixing Vagrant issues
*********************

Kuma "Reset"
------------
These commands will attempt to fix the most common problems in a Vagrant
development environment::

  cd /path/to/kuma
  vagrant halt
  make clean
  git submodule sync --recursive && git submodule update --init --recursive
  vagrant up && vagrant provision

.. _Running individual processes:

Running individual processes
----------------------------
It is usually easier to see and debug problems if you run MDN processes
individually, instead of running them via ``foreman``. You can run each process
exactly as it is listed in ``Procfile``

-  ``web`` - runs the Django development server.
-  ``worker`` - runs the celery worker process for tasks.
-  ``camera`` - stores a snapshot of celery tasks to display in admin site.
-  ``kumascript`` - runs the node.js process for KumaScript macros.
-  ``sass`` - runs a process to compile all ``.scss`` changes into ``.css``.

An alternative is to run most processes via ``foreman``, and override one or
more with a custom command. Open two sessions with ``vagrant ssh``. In the
first session, run all but the target process (such as ``web``)::

    foreman run all=1,web=0

Then you can run your own alternate for ``web``, or the default, in the second
session::

    gunicorn kuma.wsgi -w 2 -b 0.0.0.0:8000
    ./manange.py runserver_plus 0.0.0.0:8000
    ./manange.py runserver_plus --print-sql 0.0.0.0:8000
    ./manange.py runserver_plus --threaded 0.0.0.0:8000

Errors after switching branches
-------------------------------

-  You should occasionally re-run the VM setup, especially after updating
   code with major changes. This will ensure that the VM environment stays
   up to date with configuration changes and installation of additional
   services.

   On the Host run::

       vagrant provision

-  If you see ``ImportError:`` errors, you may need to update your git
   submodules and/or clean out your ``*.pyc`` files to make sure python has all
   the latest files it needs::

       git submodule update --init
       make clean

-  If you see ``DatabaseError: (1146, "Table '...' doesn't exist")`` errors,
   you probably need to run database migrations::

       python manage.py migrate

   .. Note:

      If you are using a VM, this is done when you re-run the Vagrant
      provisioning.


Errors with KumaScript
----------------------
KumaScript is a very intensive process. If you are only working on python code
or front-end code that doesn't affect live site content, you can usually avoid
running it. (See `Running individual processes`_).

-  If you see lots of KumaScript timeout errors and you're running a VM, try
   increasing the memory allocated to the VM.

   Update the ``.env`` file in the ``/home/vagrant/src`` folder::

       MEMORY_SIZE=4096

-  If you see ``Kumascript service failed unexpectedly: HTTPConnectionPool``,
   make sure you enabled :ref:`KumaScript <enable KumaScript>`.

-  If changes to stylesheets do not have any effect, try compiling the Sass
   manually by running this command in the VM::

       compile-stylesheets

.. _more-help:

Getting more help
*****************

If you have more problems running Kuma, please:

#. Paste errors to `pastebin`_.
#. Email the `dev-mdn`_ list.
#. After you email dev-mdn, you can also ask in `IRC`_.

.. _pastebin: https://pastebin.mozilla.org/
.. _dev-mdn: https://lists.mozilla.org/listinfo/dev-mdn
.. _IRC: irc://irc.mozilla.org:6697/#mdndev
