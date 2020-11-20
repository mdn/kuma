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
Indexing is done outside Kuma. It's done by the Deployer in Yari.
