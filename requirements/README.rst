Kuma requirements
=================

The files define the third-party libraries needed for running and developing
Kuma.  The files are:

* ``constraints.txt`` - Requirements for our requirements.
* ``default.txt`` - Requirements for production and deployment.
* ``default_and_test.txt`` - Requirements production, deployment, and test.
* ``docs.txt`` - Requirements for building docs in `Read the Docs`_.
* ``dev.txt`` - Requirements for Docker or native development.
* ``test.txt`` - Requirements to run functional tests.

These files have two audiences:

* **Computers** need to know what packages to install. We use exact versions
  and hashes to ensure each environment installs the same packages.
* **Developers** need to integrate and update packages. Often, these tasks
  include reading documentation and source code.  We organize packages by task,
  split primary packages from support packages, and include URLs to get more
  information.

Hash-Checking Mode
------------------
For the production and development requirements, we use pip 8.x's
`Hash-Checking Mode`_, which checks that downloaded packages match one of the
given hashes, ensuring that there are no man-in-the-middle attacks.  When
hashes are used, all requirements, including those installed as dependencies,
require hashes.

To help gather packages and add hashes, we use hashin_, which computes the
hashes and updates requirement files. For example, to install a particular
Django version::

    hashin Django==1.8.13 -r requirements/default.txt

Or, to update to the latest version of a package::

    hashin django-allauth -r requirements/default.txt

It is still up to you to install the requirements, and to specify any
requirements of your requirements, in ``constraints.txt``.

Requirements format
-------------------
Requirements files should include a summary explaining why a requirement
is used, and URLs for more information. For example::

    # Refresh stale cache items asynchronously
    # Code: https://github.com/codeinthehole/django-cacheback
    # Changes: https://github.com/codeinthehole/django-cacheback/blob/master/CHANGELOG.rst
    # Docs: http://django-cacheback.readthedocs.io/en/latest/
    django-cacheback==1.0 \
        --hash=sha256:8feaa8df6cbe23e1fca5d858f518a235442a8ddc4aefb5be0846692c69d65a8e \
        --hash=sha256:2fc21e0ed78ee8e4cc07ac2c5936b27f956c99c81fc4f965e96fb27171180819

The purpose of the comment is:

* Summarize the purpose of the requirement, to save an internet search.
* Describe how the requirement is used in Kuma.
* Help the maintainer to prioritize upgrading requirements.
* Give a hint on exploratory tests to ensure upgrades do not break things.

The additional links (which we started adding in 2018) help maintainers dive
deeper. When possible, include the links to:

* **Code**, such as the main Github repository.
* **Changes**, such as a documentation page or file in the repo that says what
  changes with each release. Use ``Changes`` for the key, even when the project
  calls it something else, like changelog or release notes.
* **Docs**, such as documentation hosted on ReadTheDocs. If the README on the
  GitHub repository is the only documentation, this can be skipped.

Within a requirements file, requirements should be alphabetical.

Constraints
-----------
``constraints.txt`` contains requirements of requirements, using pip 7.1's
`constraints feature`_.  These files are installed if needed, and not if not
needed. This means if a requirement changes its own requirements, unneeded
libraries are not installed. It also helps separate the requirements we need
from the ones we are using indirectly.

This file requires hashes. The format is to group requirements by the package
that requires them, and then alphabetically with links, such as::

    #
    # mock
    #
    # Backport of function signature features from Python 3.3's inspect
    # Code: https://github.com/aliles/funcsigs
    # Changes: https://github.com/aliles/funcsigs/blob/master/CHANGELOG
    # Docs: http://funcsigs.readthedocs.io/en/latest/
    funcsigs==0.4 \
        --hash=sha256:ff5ad9e2f8d9e5d1e8bbfbcf47722ab527cf0d51caeeed9da6d0f40799383fde \
        --hash=sha256:d83ce6df0b0ea6618700fe1db353526391a8a3ada1b7aba52fed7a61da772033
    # Automation for setuptools
    # Code: https://github.com/openstack-dev/pbr
    # Changes: https://docs.openstack.org/pbr/latest/user/history.html
    # Docs: https://docs.openstack.org/pbr/latest/
    pbr==1.8.1 \
        --hash=sha256:46c8db75ae75a056bd1cc07fa21734fe2e603d11a07833ecc1eeb74c35c72e0c \
        --hash=sha256:e2127626a91e6c885db89668976db31020f0af2da728924b56480fc7ccf09649

If a constraint is needed in several requirements, there's a section at the top
for them. All constraints, for production and development, go in this file.

The tool pipdeptree_ is useful for determining dependencies between packages.
Grepping the source code is needed to determine if a package is used directly
or indirectly.

For packages that are both dependencies and used directly, it's up to the
developer to determine where it goes. The only rule is to not break production
or deployment. Use comments to justify placement as needed.

Testing new requirements in Docker
----------------------------------

The python dependencies are installed in a "base" image, and to test new requirements
locally use the following command to build a new base image with the "latest" tag, for
use with the existing docker-compose files::

    make build-base VERSION=latest

To start using this image::

    docker-compose stop    # if necessary
    docker-compose up -d

To update your local base image with the latest version built from the master
branch, run::

    docker-compose pull web


Future
------
* Add ``Code``, ``Changes``, and ``Docs`` links to existing requirements
* Remove unused requirements, and refactor code to eliminate unmaintained
  requirements.
* Requirements files may be further split into roles, so that there are minimal
  requirements installed for running the web service, the async task workers,
  building static files in a deployment, etc.

.. _Read the Docs: https://readthedocs.org
.. _Hash-Checking mode: http://pip.readthedocs.io/en/stable/reference/pip_install/#hash-checking-mode
.. _hashin: https://github.com/peterbe/hashin
.. _constraints feature: http://pip.readthedocs.io/en/stable/user_guide/#constraints-files
.. _pipdeptree: https://github.com/naiquevin/pipdeptree
