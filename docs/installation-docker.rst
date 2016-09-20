=======================
Installation via Docker
=======================

Kuma has experimental support for `Docker`_ as an alternative to the
Vagrant set up.

.. _Docker: https://www.docker.com/

**Current Status**:

* These instructions work. Or worked at least once.
* Some ``kuma_base`` images are published to `quay.io`_.  They are tagged with
  the short commit hash of the kuma repository at check-in.  For example, the
  image tagged "609f6e5" is based on kuma at `commit 609f6e5`_. Automatic
  creation of images is a work in progress.
* The Docker development environment may not include parts needed for all
  development tasks. For example, ``kuma_base:609f6e5`` does not have the
  requirements to run tests, and does not include ElasticSearch.
* Most instructions are still written for Vagrant. Some Vagrant-specific
  instructions may work when run against Docker, others will fail.
* The Docker development environment is evolving rapidly. You should expect to
  have to remove and rebuild your containers with each change. Vagrant is the
  stable development environment.

.. _`quay.io`: https://quay.io/repository/mozmar/kuma_base?tab=tags
.. _`commit 609f6e5`: https://github.com/mozilla/kuma/commits/609f6e5 .

Docker setup
============

#. Install the `Docker platform`_, following Docker's instructions for your
   operating system.

   .. _Docker platform: https://www.docker.com/products/overview

#. Clone the kuma Git repository, if you haven't already::

        git clone git@github.com:mozilla/kuma.git

#. Ensure you are in the existing or newly cloned kuma working copy::

        cd kuma

#. Pull the Docker images and build the containers::

        docker-compose pull
        docker-compose build

#. Start the containers in the background::

        docker-compose up -d

Provision the database
======================
There are two options for provisioning the database.  One option is to
initialize a new, empty database, and another is to restore an existing
database from a data dump.

Initialize a new database
-------------------------
To initialize a fresh database, run the migrations::

    docker exec -it kuma_web_1 ./manage.py migrate

It will run the standard Django migrations, with output similar to::

    Operations to perform:
      Synchronize unmigrated apps: allauth, humans, dashboards, statici18n, captcha, django_mysql, django_extensions, rest_framework, cacheback, dbgettext, django_jinja, flat, persona, staticfiles, landing, puente, sitemaps, github, pipeline, soapbox, messages, honeypot, constance
      Apply all migrations: wiki, core, account, tidings, attachments, database, admin, sessions, djcelery, search, auth, feeder, sites, contenttypes, taggit, users, waffle, authkeys, socialaccount
    Synchronizing apps without migrations:
      Creating tables...
    ...
      Applying wiki.0030_add_page_creators_group... OK
      Applying wiki.0031_add_data_to_revisionip... OK

The database will be populated with empty tables.

Restore an existing database
----------------------------
To restore a gzipped-database dump ``kuma.sql.gz``::

    docker exec -i kuma_web_1 bash -c "zcat | ./manage.py dbshell" < kuma.sql.gz

There will be no output until the database is loaded, which may take several
minutes depending on the size of the data dump.

This command can be adjusted to restore from an uncompressed database, or
directly from a ``mysqldump`` command.

Compile locales
---------------
Localized string databases are included in their source form, and need to be
compiled to their binary form::

    docker exec -i kuma_web_1 make localecompile

Dozens of lines of warnings will be printed::

    cd locale; ./compile-mo.sh . ; cd --
    ./af/LC_MESSAGES/django.po:2: warning: header field 'PO-Revision-Date' still has the initial default value
    ./af/LC_MESSAGES/django.po:2: warning: header field 'Last-Translator' still has the initial default value
    ...
    ./zu/LC_MESSAGES/promote-mdn.po:4: warning: header field 'PO-Revision-Date' still has the initial default value
    ./zu/LC_MESSAGES/promote-mdn.po:4: warning: header field 'Last-Translator' still has the initial default value

Warnings are OK, and will be fixed as translators update the strings on
Pontoon_.  If there is an error, the output will end with the error, such as::

    ./az/LC_MESSAGES/django.po:263: 'msgid' and 'msgstr' entries do not both end with '\n'
    msgfmt: found 1 fatal error

These need to be fixed by a Kuma developer. Notify then in the #mdndev IRC
channel or open a bug. You can continue with installation, but non-English
locales will not be localized.

.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/

Generate static assets
----------------------
Static assets such as CSS and JS are included in source form, and need to be
compiled to their final form::

    docker exec -i kuma_web_1 make build-static

A few thousand lines will be printed, like::

    ## Compiling Stylus files to CSS ##
    compiled build/assets/css/dashboards.css
    generated build/assets/css/dashboards.css.map
    ...
    Post-processed 'css/zones.css' as 'css/zones.718d56a0cdc0.css'
    Post-processed 'css/zones.css.map' as 'css/zones.css.6be0969a4847.map'

    1717 static files copied to '/app/static', 1799 post-processed.

Visit the Homepage
==================
Open the homepage at http://localhost:8000 . You've installed Kuma!

Create an admin user
====================
Many Kuma settings require access to the Django admin, including
configuring social login.  It is useful to create an admin account with
password access for local development.

If you want to create a new admin account, use ``createsuperuser``::

    docker exec -it kuma_web_1 ./manage.py createsuperuser

This will prompt you for a username, email address (a fake address like
``admin@example.com`` will work), and a password.

If your database has an existing account that you want to use, use the Django
shell, similar to this::

    docker exec -it kuma_web_1 ./manage.py shell_plus
    >>> me = User.objects.get(username='admin_username')
    >>> me.set_password('mypassword')
    >>> me.is_superuser = True
    >>> me.is_staff = True
    >>> me.save()
    >>> exit()

With a password-enabled admin account, you can log into Django admin at
http://localhost:8000/admin/login/

.. _Disable your admin password:

When social accounts are enabled, the password can be disabled with the Django
shell::

    docker exec -it kuma_web_1 ./manage.py shell_plus
    >>> me = User.objects.get(username='admin_username')
    >>> me.set_unusable_password()
    >>> me.save()
    >>> exit()

Enable the wiki
===============
By default, the wiki is disabled with a
:doc:`feature toggle <feature-toggles>`.  To enable editing:

#. Log in as an admin user.
#. Open the `Waffle / Flags`_ section of the admin site.
#. Click "`ADD FLAG`_", above the Filter sidebar.
#. Enter "kumaediting" for the Name.
#. Set "Everyone" to "Yes".
#. Click "SAVE" at the bottom of the page.

If you are using a populated database, the "kumaediting" flag may already
exist.

You can now visit http://localhost:8000/docs/new to create new wiki pages.

Many contributors use a a personal page as a testing sandbox, with a title
such as "User:myusername".

.. _Waffle / Flags: http://localhost:8000/admin/waffle/flag/
.. _ADD FLAG: http://localhost:8000/admin/waffle/flag/add/

Enable KumaScript
=================
By default, `KumaScript`_ is disabled by the default timeout of `0.0` seconds.
To enable KumaScript:

#. Log in as the admin user.
#. Open the `Constance / Config`_ section of the admin site.
#. Change ``KUMASCRIPT_TIMEOUT`` to 600.
#. Click "SAVE" at the bottom of the page.
#. Import the `KumaScript auto-loaded modules`_:

::

   docker exec -it kuma_web_1 ./manage.py import_kumascript_modules

.. _KumaScript: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Tools/KumaScript
.. _Constance / Config: http://localhost:8000/admin/constance/config/
.. _KumaScript auto-loaded modules: https://developer.mozilla.org/en-US/docs/MDN/Kuma/Introduction_to_KumaScript#Auto-loaded_modules


Enable GitHub Auth
==================
To enable GitHub authentication, you'll need to
`register an OAuth application on GitHub`_, with settings like:

* Application name: MDN Development for (<username>)
* Homepage URL: http://localhost:8000/
* Application description: My own GitHub app for MDN!
* Authorization callback URL: http://localhost:8000/users/github/login/callback/

As an admin user, `add a django-allauth social app`_ for GitHub:

* Provider: GitHub
* Name: MDN Development
* Client id: <*your GitHub App Client ID*>
* Secret key: <*your GitHub App Client Secret*>
* Sites: Move ``example.com`` from "Available sites" to "Chosen sites"

Now you can sign in with GitHub.

To associate your password-only admin account with GitHub:

#. Login with your password at http://localhost:8000/admin/login/
#. Go to Account Connections at http://localhost:8000/en-US/users/account/connections
#. Click "Connect with GitHub"
#. (*Optional*) `Disable your admin password`_.

To create a new account with GitHub, use the regular "Sign in" widget at the
top of any page.

.. _register an OAuth application on GitHub: https://github.com/settings/applications/new
.. _add a django-allauth social app: http://localhost:8000/admin/socialaccount/socialapp/add/

Interact with the Docker containers
===================================
The current directory is mounted as the ``/app`` folder in the web and worker
containers (``kuma_web_1`` and ``kuma_worker_1``).  Changes made to your local
directory are usually reflected in the running containers. To force the issue,
the container can be restarted::

    docker restart kuma_web_1 kuma_worker_1

You can connect to a running container to run commands. For example, you can
open an interactive shell in the web container::

    docker exec -it kuma_web_1 /bin/bash

To view the logs generated by a container::

    docker logs kuma_web_1

To continuously view logs from all containers::

    docker-compose logs -f

To stop the containers::

    docker-compose stop

For further information, see the Docker documentation, such as the
`Docker Overview`_ and the documentation for your operating system.
You can try Docker's guided tutorials, and apply what you've learned on the
Kuma Docker environment.

.. _`Docker Overview`: https://docs.docker.com/engine/understanding-docker/
