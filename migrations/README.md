Migration Notes
===============

This project is in transition between [Schematic][1] and [South][2] migrations.

The main thing to keep in mind about this is that any SQL migrations you write
for Schematic should steer clear of any tables of apps managed by South. 

Someday, this README might contain more useful information.

[1]: https://github.com/jbalogh/schematic/
[2]: http://south.aeracode.org/

How to run migrations
---------------------

Order is important. Run Schematic before South, just in case the SQL migrations
have fixes that preempt South:

    python2.6 vendor/src/schematic/schematic migrations
    python2.6 manage.py migrate

South-managed apps and DB tables
--------------------------------

These are apps managed by South. Do not create Schematic SQL migrations that
touch these tables, unless you're very sure about what you're doing and can
keep from breaking South migrations.

* demos
    * demos_submission
* taggit
    * taggit_tag
    * taggit_taggeditem

How to not break South migrations
---------------------------------

* Ensure your SQL migrations don't contain anything that will cause an error if
    South tries doing the same thing again. (eg. table creation, etc)

* Converting apps over to South migrations.
    * Mozilla staging auto-update does not ever run `manage.py migrate --fake`
    * So, South will try to run the 0001_initial migration, which will break
        when it tries to create tables that already exist.
    * To prevent that, commit a SQL migration that inserts a row into
        `south_migrationhistory` that tricks South into thinking that the initial
        migration has already been run.
    * [An example SQL migration][southfix]

* In general, if you must use a schematic migration, and it would conflict with
    a South migration, insert a row into `south_migrationhistory` to make South
    skip the migration.

[southfix]: https://github.com/mozilla/kuma/blob/mdn/migrations/06-taggit-convert-to-south.sql
