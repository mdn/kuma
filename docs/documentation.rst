=============
Documentation
=============
This documentation is generated and published at
`Read the Docs`_ whenever the master branch is updated.

GitHub can render our ``.rst`` documents as ReStructuredText_, which is
close enough to Sphinx_ for most code reviews, without features like links
between documents.

It is occasionally necessary to generate the documentation locally. It is
easiest to do this with a virtualenv_ on the host system, using Docker only to
regenerate the MDN Sphinx template.  If you are not comfortable with that style
of development, it can be done entirely in Docker using ``docker-compose``.

.. _`Read the Docs`: https://kuma.readthedocs.io/en/latest/
.. _ReStructuredText: https://en.wikipedia.org/wiki/ReStructuredText
.. _Sphinx: https://en.wikipedia.org/wiki/Sphinx_(documentation_generator)
.. _virtualenv: https://virtualenv.pypa.io/en/stable/

Generating documentation
------------------------
Sphinx uses a ``Makefile`` in the ``docs`` subfolder to build documentation in
several formats.  MDN only uses the HTML format, and the generated document
index is at ``docs/_build/html/index.html``.

To generate the documentation in a virtualenv on the host machine, first
install the requirements::

    pip install -r docs/requirements.txt

Then switch to the ``docs`` folder to use the ``Makefile``::

    cd docs
    make html
    python -m webbrowser file://${PWD}/_build/html/index.html


To generate the documentation with Docker::

    docker-compose run --rm web sh -c "\
      python -m venv /tmp/.venvs/docs && \
      . /tmp/.venvs/docs/bin/activate && \
      pip install -r /app/docs/requirements.txt && \
      cd /app/docs && \
      make html"
    python -m webbrowser file://${PWD}/docs/_build/html/index.html

A ``virtualenv`` is required, to avoid a ``pip`` bug when changing the version
of a system-installed package.
