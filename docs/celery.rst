======================
Celery and async tasks
======================
Kuma uses Celery_ to enable asynchronous task processing for long-running jobs
and to speed up the request-response cycle.

.. _Celery: https://github.com/celery/celery

When is Celery appropriate
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

Celery services
===============
A working Celery installation requires several services.

Worker
------
Celery processes tasks with one or more workers. In Kuma, the workers and web
processes share a code base, so that Django models, functions, and settings are
available to async tasks, and web code can easily schedule async tasks.

In Docker, the worker process runs in the ``worker`` service / container.

Broker
------

Kuma uses Redis_ as the `message broker`_. There are some caveats_ to be aware of.
Redis_ is used both in local development and in production.

.. _Redis: http://redis.io
.. _caveats: http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html
.. _message broker: http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#choosing-a-broker

Result store
------------
When a task completes, it returns processed data and task states to a
`results store`_. Kuma doesn't use returned data, but it does use returned task
state to coordinate multi-step tasks.

Referring to logging to see message about completion of Celery worker tasks.

.. _results store: http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#keeping-results
.. _chord tasks: https://docs.celeryproject.org/en/latest/userguide/canvas.html#chords

Periodic tasks scheduler
------------------------
Periodic tasks are scheduled with `celery beat`_, which adds tasks to the task
queue when they become due.  It should only be run once in a deployment, or
tasks may be scheduled multiple times.

In Docker, it runs in the ``worker`` container by starting the celery process
with ``--beat``.  In production, there are several task workers, and the
``celery beat`` process is run directly on just one worker.

All scheduled periodic tasks are configured in code. As a pattern, each
Django app (e.g. ``kuma.wiki``) that has tasks to run periodically are
wired up within the ``ready`` method of each app's app config class
(e.g. ``kuma.wiki.apps.WikiConfig``).

.. _celery beat: http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html


Configuring and running Celery
==============================
We set some reasonable defaults for Celery in ``kuma/settings/common.py``. These can be
overridden by the environment variables, including:

- ``CELERY_TASK_ALWAYS_EAGER``

  Default: ``False`` (Docker), ``True`` (tests).

  When ``True``, tasks are executed immediately, instead of being scheduled and
  executed by a worker, skipping the broker, results store, etc. In theory,
  tasks should act the same whether executed eagerly or normally. In practice,
  there are some tasks that fail or have different results in the two modes,
  mostly due to database transactions.

- ``CELERY_WORKER_CONCURRENCY``

  Default: ``4``.

  Each worker will execute this number of tasks at the same time. ``1`` is a
  good value for debugging, and the number of CPUs in your environment is good
  for performance.

The worker can also be adjusted at the command line. For example, this could
run inside the ``worker`` service container::

    celery -A kuma.celery:app worker --log-level=DEBUG -c 10

This would start Celery with 10 worker threads and a log level of ``DEBUG``.
