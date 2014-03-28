======
Search
======

Kuma uses `Elasticsearch <http://www.elasticsearch.org>`_ to power its
on-site search facility.

Elasticsearch search gives us a number of advantages over MySQL's full-text
search or Google's site search.

* Much faster than MySQL.
  * And reduces load on MySQL.
* We have total control over what results look like.
* We can adjust searches with non-visible content.
* We don't rely on Google reindexing the site.
* We can fine-tune the algorithm ourselves.

Installing Elasticsearch Search
===============================

We currently require **Elasticsearch 0.90.9**. You may be able to install this
from a package manager like yum, aptitude, or brew.

If not, you can easily `download <http://www.elasticsearch.org/download/>`_ the
source and compile it. Generally all you'll need to do is::

    $ cd elasticsearch-0.90.9
    $ bin/elasticsearch -f

Then run the Kuma search tests::

    $ ./manage.py test -s --noinput --logging-clear-handlers search

If the tests pass, everything is set up correctly!

Using Elasticsearch
===================

Having Elasticsearch installed will allow the search tests to run, which may be
enough. But you want to work on or test the search app, you will probably need
to actually see search results!

The Easy, Sort of Wrong Way
---------------------------

The easiest way to start Elasticsearch for testing is::

    $ cd path/to/elasticsearch-0.90.9
    $ bin/elasticsearch -f

Then from the Kuma source code path::

    $ ./manage.py reindex

If you need to update the search indexes::

    $ ./manage.py reindex

While this method is very easy, you will need to reindex after any time you run
the search tests, as they will overwrite the data files Elasticsearch uses.

The Ellaborate, Kinda Proper Way
--------------------------------

Assuming you're running the full stack with ``foreman start`` (or any other
way that makes sure the :doc:`Celery <celery>` workers run) there is a better
way:

- Open the Django admin UI under http://127.0.0.1:8000/admin/search/index/ or
  https://developer-local.allizom.org/admin/search/index/ if you're using
  Vagrant.

- Add a search index by clicking on the "Add index" button in the top right
  corner, safe it by clicking on the same button in the lower right corner to
  safe it to the database.

- On the search index list view again, select the just created index (the top
  most) and select "Populate search index with Celery task" from the actions
  dropdown below.

- Once the population is ready the "populated" field with show up as a green
  checkbox image. You'll also get an email (probably via the console if you're
  developing kuma locally) notifying you of the completion.

- To actually enable that newly created search index you have to promote it
  now. On the search index list view again, select the just created index (the top
  most) and select "Promote search index" from the actions dropwdown below.

- Once the search index is promoted the "promoted" and the "is current index"
  field will show up as a green checkbox image. The index is now live.

Similarly you can also demote a search index and it will automatically fall
back to the previously created index (by created date). That helps to figure
out issues in production and should allow for a smooth deployment of search
index changes. It's recommmended to keep a few search indexes around just in
case.

If no index is created in the admin UI the fallback "main_index" index will be
used instead.

.. warning::

   If you delete any of the search indexes in the admin interface they will be
   deleted on Elasticsearch as well.
