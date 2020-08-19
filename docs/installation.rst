============
Installation
============
Kuma uses `Docker`_ for local development and integration testing, and we are
transitioning to Docker containers for deployment as well.

.. _Docker: https://www.docker.com/

**Current Status of Dockerization**:

* Kuma developers are using Docker for daily development and maintenance tasks.
  Staff developers primarily use `Docker for Mac`_. Other staff
  members and contributors use `Docker's Ubuntu packages`_.
* The development environment can use a lot of resources. On Docker for Mac,
  the environment runs well with 6 CPUs and 10 GB of memory dedicated to
  Docker. It can be run successfully on 2 CPUs and 2 GB of memory.
* The Docker development environment is evolving rapidly, to address issues
  found during development and to move toward a containerized design. You may
  need to regularly reset your environment to get the current changes.
* The Docker development environment doesn't fully support a 'production-like'
  environment. For example, we don't have a documented configuration for
  running with an SSL connection.
* When the master branch is updated, the ``kuma_base`` image is refreshed and
  published to `DockerHub`_. This image contains system packages and
  third-party libraries.
* Our TravisCI_ builds include a target that build Docker containers and runs
  the tests inside.
* Our Jenkins_ server builds and publishes Docker images, and runs integration
  tests using Docker.
* We are documenting tips and tricks on the
  :doc:`Troubleshooting page <troubleshooting>`.
* Feel free to ask for help on Matrix at ``#mdn`` or on `discourse`_.

.. _`Docker for Mac`: https://docs.docker.com/docker-for-mac/
.. _`Docker's Ubuntu packages`: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _`DockerHub`: https://hub.docker.com/r/mdnwebdocs/kuma_base/tags/
.. _TravisCI: https://travis-ci.com/mdn/kuma/
.. _Jenkins: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/activity
.. _discourse: https://discourse.mozilla.org/c/mdn

Docker setup
============

#. Install the `Docker platform`_, following Docker's instructions for your
   operating system, such as `Docker for Mac`_ for MacOS, or for your
   `Linux distribution`_.

   Non-Linux users should increase Docker's memory limits (`Windows`_,
   `macOS`_) to at least 4 GB, as the default of 2 GB is insufficient.

   Linux users will also want to install `Docker Compose`_ and follow
   `post-install instructions`_ to confirm that the development user can run
   Docker commmands.

   To confirm that Docker is installed correctly, run::

        docker run hello-world

   If you find any error using docker commands without ``sudo`` visit using
   `docker as non-root`_ user.

#. Clone the kuma Git repository, if you haven't already::

        git clone --recursive https://github.com/mdn/kuma.git

   If you think you might be submitting pull requests, consider
   forking the repository first, and then cloning your fork of it.

#. Ensure you are in the existing or newly cloned kuma working copy::

        cd kuma

#. Initialize and customize ``.env``::

        cp .env-dist.dev .env
        vim .env  # Or your favorite editor

   Linux users should set the ``UID`` parameter in ``.env``
   (i.e. change ``#UID=1000`` to ``UID=1000``) to avoid file
   permission issues when mixing ``docker-compose`` and ``docker``
   commands. MacOS users do not need to change any of the defaults to
   get started. Note that there are settings in this file that can be
   useful when debugging, however.

#. Pull the Docker images and build the containers::

        docker-compose pull
        docker-compose build

   (The ``build`` command is effectively a no-op at this point because
   the ``pull`` command just downloaded pre-built docker images.)

#. Start the containers in the background::

        docker-compose up -d

.. _Docker platform: https://www.docker.com/products/overview
.. _Linux distribution: https://docs.docker.com/engine/installation/linux/
.. _Docker Compose: https://docs.docker.com/compose/install/
.. _post-install instructions: https://docs.docker.com/engine/installation/linux/linux-postinstall/
.. _docker as non-root: https://docs.docker.com/engine/installation/linux/linux-postinstall/
.. _Windows: https://docs.docker.com/docker-for-windows/#advanced
.. _macOS: https://docs.docker.com/docker-for-mac/#advanced

.. _provision-the-database:

Load the sample database
========================

Download the sample database with either of the following ``wget`` or
``curl`` (installed by default on macOS) commands::

    wget -N https://mdn-downloads.s3-us-west-2.amazonaws.com/mdn_sample_db.sql.gz
    curl -O https://mdn-downloads.s3-us-west-2.amazonaws.com/mdn_sample_db.sql.gz

Next, upload that sample database into the Kuma web container with::

    docker-compose exec web bash -c "zcat mdn_sample_db.sql.gz | ./manage.py dbshell"

(This command can be adjusted to restore from an uncompressed database, or
directly from a ``mysqldump`` command.)

Then run the following command::

    docker-compose exec web ./manage.py migrate

This will ensure the sample database is in sync with your version of Kuma.

Compile locales
===============
Localized string databases are included in their source form, and need to be
compiled to their binary form::

    docker-compose exec web make localecompile

Dozens of lines of warnings will be printed::

    cd locale; ./compile-mo.sh .
    ./af/LC_MESSAGES/django.po:2: warning: header field 'PO-Revision-Date' still has the initial default value
    ./af/LC_MESSAGES/django.po:2: warning: header field 'Last-Translator' still has the initial default value
    ...
    ./zu/LC_MESSAGES/javascript.po:2: warning: header field 'PO-Revision-Date' still has the initial default value
    ./zu/LC_MESSAGES/javascript.po:2: warning: header field 'Last-Translator' still has the initial default value

Warnings are OK, and will be fixed as translators update the strings on
Pontoon_. If there is an error, the output will end with the error, such as::

    ./az/LC_MESSAGES/django.po:263: 'msgid' and 'msgstr' entries do not both end with '\n'
    msgfmt: found 1 fatal error

These need to be fixed by a Kuma developer. Notify them in the #mdn Matrix
room or open a bug. You can continue with installation, but non-English
locales will not be localized.

.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/

Generate static assets
======================
Static assets such as CSS and JS are included in source form, and need to be
compiled to their final form::

    docker-compose exec web make build-static

A few thousand lines will be printed, like::

    ## Generating JavaScript translation catalogs ##
    processing language en_US
    processing language af
    processing language ar
    ...
    ## Compiling (Sass), collecting, and building static files ##
    Copying '/app/kuma/static/img/embed/promos/survey.svg'
    Copying '/app/kuma/static/styles/components/home/column-callout.scss'
    Copying '/app/build/locale/jsi18n/fy-NL/javascript.js'
    ...
    Post-processed 'build/styles/editor-locale-ar.css' as 'build/styles/editor-locale-ar.css'
    Post-processed 'build/styles/locale-ln.css' as 'build/styles/locale-ln.css'
    Post-processed 'build/styles/editor-locale-pt-BR.css' as 'build/styles/editor-locale-pt-BR.css'
    ....
    1870 static files copied to '/app/static', 125 post-processed.

Visit the homepage
==================
Open the homepage at http://localhost.org:8000 . You've installed Kuma!

Create an admin user
====================
Many Kuma settings require access to the Django admin, including
configuring social login.  It is useful to create an admin account with
password access for local development.

If you want to create a new admin account, use ``createsuperuser``::

    docker-compose exec web ./manage.py createsuperuser

This will prompt you for a username, email address (a fake address like
``admin@example.com`` will work), and a password.

If your database has an existing account that you want to use, run the
management command. Replace ``YOUR_USERNAME`` with your username and
``YOUR_PASSWORD`` with your password::

    docker-compose run --rm web ./manage.py ihavepower YOUR_USERNAME \
    --password YOUR_PASSWORD

With a password-enabled admin account, you can log into Django admin at
http://localhost.org:8000/admin/login

.. _enable-github-auth:

Update the Sites section
=======================================
#. After logging in to the Django admin (an alternative is using the login ``test-super``
   with password ``test-password``), scroll down to the Sites section.

#. Click on "Change".

#. Click on the entry that says ``localhost:8000``.

#. Change both the domain and display name from ``localhost:8000`` to ``localhost.org:8000``.

#. Click "Save".



Enable GitHub/Google authentication (optional)
==============================================
Since Google's OAuth requires us to use a valid top-level-domain, we're going to use
http://localhost.org:8000 as an example for every URL here.

To automate setting Django up for social auth you can run
``docker-compose exec web ./manage.py configure_social_auth`` and follow its steps (and
ignore the rest of this section).

If you want to do it manually, follow these steps:

To enable GitHub authentication, you'll need to
`register an OAuth application on GitHub`_, with settings like:

* Application name: MDN Development for (<username>).
* Homepage URL: http://localhost.org:8000/.
* Application description: My own GitHub app for MDN!
* Authorization callback URL: http://localhost.org:8000/users/github/login/callback/.

To enable Google authentication, you'll need to first `create an API project on Google`_.
After that we'll need to `configure credentials for that project`_ with settings like:

* Name: MDN Development for (<username>).
* Authorized JavaScript origins: http://localhost.org:8000
* Authorized redirect URIs: http://localhost.org:8000/users/google/login/callback/

As an admin user, `add a django-allauth social app`_ for both GitHub and Google do the
following:

* Provider: GitHub/Google.
* Name: MDN Development.
* Client id: <*your Client ID*>.
* Secret key: <*your Client Secret*>.
* Sites: Move ``locahost:8000`` from "Available sites" to "Chosen sites".

``locahost:8000`` needs to either have ID 1 or ``SITE_ID=1`` has to be set in ``.env``
to its actual ID. You'll also need to set ``DOMAIN=localhost.org`` (no port!) there.

Your hosts file should contain the following lines::

    127.0.0.1       localhost demos localhost.org wiki.localhost.org
    255.255.255.255 broadcasthost
    ::1             localhost demos localhost.org wiki.localhost.org

Now you can sign in with GitHub.

To associate your password-only admin account with GitHub:

#. Login with your password at http://localhost.org:8000/admin/login.
#. Go to the Homepage at https://developer.mozilla.org/en-US/.
#. Click your username at the top to view your profile.
#. Click Edit to edit your profile.
#. Under My Profiles, click `Use your GitHub account to sign in`_.

To create a new account with GitHub, use the regular "Sign in" widget at the
top of any page.

With social accounts are enabled, you can disable the admin password in the
Django shell::

    docker-compose exec web ./manage.py shell_plus
    >>> me = User.objects.get(username='admin_username')
    >>> me.set_unusable_password()
    >>> me.save()
    >>> exit()

.. _register an OAuth application on GitHub: https://github.com/settings/applications/new
.. _create an API project on Google: https://console.developers.google.com/projectcreate
.. _configure credentials for that project: https://console.developers.google.com/apis/credentials
.. _add a django-allauth social app: http://localhost.org:8000/admin/socialaccount/socialapp/add/
.. _`Use your GitHub account to sign in`: https://developer.mozilla.org/users/github/login/?process=connect


Enable Stripe payments (optional)
=================================
#. Go to https://dashboard.stripe.com and create a Stripe account (if you don't have one already).
#. Go to https://dashboard.stripe.com/apikeys and copy both the publishable and secret key
   into your ``.env`` file. The respective config keys are ``STRIPE_PUBLIC_KEY`` and
   ``STRIPE_SECRET_KEY``.
#. Go to https://dashboard.stripe.com/test/subscriptions/products and create a new product and plan.
#. Once created copy the plan ID and also put it into ``.env`` as ``STRIPE_PLAN_ID``. Unless you
   set a custom ID it should start with ``plan_``.

If you're using Stripe in testing mode you can also get test numbers from this site:
https://stripe.com/docs/testing#cards

Testing Stripe's hooks locally requires setting up a tunneling service, like ngrok (https://ngrok.com).
You should then set ``CUSTOM_WEBHOOK_HOSTNAME`` to the hostname you get from your tunneling service, e.g. for
ngrok it might be https://203ebfab.ngrok.io
After kuma has started you will have a webhook configured in stripe. You can view it on Stripe's dashboard:
https://dashboard.stripe.com/test/webhooks
Note that with the free tier a restart of ngrok gives you a new hostname, so you'll have to change the config
again and restart the server (or manually change the webhook in Stripe's dashboard).

Enable Sendinblue email integration
===================================
#. Create a Sendinblue account over at https://www.sendinblue.com (you can skip a lot of the profile set-up,
   look for skip in the upper right).
#. Get your v3 API key at https://account.sendinblue.com/advanced/api
#. Create a list at https://my.sendinblue.com/lists/new/parent_id/1
#. Add the sendinblue config keys to your .env, the keynames are ``SENDINBLUE_API_KEY`` and ``SENDINBLUE_LIST_ID``

Interact with the Docker containers
===================================
The current directory is mounted as the ``/app`` folder in the web and worker
containers. Changes made to your local
directory are usually reflected in the running containers. To force the issue,
the containers for specified services can be restarted::

    docker-compose restart web worker

You can connect to a running container to run commands. For example, you can
open an interactive shell in the web container::

    docker-compose exec web /bin/bash
    make bash  # Same command, less typing

To view the logs generated by a container::

    docker-compose logs web

To continuously view logs from all containers::

    docker-compose logs -f

To stop the containers::

    docker-compose stop

If you have made changes to the ``.env`` or ``/etc/hosts`` file, it's a good idea to run::

    docker-compose stop
    docker-compose up


For further information, see the Docker documentation, such as the
`Docker Overview`_ and the documentation for your operating system.
You can try Docker's guided tutorials, and apply what you've learned on the
Kuma Docker environment.

.. _`Docker Overview`: https://docs.docker.com/engine/understanding-docker/
