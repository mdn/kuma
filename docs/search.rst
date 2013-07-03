.. This Source Code Form is subject to the terms of the Mozilla Public
.. License, v. 2.0. If a copy of the MPL was not distributed with this
.. file, You can obtain one at http://mozilla.org/MPL/2.0/.

======
Search
======

Kuma uses `Sphinx Search <http://www.sphinxsearch.com>`_ to power its
on-site search facility.

Sphinx search gives us a number of advantages over MySQL's full-text search or
Google's site search.

* Much faster than MySQL.
  * And reduces load on MySQL.
* We have total control over what results look like.
* We can adjust searches with non-visible content.
* We don't rely on Google reindexing the site.
* We can fine-tune the algorithm ourselves.


Installing Sphinx Search
========================

We currently require **Sphinx 0.9.9**. You may be able to install this from a
package manager like yum, aptitude, or brew.

If not, you can easily `download <http://sphinxsearch.com/downloads/>`_ the
source and compile it. Generally all you'll need to do is::

    $ cd sphinx-0.9.9
    $ ./configure --enable-id64  # Important! We need 64-bit document IDs.
    $ make
    $ sudo make install

This should install Sphinx in ``/usr/local/bin``. (You can change this by
setting the ``--prefix`` argument to ``configure``.)

To test that everything works, make sure that the ``SPHINX_INDEXER`` and
``SPHINX_SEARCHD`` settings point to the ``indexer`` and ``searchd`` binaries,
respectively. (Probably ``/usr/local/bin/indexer`` and
``/usr/local/bin/searchd``, unless you changed the prefix.) Then run the
Kuma search tests::

    $ ./manage.py test -s --noinput --logging-clear-handlers search

If the tests pass, everything is set up correctly!


Using Sphinx Search
===================

Having Sphinx installed will allow the search tests to run, which may be
enough. But you want to work on or test the search app, you will probably need
to actually see search results!


The Easy, Sort of Wrong Way
---------------------------

The easiest way to start Sphinx for testing is to use some helpful management
commands for developers::

    $ ./manage.py reindex
    $ ./manage.py start_sphinx

You can also stop Sphinx::

    $ ./manage.py stop_sphinx

If you need to update the search indexes, you can pass the ``--rotate`` flag to
``reindex`` to update them in-place::

    $ ./manage.py reindex --rotate

While this method is very easy, you will need to reindex after any time you run
the search tests, as they will overwrite the data files Sphinx uses.


The Complicated but Safe Way
----------------------------

You can safely run multiple instances of ``searchd`` as long as they listen on
different ports, and store their data files in different locations.

The advantage of this method is that you won't need to reindex every time you
run the search tests. Otherwise, this should be identical to the easy method
above.

Start by copying ``configs/sphinx`` to a new directory, for example::

    $ cp -r configs/sphinx ../
    $ cd ../sphinx

Then create your own ``localsettings.py`` file::

    $ cp localsettings.py-dist localsettings.py
    $ vim localsettings.py

Fill in the settings so they match the values in ``settings_local.py``. Pick a
place on the file system for ``ROOT_PATH``.

Once you have tweaked all the settings so Sphinx will be able to talk to your
database and write to the directories, you can run the Sphinx binaries
directly (as long as they are on your ``$PATH``)::

    $ indexer --all -c sphinx.conf
    $ searchd -c sphinx.conf

You can reindex without restarting ``searchd`` by using the ``--rotate`` flag
for ``indexer``::

    $ indexer --all --rotate -c sphinx.conf

You can also stop ``searchd``::

    $ searchd --stop -c sphinx.conf

This method not only lets you maintain a running Sphinx instance that doesn't
get wiped out by the tests, but also lets you see some very interesting output
from Sphinx about indexing rate and statistics.
