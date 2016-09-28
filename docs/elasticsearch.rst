======
Search
======
Kuma uses Elasticsearch_ to power its on-site search.

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch

Installed Version
=================
Elasticsearch `releases new versions often`_, and Kuma is slow to upgrade.  The
Vagrant and Docker environments use 1.7, but production is older.

The Kuma search tests use the configured Elasticsearch, and can be run inside
the Vagrant VM or the ``web`` Docker container to confirm the engine works::

    py.test kuma/search/

.. _releases new versions often: https://en.wikipedia.org/wiki/Elasticsearch#History

Indexing Documents
==================
To see search results, you will need to index the documents.

Using the Admin
---------------
This process works both in a development environment and in production:

- Open the Django admin search index list view
  (on Docker, http://localhost:8000/admin/search/index/,
  and on Vagrant, https://developer-local.allizom.org/admin/search/index/).

- Add a search index by clicking on the "Add index" button in the top right
  corner. Optionally name it, or leave it blank to generate a valid name based
  on the time. Click the "SAVE" button in the lower right corner.

- On the search index list, select the checkbox next to the newly created index
  (the top most) and select "Populate selected search index via Celery" from
  the Action dropdown menu. Click "Go" to start indexing asynchronously.

- Refresh the search index list until the "populated" field changes to a green
  checkbox image.  You will also get an email, if the environment is set up for
  it (the default Docker environment is not), notifying you of the completion.

- Select the checkbox next to the populated index, then choose "Promote
  selected search index to current index" in the actions dropdox. Click "Go"
  to promote the index.

- All three fields will be green checkboxes (promoted, populates, and "is current index?").
  The index is live, and will be used for site search.

Similarly you can also demote a search index and it will automatically fall
back to the previously created index (by created date). That helps to figure
out issues in production and should allow for a smooth deployment of search
index changes. It's recommended to keep a few search indexes around just in
case.

If no index is created in the admin UI the fallback "main_index" index will be
used instead.

When you delete a search index in the admin interface, it is deleted on
Elasticsearch as well.

Using the shell
---------------
Inside the Vagrant VM or ``web`` Docker container::

    ./manage.py reindex

This will populate and activate the fallback index "main_index".  It will be
overwritten when the search tests run.
