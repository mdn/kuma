.. _Troubleshooting:

Troubleshooting
===============
Kuma has many components. Even core developers need reminders of how to keep
them all working together. This doc outlines some problems and potential
solutions running Kuma.

Kuma "Reset"
------------
These commands will reset your environment to a "fresh" version, with the
current third-party libraries, while retaining the database::

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

.. _more-help:

KumaScript macros are not evaluating
------------------------------------

If you're seeing tags like ``{{HTMLSidebar}}`` or ``{{HTMLElement("head")}}``
it could be happening because there is an outdated macro that needs to be
removed.

For example on ``/en-US/docs/Web/HTML``, there is a deleted macro called
``CommunityBox``. To fix this, log in to edit the page, remove the
``CommunityBox`` macro, then click "Publish".  Visit the affected page again
and you should see actual content instead of the macros.

Note: Sometimes the wiki site
(e.g. http://wiki.localhost.org:8000/en-US/docs/Web/HTML$edit) will throw
an error after editing the page, acting as if it didn't save your edit. View
the actual URL of the page (e.g. http://localhost.org:8000/en-US/docs/Web/HTML)
to verify that the changes were accepted.


Getting more help
-----------------
Check if there is anything helpful in the logs::

    docker-compose logs web kumascript
    docker-compose logs web

If you have more problems running Kuma, please:

#. Paste errors to `pastebin`_.
#. Start a thread on `Discourse`_.
#. After you email dev-mdn, you can also ask in the #mdn-dev Slack
   channel.

.. _pastebin: https://pastebin.mozilla.org/
.. _Discourse: https://discourse.mozilla.org/c/mdn
.. _IRC: irc://irc.mozilla.org:6697/#mdndev
