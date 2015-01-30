Migrations
==========

South-managed apps and DB tables
--------------------------------

Basically all apps are migrated using South. We used to use a different
migration tool side by side with South. But that's ancient history.

You can `convert an app over to South <http://south.aeracode.org/docs/convertinganapp.html#converting-an-app>`_, if it doesn't have
migrations yet, for great justice.

How to run the migrations
-------------------------

Run South via its Django management command::

    python2.6 manage.py migrate

Where are the migrations?
-------------------------

South migrations for first-party, non-vendor apps are in a ``migrations``
subdirectory. For example, check out ``kuma/demos/migrations``.

South migrations for third-party apps under ``vendor/`` are found in python
modules under ``migrations/south/`` and are activated by adding them to
``SOUTH_MIGRATION_MODULES`` in ``settings.py``. See
`the South docs <http://south.aeracode.org/docs/settings.html#setting-south-migration-modules>`_ about this.
