=============
Documentation
=============

Generating Documentation
------------------------
This documentation is generated and published at
`Read the Docs`_ whenever the master branch is updated.

To generate locally, install the packages in ``requirements/docs.txt``
(inside the development VM or in a new `virtualenv`_ on the host system),
and run::

    cd docs
    make html

This will generate the documents with the index at
``docs/_build/html/index.html``.


Updating the MDN Sphinx Theme
-----------------------------
The documentation uses a Sphinx theme generated from the MDN templates:

https://github.com/mdn/sphinx-theme

If this theme is checked out, the in-development theme can be used to generate
the local documentation::

    pip install -e /path/to/sphinx-theme
    cd docs
    make html

The theme's template can be regenerated with::

    ./manage.py generate_sphinx_template > /path/to/sphinx-theme/mdn_theme/mdn/layout.html

To use the new theme in the public documentation,

1. Commit and merge the new template to ``sphinx-theme``
2. Tag and publish a new version of ``mdn-sphinx-theme`` to PyPI_
3. Update ``requirements/docs.txt`` in ``kuma``, merge to master

.. _`Read the Docs`: https://kuma.readthedocs.io/en/latest/
.. _PyPI: https://pypi.python.org/pypi/mdn-sphinx-theme
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
