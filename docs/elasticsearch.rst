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

We currently require **Elasticsearch 1.3.x** and automatically install it
as part of the :doc:`Vagrant provisioning <installation>`.

Then run the Kuma search tests::

    $ py.test kuma/search/

If the tests pass, everything is set up correctly!

Using Elasticsearch
===================

Having Elasticsearch installed will allow the search tests to run, which may be
enough. But you want to work on or test the search app, you will probably need
to actually see search results!

The Elaborate, Kinda Proper Way
-------------------------------

Assuming you're running the full stack with ``foreman start`` (or any other
way that makes sure the :doc:`Celery <celery>` workers run) there is a better
way:

- Open the Django admin UI under
  https://developer-local.allizom.org/admin/search/index/.

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

The Easy, Sort of Wrong Way
---------------------------

From the Kuma source code path::

    $ ./manage.py reindex

If you need to update the search indexes run the command again.

While this method is very easy, you will need to reindex after any time you run
the search tests, as they will overwrite the data files Elasticsearch uses.
