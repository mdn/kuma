===========
Development
===========

Basic Docker usage
==================
Edit files as usual on your host machine; the current directory is mounted
via Docker host mounting at ``/app`` within various
Kuma containers. Useful docker sub-commands::

    docker-compose exec web bash     # Start an interactive shell
    docker-compose logs web          # View logs from the web container
    docker-compose logs -f           # Continuously view logs from all containers
    docker-compose restart web       # Force a container to reload
    docker-compose stop              # Shutdown the containers
    docker-compose up -d             # Start the containers
    docker-compose rm                # Destroy the containers

There are ``make`` shortcuts on the host for frequent commands, such as::

    make up         # docker-compose up -d
    make bash       # docker-compose exec web bash
    make shell_plus # docker-compose exec web ./manage.py shell_plus

Run all commands in this doc in the ``web`` service container after ``make bash``.

Running Kuma
============
When the Docker container environment is started (``make up`` or similar), all
of the services are also started. The development instance is available at
http://localhost:8000.

Running the tests
=================
One way to confirm that everything is working, or to pinpoint what is broken,
is to run the test suite.

Django tests
------------
Run the Django test suite::

    make test

For more information, see the :doc:`test documentation <tests>`.

Functional tests
----------------
To run the functional tests, see
:doc:`Client-side Testing <tests-functional>`.

Kumascript tests
----------------
If you're changing Kumascript, be sure to run its tests too.
See https://github.com/mdn/kumascript.

.. _front-end-development:

Front-end development
=====================
Assets are processed in several steps by Django and django-pipeline_:

* Front-end localization libraries and string catalogs are generated based on
  ``gettext`` calls in Javascript files.
* Sass_ source files are compiled to plain CSS with node-sass_.
* Assets are collected to the ``static/`` folder.
* CSS, JS, and image assets are included in templates using the
  ``{% stylesheet %}``, ``{% javascript %}``, and ``{% static %}`` Jinja2
  macros.

In production mode (``DEBUG=False``), there is additional processing. See
:ref:`generating-production-assets` for more information.

To rebuild the front-end localization libraries::

    make compilejsi18n

To rebuild CSS, JS, and image assets::

    make collectstatic

To do both::

    make build-static

.. _ManifestStaticFilesStorage: https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage
.. _Sass: https://sass-lang.com/
.. _UglifyJS: https://github.com/mishoo/UglifyJS2
.. _cleancss: https://github.com/jakubpawlowicz/clean-css-cli
.. _django-pipeline: https://github.com/jazzband/django-pipeline
.. _node-sass: https://github.com/sass/node-sass

Compiling JS on the host system with webpack
--------------------------------------------
For a quicker iteration cycle while developing the frontend app you can run::

    npm i
    npm run webpack:dev

This watches the react frontend and rebuilds both the web and SSR bundle
when changes occur. It rebuilds only what has changed and also restarts the
SSR server.
It serves React in development mode which yields more explicit warnings and
allows you to use tools such as the `React DevTools`_.

.. _`React DevTools`: https://reactjs.org/blog/2019/08/15/new-react-devtools.html#how-do-i-get-the-new-devtools

You can also run it in production mode::

   npm run webpack:prod

Style guide and linters
-----------------------
There is an evolving style guide at https://mdn.github.io/mdn-fiori/, sourced
from https://github.com/mdn/mdn-fiori. Some of the style guidelines are
enforced by linters.

To run stylelint_ on all ``.scss`` files::

    npm run stylelint

To run eslint_ on ``.js`` files::

    npm run eslint

.. _stylelint: https://stylelint.io/
.. _eslint: https://eslint.org/

Bundle Analyze
--------------
To get an idea about the size distribution of our react codebase you can run::

    npm run webpack:analyze

This will open an interactively explorable report in your browser.

Add a React page
----------------
Let's say we are adding a new Example page to the dashboards section on Kuma. We'd like the pathname to be ``/dashboards/example/``.

First we need to set up a few things in Django:

#. In ``kuma/dashboards/jinja2/dashboards/``, create a new Jinja template that our view will render called ``example.html``. Paste the following code in ``example.html`` to get started::

    {% extends "react_base.html" %}

    {% block title %}{{ page_title(_('Example Page')) }}{% endblock %}

    {% block content %}This works!{% endblock %}

    {# This overrides the Jinja footer, since we will be using the React footer instead. Without this line, two footers will render. #}
    {% block footer %}{% endblock %}

#. In ``kuma/dashboards/views.py``, render the Jinja template we just created::

    def example(request):
        return render(request, "dashboards/example.html")


#. In ``kuma/dashboards/urls.py``, add a new url that will render our view. This code will change slightly depending on your url and file structure::

    # Import the view

    # (This next line most likely will already be there, if not, add it to the top of the file.)
    from . import views

    ...

    re_path(r"^example/$", views.example, name="dashboards.example"),


#. We are done with the Django part! In your browser, go to http://wiki.localhost.org:8000/en-US/dashboards/example/ and you should see a page that says "This works!"

#. Now we can set up the React part. In ``kuma/dashboards/jinja2/dashboards/example.html``, we can remove the "This works!" text and add the following code between ``{% block title %}`` and ``{% block content %}``::

    {# Pass `True` for initial data if you do not have any data to fetch. Otherwise, change `True` to `None` or whatever your initial data will be. #}
    {% block document_head %}
        {{ render_react("SPA", request.LANGUAGE_CODE, request.get_full_path(), True)|safe }}
    {% endblock %}

#. So your ``kuma/dashboards/jinja2/dashboards/example.html`` file should now look something like this::

    {% extends "react_base.html" %}

    {% block title %}{{ page_title(_('Example Page')) }}{% endblock %}

    {# Pass `True` for initial data if you do not have any data to fetch (i.e. static page). #}
    {# Otherwise, change `True` to `None` or whatever your initial data will be. #}
    {% block document_head %}
        {{ render_react("SPA", request.LANGUAGE_CODE, request.get_full_path(), True)|safe }}
    {% endblock %}

    {% block content %}
    {% endblock %}

    {# This overrides the Jinja footer, since we will be using the React footer instead. Without this line, two footers will render. #}
    {% block footer %}{% endblock %}


#. In ``kuma/javascript/src``, if there is not a ``kuma/javascript/dashboards`` folder already, add a folder called ``dashboards``.

#. In ``kuma/javascript/src/dashboards``, create a file called ``example.jsx``. Add the following lines as a starter::

    // @flow
    import * as React from 'react';

    import { gettext } from '../l10n.js';
    import A11yNav from '../a11y/a11y-nav.jsx';
    import Header from '../header/header.jsx';
    import Footer from '../footer.jsx';
    import Route from '../route.js';

    type ExampleRouteParams = {
        locale: string
    };

    export default function ExamplePage() {
        return (
            <>
                <A11yNav />
                <Header />
                {gettext('Hello!')}
                <Footer />
            </>
        );
    }

    const BASEURL =
        typeof window !== 'undefined' && window.location
            ? window.location.origin
            : 'http://ssr.hack';

    export class ExampleRoute extends Route<ExampleRouteParams, null> {
        locale: string;

        constructor(locale: string) {
            super();
            this.locale = locale;
        }

        getComponent() {
            return ExamplePage;
        }

        match(url: string): ?ExampleRouteParams {
            const path = new URL(url, BASEURL).pathname;
            const examplePath = `/${this.locale}/dashboards/example/`;
            const regex = new RegExp(examplePath, 'g');

            if (regex.test(path)) {
                return {
                    locale: this.locale
                };
            }
            return null;
        }
    }

#. We need to tell the single-page-app component about our new Route component, ``ExampleRoute``. In ``kuma/javascript/src/single-page-app.jsx``, at the top, add::

    import { ExampleRoute } from './dashboards/example.jsx';

#. A few lines down in the same file, where you see ``const routes = [ ... ]``, add ``ExampleRoute``, so it should look like this::

    const routes = [
        ...
        new ExampleRoute(locale)
    ];

#. We are done! Go to ``/dashboards/example/`` in your browser and you should see a header, footer, and the words, "Hello!"

React page with initial data
############################
If we have initial data we'd like to pass to our React component, we can do so by updating the 4th argument (``document_data``) in the ``render_react`` function call. This data will then be available as a prop on the React side.
For a real-life example, search for ``document_data`` in ``kuma/wiki/views/document.py``.


#. Continuing our example from above, go back to ``kuma/dashboards/jinja2/dashboards/example.html``. In the call to ``render_react``, change ``True`` to your initial data. For our purposes, initial data will be ``{"content": "Goodbye!"}``. The full line should look like::

    {{ render_react("SPA", request.LANGUAGE_CODE, request.get_full_path(), {"content": "Goodbye!"})|safe }}

#. In ``kuma/javascript/src/dashboards/example.jsx``, import the ``RouteComponentProps`` type by making the change below::

    import Route from '../route.js';

    ↑ to ↴

    import Route, { type RouteComponentProps } from '../route.js';

#. In the same file, update the ``ExamplePage`` function to accept a ``data`` parameter. The function declaration should now look like this::

    export default function ExamplePage({ data }: RouteComponentProps) {
        ...
    }

#. Now we can access the initial data from Step 1. Change ``{gettext("Hello!)}`` to ``{gettext(data.content)}``. Refresh the page and the "Hello!" text should be replaced by "Goodbye!"


React page using ``fetch()``
############################
In some cases, you may choose to fetch data asynchronously when the page renders.

#. Continuing our example from above, go back to ``kuma/dashboards/jinja2/dashboards/example.html``. In the call to ``render_react``, change the 4th argument to ``None``. The full line should look like::

    {{ render_react("SPA", request.LANGUAGE_CODE, request.get_full_path(), None)|safe }}

#. Refresh the page in the browser and you should now get an error. That is because we do not have a ``fetch()`` method yet, so let's make one. In ``kuma/javascript/src/dashboards/example.jsx``, ``ExampleRoute`` class, add this method (note: we are using ``/api/v1/whoami`` just to show a working example of an API call. Change this to reflect your API endpoint.)::

    fetch(): Promise<any> {
        return fetch('/api/v1/whoami').then(response => response.json());

    }

#. Once the fetch completes, our data will be available as a data prop once again. In the `ExamplePage` function, replace the ``{gettext(data.content)}`` line with::

    {!data && gettext('Loading...')}
    {data && gettext(data.username)}

#. Your ``kuma/javascript/src/dashboards/example.jsx`` file should look like::

    // @flow
    import * as React from 'react';

    import { gettext } from '../l10n.js';
    import A11yNav from '../a11y/a11y-nav.jsx';
    import Header from '../header/header.jsx';
    import Footer from '../footer.jsx';
    import Route, { type RouteComponentProps } from '../route.js';

    type ExampleRouteParams = {
        locale: string
    };

    export default function ExamplePage({ data }: RouteComponentProps) {
        return (
            <>
                <A11yNav />
                <Header />
                {!data && gettext('Loading...')}
                {data && gettext(data.username)}
                <Footer />
            </>
        );
    }

    const BASEURL =
        typeof window !== 'undefined' && window.location
            ? window.location.origin
            : 'http://ssr.hack';

    export class ExampleRoute extends Route<ExampleRouteParams, null> {
        locale: string;

        constructor(locale: string) {
            super();
            this.locale = locale;
        }

        getComponent() {
            return ExamplePage;
        }

        match(url: string): ?ExampleRouteParams {
            const path = new URL(url, BASEURL).pathname;
            const examplePath = `/${this.locale}/dashboards/example/`;
            const regex = new RegExp(examplePath, 'g');

            if (regex.test(path)) {
                return {
                    locale: this.locale
                };
            }
            return null;
        }

        fetch(): Promise<any> {
            return fetch('/api/v1/whoami').then(response => response.json());
        }
    }



#. Refresh the page in the browser, and you should now see your username if you are logged in. Or just the header and footer if you are logged out.

Database migrations
===================
Apps are migrated using Django's migration system. To run the migrations::

    ./manage.py migrate

If your changes include schema modifications, see the Django documentation for
the `migration workflow`_.

.. _migration workflow: https://docs.djangoproject.com/en/1.8/topics/migrations/#workflow

Coding conventions
==================
See CONTRIBUTING.md_ for details of the coding style on Kuma.

New code is expected to have test coverage.  See the
:doc:`Test Suite docs <tests>` for tips on writing tests.

.. _CONTRIBUTING.md: https://github.com/mdn/kuma/blob/master/CONTRIBUTING.md

Managing dependencies
=====================

Python dependencies
-------------------

Kuma uses `Poetry`_ for dependency management. Poetry is configured in the
``pyproject.toml`` file at the root of the repository, and exact versions of
dependencies (along with hashes) are stored in the ``poetry.lock`` file.

Please refer to the Poetry docs on `adding`_ and `updating`_ dependencies.

A few examples:

* Use ``poetry update`` to update and re-lock all dependencies to their latest
  compatible versions, according to constraints in ``pyproject.toml``.

* Use ``poetry update <name>`` to update only a single dependency to its latest
  compatible version, according to constraints in ``pyproject.toml``. For
  example ``poetry update pytz``.

* To update a package to the very latest and not just what matches what's
  currently in ``pyproject.toml``, add ``@latest``. For example
  ``poetry update pytz@latest``.

* Use ``poetry add <name>`` to modify or add new entries inside of
  ``pyproject.toml``, for example, ``poetry add django~2.2`` or ``poetry add
  flake8@latest``.

* Use ``poetry lock`` to regenerate the ``poetry.lock``, for example, after
  manually editing ``pyproject.toml``.

* Use ``poetry show`` to report on the project's dependencies.

In brief, ``update`` alters the lockfile, but does not modify entries within
``pyproject.toml``. The ``add`` command changes both.

You may wish to run these commands inside of Docker::

    docker-compose exec web poetry update --dry-run

Using Poetry directly on your host computer is also fine; the resulting
``pyproject.toml`` and ``poetry.lock`` files should be the same either way.

.. _Poetry: https://python-poetry.org/
.. _adding: https://python-poetry.org/docs/cli/#add
.. _updating: https://python-poetry.org/docs/cli/#update

.. _front-end-asset-dependencies:

Front-end asset dependencies
----------------------------
Front-end dependencies are managed by Bower_ and checked into the repository.
Follow these steps to add or upgrade a dependency:

#. On the host, update ``bower.json``.
#. Start a root Docker container shell ``docker-compose run -u root web bash``
#. (*Docker only*) In the root container shell, run::

    apt-get update
    apt-get install -y git
    npm install -g bower-installer
    bower-installer

#. On the host, prepare the dependency to be committed (``git add path/to/dependency``).

Front-end dependencies that are not already managed by Bower should begin using
this approach the next time they're upgraded.

.. _Bower: http://bower.io

Front-end toolchain dependencies
--------------------------------
The Front-end toolchain dependencies are managed by yarn_, but not checked in to
the repository. Follow these steps to add a dependency:

    docker-compose exec web bash

Once you're inside the Docker container, run:

    yarn add my-needed-new-lib

Exit the container and the check in the changes to ``package.json`` and ``yarn.lock``.

To *upgrade* a dependency:

    docker-compose exec web bash

Once you're inside the Docker container, run:

    yarn upgrade-interactive --latest

Use the interactive prompt.
Exit the container and the check in the changes to ``package.json`` and ``yarn.lock``.

.. _yarn: https://yarnpkg.com/


Customizing with environment variables
======================================
`Environment variables`_ are used to change the way different components work.
There are a few ways to change an environment variables:

* Exporting in the shell, such as::

    export DEBUG=True;
    ./manage.py runserver

* A one-time override, such as::

    DEBUG=True ./manage.py runserver

* Changing the ``environment`` list in ``docker-compose.yml``.
* Creating a ``.env`` file in the repository root directory.

One variable you may wish to alter for local development is ``DEBUG_TOOLBAR``,
which, when set to ``True``, will enable the Django Debug Toolbar::

    DEBUG_TOOLBAR=True

Note that enabling the Debug Toolbar can severely impact response time, adding
around 4 seconds to page load time.

.. _Environment variables: http://12factor.net/config

Customizing number of workers
=============================

The ``docker-compose.yml`` in git comes with a default setting of
4 ``celery`` workers and 4 ``gunicorn`` workers. That's pretty resource
intensive since they prefork. To change the number of ``gunicorn``
and ``celery`` workers, consider setting this in your ``.env`` file::

    CELERY_WORKERS=2
    GUNICORN_WORKERS=3

In that example, it will only start 2 ``celery`` workers and 3 ``gunicorn``
workers just for your environment.

.. _advanced_config_docker:

Customizing the Docker environment
==================================
Running docker-compose_ will create and run several containers, and each
container's environment and settings are configured in ``docker-compose.yml``.
The settings are "baked" into the containers created by ``docker-compose up``.

To override a container's settings for development, use a local override file.
For example, the ``web`` service runs in a container with the
default command
"``gunicorn -w 4 --bind 0.0.0.0:8000 --timeout=120 kuma.wsgi:application``".
(The container has a name that begins with ``kuma_web_1_`` and
ends with a string of random hex digits. You can look up the name of
your particular container with ``docker ps | grep kuma_web``. You'll
need this container name for some of the commands described below.)
A useful alternative for debugging is to run a single-threaded process that
loads the Werkzeug debugger on exceptions (see docs for runserver_plus_), and
that allows for stepping through the code with a debugger.
To use this alternative, create an override file ``docker-compose.override.yml``::

    version: "2.1"
    services:
      web:
        command: ./manage.py runserver_plus 0.0.0.0:8000
        stdin_open: true
        tty: true


This is similar to "``docker run -it <container> ./manage.py runserver_plus``",
using all the other configuration items in ``docker-compose.yml``.
Apply the custom setting with::

    docker-compose up -d

You can then add ``pdb`` breakpoints to the code
(``import pdb; pdb.set_trace``) and connect to the debugger with::

    docker attach <container>

A similar method can be used to override environment variables in containers,
run additional services, or make other changes.  See the docker-compose_
documentation for more ideas on customizing the Docker environment.

.. _docker-compose: https://docs.docker.com/compose/overview/
.. _pdb: https://docs.python.org/2/library/pdb.html
.. _runserver_plus: http://django-extensions.readthedocs.io/en/latest/runserver_plus.html

Customizing the database
========================
The database connection is defined by the environment variable
``DATABASE_URL``, with this default::

    DATABASE_URL=mysql://root:kuma@mysql:3306/developer_mozilla_org

The format is defined by the dj-database-url_ project::

    DATABASE_URL=mysql://user:password@host:port/database

If you configure a new database, override ``DATABASE_URL`` to connect to it. To
add an empty schema to a freshly created database::

    ./manage.py migrate

To connect to the database specified in ``DATABASE_URL``, use::

    ./manage.py dbshell

.. _dj-database-url: https://github.com/kennethreitz/dj-database-url

.. _generating-production-assets:

Generating production assets
============================
Setting ``DEBUG=False`` will put you in production mode, which adds aditional
asset processing:

* Javascript modules are combined into single JS files.
* CSS and JS files are minifed and post-processed by cleancss_ and UglifyJS_.
* Assets are renamed to include a hash of contents by a variant of Django's ManifestStaticFilesStorage_.

In production mode, assets and their hashes are read once when the server
starts, for efficiency. Any changes to assets require rebuilding with
``make build-static`` and restarting the web process.

To emulate production, and test compressed and hashed assets locally:

#. Set the environment variable ``DEBUG=False``
#. Start (``docker-compose up -d``) your Docker services.
#. Run ``docker-compose run --rm -e DJANGO_SETTINGS_MODULE=kuma.settings.prod web make build-static``.
#. Restart the web process using ``docker-compose restart web``.

Using secure cookies
====================
To prevent error messages like "``Forbidden (CSRF cookie not set.):``", set the
environment variable::

    CSRF_COOKIE_SECURE = false

This is the default in Docker, which does not support local development with
HTTPS.

.. _maintenance-mode:

Maintenance mode
================
Maintenance mode is a special configuration for running Kuma in read-only mode,
where all operations that would write to the database are blocked. As the name
suggests, it's intended for those times when we'd like to continue to serve
documents from a read-only copy of the database, while performing maintenance
on the master database.

For local Docker-based development in maintenance mode:

#. If you haven't already, create a read-only user for your local MySQL
   database::

    docker-compose up -d
    docker-compose exec web mysql -h mysql -u root -p
    (when prompted for the password, enter "kuma")
    mysql> source ./scripts/create_read_only_user.sql
    mysql> quit

#. Create a ``.env`` file in the repository root directory, and add these
   settings::

    MAINTENANCE_MODE=True
    DATABASE_USER=kuma_ro

   Using a read-only database user is not required in maintenance mode. You can run
   in maintenance mode just fine with only this setting::

    MAINTENANCE_MODE=True

   and going with a database user that has write privileges. The read-only database
   user simply provides a level of safety as well as notification (for example, an
   exception will be raised if an attempt to write the database slips through).

#. Update your local Docker instance::

    docker-compose up -d

#. You may need to recompile your static assets and then restart::

    docker-compose exec web make build-static
    docker-compose restart web

You should be good to go!

There is a set of integration tests for maintenance mode. If you'd like to run
them against your local Docker instance, first do the following:

#. Load the latest sample database (see :ref:`provision-the-database`).
#. Ensure that the test document "en-US/docs/User:anonymous:uitest" has been
   rendered (all of its macros have been executed). You can check this by
   browsing to http://localhost:8000/en-US/docs/User:anonymous:uitest. If
   there is no message about un-rendered content, you are good to go. If there
   is a message about un-rendered content, you will have to put your local
   Docker instance back into non-maintenance mode, and render the document:

   * Configure your ``.env`` file for non-maintenance mode::

       MAINTENANCE_MODE=False
       DATABASE_USER=root

   * ``docker-compose up -d``
   * Using your browser, do a shift-reload on
     http://localhost:8000/en-US/docs/User:anonymous:uitest

   and then put your local Docker instance back in maintenance mode:

   * Configure your ``.env`` file for maintenance mode::

       MAINTENANCE_MODE=True
       DATABASE_USER=kuma_ro

   * ``docker-compose up -d``

#. Configure your environment with DEBUG=False because the maintenance-mode
   integration tests check for the non-debug version of the not-found page::

       DEBUG=False
       MAINTENANCE_MODE=True
       DATABASE_USER=kuma_ro

   This, in turn, will also require you to recompile your static assets::

       docker-compose up -d
       docker-compose exec web ./manage.py compilejsi18n
       docker-compose exec web ./manage.py collectstatic
       docker-compose restart web

Now you should be ready for a successful test run::

    py.test --maintenance-mode -m "not search" tests/functional --base-url http://localhost:8000 --driver Chrome --driver-path /path/to/chromedriver

Note that the "search" tests are excluded. This is because the tests marked
"search" are not currently designed to run against the sample database.

Serving over SSL / HTTPS
========================
Kuma can be served over HTTPS locally with a self-signed certificate. Browsers
consider self-signed certificates to be unsafe, and you'll have to confirm
that you want an exception for this.


#. If you want GitHub logins:

   * In the `Django Admin for Sites`_, ensure that site #2's domain is set to
     ``developer.127.0.0.1.nip.io``.

   * In GitHub, generate a new GitHub OAuth app for the test SSL domain,
     modifying the procees at :ref:`enable-github-auth`. When creating the
     GitHub OAuth app, replace ``http://localhost:8000`` with
     ``https://developer.127.0.0.1.nip.io`` in both URLs. When creating the
     ``SocialApp`` in Kuma, chose the ``developer.127.0.0.1.nip.io`` site.

#. Include the SSL containers by updating ``.env``::

    COMPOSE_FILE=docker-compose.yml:docker-compose.ssl.yml

#. Run the new containers::

    docker-compose up -d

#. Load https://developer.127.0.0.1.nip.io/en-US/ in your browser, and add an
   exception for the self-signed certificate.

#. Load https://demos.developer.127.0.0.1.nip.io/en-US/ in your browser, and
   add an exception for the self-signed certificate again.

Some features of SSL-protected sites may not be available, because the browser
does not fully trust the self-signed SSL certificate. The HTTP-only website
will still be available at http://localhost:8000/en-US/, but GitHub logins will
not work.

.. _`Django Admin for Sites`: http://localhost:8000/admin/sites/site/

Enabling ``PYTHONWARNINGS``
===========================

Python `ignores some warnings`_ by default, including ``DeprecationWarning``.
To see these warnings, you can set the `PYTHONWARNINGS`_ environment variable
in your ``.env`` file. For example::

    # Show every warning, every time it occurs
    PYTHONWARNINGS=always

Or alternatively::

    # Show every warning, but ignore repeats
    PYTHONWARNINGS=default

Note: Explicitly setting ``PYTHONWARNINGS=default`` will not do what you expect.
It actually *disables* the default filters, ensuring that *every* warning gets
displayed, but only the first time it occurs on a given line.

See the `PYTHONWARNINGS`_ docs for more information on possible values.

.. _`ignores some warnings`: https://docs.python.org/3/library/warnings.html#default-warning-filter
.. _`PYTHONWARNINGS`: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONWARNINGS


Configuring AWS S3
==================

The ``publish`` and ``unpublish`` Celery tasks and Django management commands
require AWS S3 to be configured in order for them to do any real work, that is,
creating/updating/deleting S3 objects used by the stage/production document API.
In stage and production, the S3 bucket name as well as the AWS credentials are
configured via the container environment, which in turn, gets the AWS credentials
from a Kubernetes ``secrets`` resource. For local development, there is no need
for any of this configuration. The ``publish`` and ``unpublish`` tasks will
simply be skipped (although, for verification/debugging purposes, you can see
the detailed skip messages in the ``worker`` log (
``docker-compose logs -f worker``).

However, if for testing purposes you'd like to locally configure the
``publish`` and ``unpublish`` tasks to use S3, you can simply add the
following to your ``.env`` file::

    MDN_API_S3_BUCKET_NAME=<your-s3-bucket-name>
    AWS_ACCESS_KEY_ID=<your-aws-access-key>
    AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>


Enabling ``django-querycount``
==============================

If you want to find out how many SQL queries are made, per request,
even if they are XHR requests, you can simply add this to your ``.env`` file::

    ENABLE_QUERYCOUNT=true

Stop and start ``docker-compose`` and now, on ``stdout``, it will print a
table for every request URL about how many queries that involved and
some information about how many of them were duplicates.

If you want more insight into the duplicate queries add this to your ``.env``::

    QUERYCOUNT_DISPLAY_DUPLICATES=3

A number greater than the (default) 0 means it will print the 3 most
repeated SQL queries.
