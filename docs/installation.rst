=======================
Installation via Docker
=======================
Starting in 2016, we support using `Docker`_ for local development, and we are
transitioning to Docker for integration testing and deployment as well.

.. _Docker: https://www.docker.com/

**Current Status**:

* Kuma developers are using Docker for daily development and maintenance tasks.
  Staff developers primarily use `Docker for Mac`_. Other staff
  members and contributors use `Docker's Ubuntu packages`_.
* When the master branch is updated, the ``kuma_base`` image is refreshed and
  published to `quay.io`_. This image contains system packages and
  third-party libraries.
* The Docker development environment is evolving rapidly, to address issues
  found during development and to move toward a containerized design. You may
  need to regularly reset your environment to get the current changes.
* The Docker environment doesn't yet support everything from the Vagrant
  environment, such as local SSL development and automatic asset compiling.
* We are documenting tips and tricks on the
  :doc:`Troubleshooting page <troubleshooting>`.

.. _`Docker for Mac`: https://docs.docker.com/docker-for-mac/
.. _`Docker's Ubuntu packages`: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _`quay.io`: https://quay.io/repository/mozmar/kuma_base?tab=tags

Docker setup
============

#. Install the `Docker platform`_, following Docker's instructions for your
   operating system (`Docker for Mac`_ for MacOS,
   `Docker's Ubuntu packages`_ etc.).

   .. _Docker platform: https://www.docker.com/products/overview

#. Clone the kuma Git repository, if you haven't already::

        git clone --recursive git@github.com:mozilla/kuma.git

#. Ensure you are in the existing or newly cloned kuma working copy::

        cd kuma

#. Copy ``.env-dist.dev`` to ``.env``. Linux users should to set the ``UID``
   parameter in ``.env``, to avoid issues when mixing ``docker-compose`` and
   ``docker`` commands.

#. Pull the Docker images and build the containers::

        docker-compose pull
        docker-compose build

#. Start the containers in the background::

        docker-compose up -d

The following instructions assume that you are running from a folder named
``kuma``, so that the containers created are named ``kuma_web_1``,
``kuma_worker_1``, etc.  If you run from another folder, like ``mdn``, the
containers will be named ``mdn_web_1``, ``mdn_worker_1``, etc. Adjust the
command accordingly, or force the ``kuma`` name with::

        docker-compose up -d -p kuma

.. _provision-the-database:

Provision the database
======================
There are two options for provisioning the database. One option is to
initialize a new, empty database, and another is to restore an existing
database from a data dump.

Initialize a new database
-------------------------
To initialize a fresh database, run the migrations::

    docker exec -it kuma_web_1 ./manage.py migrate

It will run the standard Django migrations, with output similar to::

    Operations to perform:
      Synchronize unmigrated apps: allauth, humans, dashboards, statici18n, captcha, django_mysql, django_extensions, rest_framework, cacheback, dbgettext, django_jinja, flat, staticfiles, landing, puente, sitemaps, github, pipeline, soapbox, messages, honeypot, constance
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
===============
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
Pontoon_. If there is an error, the output will end with the error, such as::

    ./az/LC_MESSAGES/django.po:263: 'msgid' and 'msgstr' entries do not both end with '\n'
    msgfmt: found 1 fatal error

These need to be fixed by a Kuma developer. Notify them in the #mdndev IRC
channel or open a bug. You can continue with installation, but non-English
locales will not be localized.

.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/

Generate static assets
======================
Static assets such as CSS and JS are included in source form, and need to be
compiled to their final form::

    docker exec -i kuma_web_1 make build-static

A few thousand lines will be printed, like::

    ## Generating JavaScript translation catalogs ##
    processing language en_US
    processing language af
    processing language ar
    ...
    ## Compiling (Sass), collecting, and building static files ##
    Copying '/app/build/locale/jsi18n/af/javascript.js'
    Copying '/app/build/locale/jsi18n/ar/javascript.js'
    Copying '/app/build/locale/jsi18n/az/javascript.js'
    ...
    Post-processed 'build/styles/wiki.css' as 'build/styles/wiki.css'
    Post-processed 'build/styles/error-404.css' as 'build/styles/error-404.css'
    Post-processed 'build/styles/mdn.css' as 'build/styles/mdn.css'
    ....
    1687 static files copied to '/app/static', 1773 post-processed

.. _frontend-development:

Frontend Development
====================
When doing front-end development on your local machine, you'll probably
want to run (most likely in its own shell)::

     gulp

within the root directory of your local Kuma repository. It will watch for
changes to any source files under ``./kuma/static`` (e.g., Sass files)
and move any changed files to ``./static``, where they will be compiled
on-demand.

However, first you'll need to install `Node.js`_  and `gulp`_ on your local
machine. First install Node.js, and then to install gulp, run::

    npm install

from the root directory of your local Kuma repository.

.. _gulp: http://gulpjs.com/
.. _`Node.js`: https://nodejs.org/

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

If your database has an existing account that you want to use, run the
management command. Replace ``YOUR_USERNAME`` with your username and
``YOUR_PASSWORD`` with your password::

    docker-compose run --rm web ./manage.py ihavepower YOUR_USERNAME \
    --password YOUR_PASSWORD

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
:doc:`feature toggle <feature-toggles>`. To enable editing:

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

* Application name: MDN Development for (<username>).
* Homepage URL: http://localhost:8000/.
* Application description: My own GitHub app for MDN!
* Authorization callback URL: http://localhost:8000/users/github/login/callback/.

As an admin user, `add a django-allauth social app`_ for GitHub:

* Provider: GitHub.
* Name: MDN Development.
* Client id: <*your GitHub App Client ID*>.
* Secret key: <*your GitHub App Client Secret*>.
* Sites: Move ``example.com`` from "Available sites" to "Chosen sites".

Now you can sign in with GitHub.

To associate your password-only admin account with GitHub:

#. Login with your password at http://localhost:8000/admin/login/.
#. Go to the Homepage at https://developer.mozilla.org/en-US/.
#. Click your username at the top to view your profile.
#. Click Edit to edit your profile.
#. Under My Profiles, click `Use your GitHub account to sign in`_.
#. (*Optional*) `Disable your admin password`_.

To create a new account with GitHub, use the regular "Sign in" widget at the
top of any page.

.. _register an OAuth application on GitHub: https://github.com/settings/applications/new
.. _add a django-allauth social app: http://localhost:8000/admin/socialaccount/socialapp/add/
.. _`Use your GitHub account to sign in`: https://developer.mozilla.org/users/github/login/?process=connect

Interact with the Docker containers
===================================
The current directory is mounted as the ``/app`` folder in the web and worker
containers (``kuma_web_1`` and ``kuma_worker_1``). Changes made to your local
directory are usually reflected in the running containers. To force the issue,
the container can be restarted::

    docker restart kuma_web_1 kuma_worker_1

You can connect to a running container to run commands. For example, you can
open an interactive shell in the web container::

    docker exec -it kuma_web_1 /bin/bash
    make bash  # Same command, less typing

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
