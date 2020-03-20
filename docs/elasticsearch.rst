======
Search
======
Kuma uses Elasticsearch_ to power its on-site search.

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch

Installed version
=================
Elasticsearch `releases new versions often`_. They release a new minor version
(for example, 6.2.0, 6.3.0) every 30 to 90 days, and support the most recent
minor version. They release a major version (5.0.0, 6.0.0) every 12 to 18
months, and support the last minor version of the previous major release
(for example, 2.4.x supported until 6.x is released, 5.6.x supported until 7.x
is released).

Kuma's goal is to update to the last minor version of the previous major
release, so we expect to update every 12 to 18 months. Kuma is running on
ElasticSearch 6.7.1 in development and production, which is planned to be
supported until September 2020.

The Kuma search tests use the configured Elasticsearch, and can be run inside
the ``web`` Docker container to confirm the engine works::

    py.test kuma/search/

.. _releases new versions often: https://www.elastic.co/support/eol

.. _indexing-documents:

Indexing documents
==================
To see search results, you will need to index the documents.

Using the Admin
---------------
This process works both in a development environment and in production:

- Open the Django admin search index list view. On Docker, this is located
  at http://localhost.org:8000/admin/search/index/.

- On the search index list, select the checkbox next to the each index. Then
  select "Delete selected Indexes" from the dropdown menu.

- Inside the ``web`` Docker container::

    docker-compose exec web ./manage.py reindex

- Refresh the search index list until the "populated" field changes to a green
  checkbox image.  In production, you will also get an email notifying you when
  the index is populated.

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
Inside the ``web`` Docker container::

    ./manage.py reindex

This will populate and activate the fallback index "main_index". It will be
overwritten when the search tests run.

Search Filters
==============
The search interface uses Filters and Filter Groups to determine what results
are shown. Currently, the only active Filter Group is "Topics". The Filters
collect documents by tag. For example, the Filter "Add-ons & Extensions"
collects all documents tagged with "Add-ons", "Extensions", "Plugins", or
"Themes". Most filters have a single associated tag. For example, the "CSS"
filter collects the documents with the "CSS" tag.

Filter and Filter Groups are defined in the database, but the names are
shown to users. The names of these objects (enabled and disabled) are
listed in ``kuma/search/names.py``, and marked for translation. To generate
this file, run this command against the production database, and copy the
output to ``names.py``::

    ./manage.py generate_search_names

The sample database contains the active subset of Filters and Filter Groups.
This won't match the production database, and so the development environment
should not be used to generate ``kuma/search/names.py``.
