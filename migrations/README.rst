===================
Database Migrations
===================

We'll be using `South <http://south.aeracode.org/>`_ for database
migrations. Migrations should be stored in this folder and in numerical
order. For example::

    $ ls
    01-add-index.sql
    02-drop-index.sql
    03-change-table.sql

And so on. Whenever you add a migration, take the next available integer for
your version number.


Migrations vs ``syncdb``
========================

What's the difference between a migration and the Django ``syncdb``
command? Which should I use?

``syncdb`` only works on *new* models. (Which makes sense. You'd hate for
accidentally deleting a line to irreplacably destroy an entire column of
data!) If you're adding a new model, assume ``syncdb`` will create it. If
your model has *never* been merged to the integration branch
(``development``), it's still considered "new." That means you can iterate on
a feature or bug branch without having to mess with migrations.

A migration is necessary when you change a model later, and want to update the
table to match. Using the management command ``sqldiff`` will print out the
SQL for your migration. Just save it, numbered correctly, in the
``/migrations`` directory.

We'll probably use `schematic <http://github.com/jbalogh/schematic>`_ to
actually *run* the migrations. We haven't had any yet, though.

Another possible use of a migration is to add something you can't quite do
through the model definitions, like a multi-column index, for example.
