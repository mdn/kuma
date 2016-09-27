=============================
Celery and Asynchronous Tasks
=============================
Kuma uses Celery_ to enable asynchronous task processing for long-running jobs
and to speed up the request-response cycle.

When is Celery Appropriate
==========================
You can use Celery to do any processing that doesn't need to happen in the
current request-response cycle.  Ask yourself the question: "Is the user going
to need this data on the page I'm about to send them?" If not, using a Celery
task may be a good choice.

Some examples where Celery is used:

* **Sending notification emails on page changes** - If this was done in the
  page change request, then pages with many watchers would be slower to edit,
  and errors in email sending would result in a "``500 Internal Server Error``"
  for the editor.
* **Populating the contributor bar** - Gathering and sorting the contributor
  list can be a slow process that would delay rendering of stale pages.
  Instead, viewers quickly see the content, possibly without the contributor
  bar. Once the async task has populated the cache, future viewers get the
  content and the contributor bar.
* **Generating the spam moderator dashboard** - Calculating spam statistics
  is a potentially long process, and if it takes more than 30 seconds the
  viewer will get a "``502 Bad Gateway``" error. The async task can take as long as
  needed, and the spam moderator will see the dashboard when the data is
  calculated and cached.
* **Rebuilding sitemaps** - Search engines need recent site URL data, and it
  can't be assembled quickly in the request for the sitemap. An async request
  repopulates the cached sitemap data, keeping this data fast and up-to-date.

There are some downsides to async tasks that should also be considered:

* Message passing, serialization, de-serialization, and data reloading increase
  the load on the entire system.
* Async tasks require different testing strategies. It is easy to write a
  passing test that doesn't reflect how the task is called in production.
* Runtime errors are more difficult to troubleshoot with async tasks, due to
  missing context on how they were called.

In general, it is better to get an algorithm right in the request loop, and
only move it to an asynchronous task when it is identified as a performance
issue.

Celery Services
===============
A working Celery installation requires several services.

Worker
------
Celery processes tasks with one or more workers. In Kuma, the workers and web
processes share a code base, so that Django models, functions, and settings are
available to async tasks, and web code can easily schedule async tasks.

In Vagrant, the worker process is started with the ``foreman`` command.  In
Docker, the worker process runs in the ``worker`` service / container.

Broker
------
Celery requires a `message broker`_ for task communication. There are two stable,
production-ready alternatives:

* RabbitMQ_ is an AMQP_ message broker written in Erlang_. The Celery team has
  recommended it for a long time, and the docs describe it as
  "feature-complete, stable, durable and easy to install". It is used in the
  Vagrant and production environments.
* Redis_ is an in-memory data structure store, used as database, cache and
  message broker.  Many projects use it for multiple roles in the same
  deployment. With Celery 3.1, it is now recommended as a `stable broker`_,
  with some caveats_. It is used in the Docker environment.

.. _AMQP: https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol
.. _Celery: http://celeryproject.org/
.. _Erlang: https://en.wikipedia.org/wiki/Erlang_(programming_language)
.. _RabbitMQ: https://www.rabbitmq.com
.. _Redis: http://redis.io
.. _caveats: http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html
.. _message broker: http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#choosing-a-broker
.. _stable broker: http://docs.celeryproject.org/en/latest/getting-started/brokers/index.html

Result Store
------------
When a task completes, it returns processed data and task states to a
`results store`_. Kuma doesn't use returned data, but it does use returned task
state to coordinate multi-step tasks.

Kuma uses a database-backed task store provided by django-celery_, a deprecated
integration project for Django and Celery.  The work to replace this is tracked
in `bug 1268257`_.

.. _bug 1268257: https://bugzilla.mozilla.org/show_bug.cgi?id=1268257
.. _django-celery: https://github.com/celery/django-celery
.. _results store: http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#keeping-results

Periodic Tasks Scheduler
------------------------
Periodic tasks are scheduled with `celery beat`_, which adds tasks to the task
queue when they become due.  It should only be run once in a deployment, or
tasks may be scheduled multiple times.

It is run in the Docker and Vagrant environments by running the single celery
worker process with ``--beat``.  In production, there are several task workers,
and the ``celery beat`` process is run directly on just one worker.

The schedules themselves are configured using the deprecated `django-celery`_
database backend.  The work to replace this is tracked in `bug 1268256`_.

.. _celery beat: http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html
.. _bug 1268256: https://bugzilla.mozilla.org/show_bug.cgi?id=1268256

Monitoring
----------
Celery task workers generate events to communicate task and worker health.  The
``celerycam`` service, provided by the deprecated django-celery_ project,
captures these events and stores them in the database.  Switching to a
supported project, like Flower_, is tracked in bug 1268281.

In the Vagrant environment, ``celerycam`` is started with other Kuma services
with ``foreman``.  It is not part of the default Docker services, but can be
started inside the ``worker`` service container with::

    ./manage.py celerycam --freq=2.0

For more options, see the `Monitoring and Management Guide`_ in the Celery
documentation.

.. _bug 1268281: https://bugzilla.mozilla.org/show_bug.cgi?id=1268281
.. _Flower: http://flower.readthedocs.io/en/latest/
.. _Monitoring and Management Guide: http://docs.celeryproject.org/en/latest/userguide/monitoring.htm

Configuring and Running Celery
==============================
We set some reasonable defaults for Celery in ``kuma/settings/common.py``. These can be
overridden by the environment variables, including:

- CELERY_ALWAYS_EAGER_

  Default: ``false`` (Docker), ``true`` (Vagrant, tests).

  When ``true``, tasks are executed immediately, instead of being scheduled and
  executed by a worker, skipping the broker, results store, etc. In theory,
  tasks should act the same whether executed eagerly or normally. In practice,
  there are some tasks that fail or have different results in the two modes,
  mostly due to database transactions.

- CELERYD_CONCURRENCY_

  Default: ``4``.

  Each worker will execute this number of tasks at the same time. ``1`` is a
  good value for debugging, and the number of CPUs in your environment is good
  for performance.

The worker can also be adjusted at the command line. For example, this could
run inside the ``worker`` service container::

    ./manage.py celeryd --log-level=DEBUG -c 10

This would start Celery with 10 worker threads and a log level of ``DEBUG``.

.. _CELERY_ALWAYS_EAGER: http://docs.celeryproject.org/en/latest/configuration.html#celery-always-eager
.. _CELERYD_CONCURRENCY: http://docs.celeryproject.org/en/latest/configuration.html#celeryd-concurrency
