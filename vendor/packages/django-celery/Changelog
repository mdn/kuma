================
 Change history
================

.. contents::
    :local:

.. _version-2.5.5:

2.5.5
=====
:release-date: 2012-04-19 01:46 P.M BST

* Fixed bug where task modules were not imported.

.. _version-2.5.4:

2.5.4
=====
:release-date: 2012-04-16 06:31 P.M BST

* Compatibility with celery 2.5.3

* Database scheduler now imports ``exchange``, ``routing_key`` and ``queue``
  options from ``CELERYBEAT_SCHEDULE``.

.. _version-2.5.3:

2.5.3
=====
:release-date: 2012-04-13 06:16 P.M BST
:by: Ask Solem

* 2.5.2 release broke installation because of an import in the package.

    Fixed by not having setup.py import the djcelery module anymore,
    but rather parsing the package file for metadata.

.. _version-2.5.2:

2.5.2
=====
:release-date: 2012-04-13 05:00 P.M BST
:by: Ask Solem

.. _v251-news:

* PeriodicTask admin now lists the enabled field in the list view

    Contributed by Gabe Jackson.

.. _v251-fixes:

* Fixed a compatibility issue with Django < 1.3

    Fix contributed by Roman Barczyski

* Admin monitor now properly escapes args and kwargs.

    Fix contributed by Serj Zavadsky

* PeriodicTask admin now gives error if no schedule set (or both set)
  (Issue #126).

* examples/demoproject has been updated to use the Django 1.4 template.

* Database connection is no longer closed for eager tasks (Issue #116).

    Fix contributed by Mark Lavin.

* The first-steps document for django-celery has been moved to the main
  Celery documentation.

* djcelerymon command no longer worked properly, this has now been fixed
  (Issue #123).

.. _version-2.5.1:

2.5.1
=====
:release-date: 2012-03-01 01:00 P.M GMT
:by: Ask Solem

.. _v251-fixes:

Fixes
-----

* Now depends on Celery 2.5.1

* Fixed problem with recursive imports when USE_I18N was enabled
  (Issue #109).

* The ``CELERY_DB_REUSE_MAX`` setting was not honored.

* The djcelerymon command no longer runs with DEBUG.

    To enable debug you can set the :envvar:`DJCELERYMON_DEBUG`
    environment variable.

* Fixed eventlet/gevent compatability with Django 1.4's new thread
  sharing detection.

* Now depends on django-picklefield 0.2.0 or greater.

    Previous versions would not work correctly with Django 1.4.

.. _version-2.5.0:

2.5.0
=====
:release-date: 2012-02-24 02:00 P.M GMT
:by: Ask Solem

.. _v250-important:

Important Notes
---------------

* Now depends on Celery 2.5.

* Database schema has been updated.

    After upgrading you need migrate using South, or migrate manually
    as described below.

    These changes means that expiring results will be faster and
    take less memory than before.

    In addition a description field to the PeriodicTask model has
    been added so that the purpose of a periodic task
    in the database can be documented via the Admin interface.

    **South Migration**

    To migrate using South execute the following command::

        $ python manage.py migrate djcelery

    If this is a new project that is also using South then you need
    to fake the migration:

        $ python manage.y migrate djcelery --fake

    **Manual Migration**

    To manually add the new fields,

    using PostgreSQL:

    .. code-block: sql

        ALTER TABLE celery_taskmeta
            ADD hidden BOOLEAN NOT NULL DEFAULT FALSE;

        ALTER TABLE celery_tasksetmeta
            ADD hidden BOOLEAN NOT NULL DEFAULT FALSE;

        ALTER TABLE djcelery_periodictask
            ADD description TEXT NOT NULL DEFAULT ""

    using MySQL:

    .. code-block:: sql

        ALTER TABLE celery_taskmeta
            ADD hidden TINYINT NOT NULL DEFAULT 0;

        ALTER TABLE celery_tasksetmeta
            ADD hidden TINYINT NOT NULL DEFAULT 0;

        ALTER TABLE djcelery_periodictask
            ADD description TEXT NOT NULL DEFAULT "";

    using SQLite:

    .. code-block:: sql

        ALTER TABLE celery_taskmeta
            ADD hidden BOOL NOT NULL DEFAULT FALSE;
        ALTER TABLE celery_tasksetmeta
            ADD hidden BOOL NOT NULL DEFAULT FALSE;
        ALTER TABLE djcelery_periodictask
            ADD description VARCHAR(200) NOT NULL DEFAULT "";

.. _v250-news:

News
----

* Auto-discovered task modules now works with the new auto-reloader
  functionality.

* The database periodic task scheduler now tried to recover from
  operational database errors.

* The periodic task schedule entry now accepts both int and
  timedelta (Issue #100).

* 'Connection already closed' errors occurring while closing
  the database connection are now ignored (Issue #93).

* The ``djcelerymon`` command used to start a Django admin monitor
  instance outside of Django projects now starts without a celery
  config module.

* Should now work with Django 1.4's new timezone support.

   Contributed by Jannis Leidel and Donald Stufft.

* South migrations did not work properly.

    Fix contributed by Christopher Grebs.

* celeryd-multi now preserves django-related arguments,
  like ``--settings`` (Issue #94).


* Migrations now work with Django < 1.3 (Issue #92).

    Fix contributed by Jude Nagurney.

* The expiry of the database result backend can now be an int (Issue #84).


.. _version-2.4.2:

2.4.2
=====
:release-date: 2011-11-14 12:00 P.M GMT

* Fixed syntax error in South migrations code (Issue #88).

    Fix contributed by Olivier Tabone.

.. _version-2.4.1:

2.4.1
=====
:release-date: 2011-11-07 06:00 P.M GMT
:by: Ask Solem

* Management commands was missing command line arguments because of recent
  changes to Celery.

* Management commands now supports the ``--broker|-b`` option.

* South migrations now ignores errors when tables already exist.

.. _version-2.4.0:

2.4.0
=====
:release-date: 2011-11-04 04:00 P.M GMT
:by: Ask Solem

.. _240-important:

Important Notes
---------------

This release adds `South`_ migrations, which well assist users in automatically
updating their database schemas with each django-celery release.

.. _`South`: http://pypi.python.org/pypi/South/

.. _240-news:

News
----

* Now depends on Celery 2.4.0 or higher.

* South migrations have been added.

    Migration 0001 is a snapshot from the previous stable release (2.3.3).
    For those who do not use South, no action is required.
    South users will want to read the :ref:`240-upgrade_south` section
    below.

    Contributed by Greg Taylor.

* Test runner now compatible with Django 1.4.

    Test runners are now classes instead of functions,
    so you have to change the ``TEST_RUNNER`` setting to read::

        TEST_RUNNER = "djcelery.contrib.test_runner.CeleryTestSuiteRunner"

    Contributed by Jonas Haag.

.. _240-upgrade_south:

Upgrading for south users
-------------------------

For those that are already using django-celery 2.3.x, you'll need to fake the
newly added migration 0001, since your database already has the current
``djcelery_*`` and ``celery_*`` tables::

    $ python manage.py migrate djcelery 0001 --fake

If you're upgrading from the 2.2.x series, you'll want to drop/reset your
``celery_*`` and ``djcelery_*`` tables and run the migration::

    $ python manage.py migrate djcelery

.. _version-2.3.3:

2.3.3
=====
:release-date: 2011-08-22 12:00 AM BST

* Precedence issue caused database backend tables to not be
  created (Issue #62).

.. _version-2.3.2:

2.3.2
=====
:release-date: 2011-08-20 12:00 AM BST

* Fixes circular import of DatabaseBackend.

.. _version-2.3.1:

2.3.1
=====
:release-date: 2011-08-11 12:00 PM BST

* Django database result backend tables were not created.

  If you are having troubles because of this, be sure you do a ``syncdb``
  after upgrading, that should resolve the issue.

.. _version-2.3.0:

2.3.0
=====
:release-date: 2011-08-05 12:00 PM BST

* Now depends on Celery 2.3.0

    Please read the Celery 2.3.0 changelog!

.. _version-2.2.4:

2.2.4
=====

* celerybeat: DatabaseScheduler would not react to changes when using MySQL and
  the default transaction isolation level ``REPEATABLE-READ`` (Issue #41).

    It is still recommended that you use isolation level ``READ-COMMITTED``
    (see the Celery FAQ).

.. _version-2.2.3:

2.2.3
=====
:release-date: 2011-02-12 16:00 PM CET

* celerybeat: DatabaseScheduler did not respect the disabled setting after restart.

* celeryevcam: Expiring objects now works on PostgreSQL.

* Now requires Celery 2.2.3

.. _version-2.2.2:

2.2.2
=====
:release-date: 2011-02-03 16:00 PM CET

* Now requires Celery 2.2.2

* Periodic Task Admin broke if the CELERYBEAT_SCHEDULE setting was not set.

* DatabaseScheduler No longer creates duplicate interval models.

* The djcelery admin templates were not included in the distribution.

.. _version-2.2.1:

2.2.1
=====

:release-date: 2011-02-02 16:00 PM CET

* Should now work with Django versions previous to 1.2.

.. _version-2.2.0:

2.2.0
=====
:release-date: 2011-02-01 10:00 AM CET

* Now depends on Celery v2.2.0

* djceleryadm: Adds task actions Kill and Terminate task

* celerycam: Django's queryset.delete() fetches everything in
  memory THEN deletes, so we need to use raw SQL to expire objects.

* djcelerymon: Added Command.stdout + Command.stderr  (Issue #23).

* Need to close any open database connection after any embedded
  celerybeat process forks.

* Added contrib/requirements/py25.txt

* Demoproject now does ``djcelery.setup_loader`` in settings.py.

.. _version-2.1.1:

2.1.1
=====
:release-date: 2010-10-14 02:00 PM CEST

* Now depends on Celery v2.1.1.

* Snapshots: Fixed bug with losing events.

* Snapshots: Limited the number of worker timestamp updates to once every second.

* Snapshot: Handle transaction manually and commit every 100 task updates.

* snapshots: Can now configure when to expire task events.

    New settings:

    * ``CELERYCAM_EXPIRE_SUCCESS`` (default 1 day),
    * ``CELERYCAM_EXPIRE_ERROR`` (default 3 days), and
    * ``CELERYCAM_EXPIRE_PENDING`` (default 5 days).

* Snapshots: ``TaskState.args`` and ``TaskState.kwargs`` are now
  represented as ``TextField`` instead of ``CharField``.

    If you need to represent arguments larger than 200 chars you have
    to migrate the table.

* ``transaction.commit_manually`` doesn't accept arguments on older
  Django version.

    Should now work with Django versions previous to v1.2.

* The tests doesn't need :mod:`unittest2` anymore if running on Python 2.7.

.. _version-2.1.0:

2.1.0
=====
:release-date: 2010-10-08 12:00 PM CEST

Important Notes
---------------

This release depends on Celery version 2.1.0.
Be sure to read the Celery changelog before you upgrade:
http://ask.github.com/celery/changelog.html#version-2-1-0

News
----

* The periodic task schedule can now be stored in the database and edited via
  the Django Admin interface.

    To use the new database schedule you need to start ``celerybeat`` with the
    following argument::

        $ python manage.py celerybeat -S djcelery.schedulers.DatabaseScheduler

    Note that you need to add your old periodic tasks to the database manually
    (using the Django admin interface for example).

* New Celery monitor for the Django Admin interface.

    To start monitoring your workers you have to start your workers
    in event mode::

        $ python manage.py celeryd -E

    (you can do this without restarting the server too::

        >>> from celery.task.control import broadcast
        >>> broadcast("enable_events")

    You need to do a syncdb to create the new tables:

        python manage.py syncdb

    Then you need to start the snapshot camera::

        $ python manage.py celerycam -f 2.0

    This will take a snapshot of the events every 2 seconds and store it in
    the database.

Fixes
-----

* database backend: Now shows warning if polling results with transaction isolation level
  repeatable-read on MySQL.

    See http://github.com/ask/django-celery/issues/issue/6

* database backend: get result does no longer store the default result to
  database.

    See http://github.com/ask/django-celery/issues/issue/6

2.0.2
=====

Important notes
---------------

* Due to some applications loading the Django models lazily, it is recommended
  that you add the following lines to your ``settings.py``::

       import djcelery
       djcelery.setup_loader()

    This will ensure the Django celery loader is set even though the
    model modules haven't been imported yet.

News
----

* ``djcelery.views.registered_tasks``: Added a view to list currently known
  tasks.

2.0.0
=====
:release-date: 2010-07-02 02:30 P.M CEST

* Initial release
