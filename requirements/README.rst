Kuma Requirements
=================

The files define the third-party libraries needed for running and developing
Kuma.  The files are:

* ``constraints.txt`` - Requirements for our requirements
* ``default.txt`` - Requirements for production and deployment
* ``docs.txt`` - Requirements for building docs in `Read the Docs`_
* ``local.txt`` - Requirements for local development and tests
* ``travis.txt`` - Requirements for testing in TravisCI

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

    hashin Django==1.8.13 requirements/default.txt

Or, to update to the latest version of a package::

    hashin django-allauth requirements/default.txt

It is still up to you to install the requirements, and to specify any
requirements of your requirements, in ``constraints.txt``.

Constraints
-----------
``constraints.txt`` contains requirements of requirements, using pip 7.1's
`constraints feature`_.  These files are installed if needed, and not if not
needed. This means if a requirement changes its own requirements, unneeded
libraries are not installed. It also helps separate the requirements we need
from the ones we are using indirectly.

This file requires hashes. The format is to group requirements by the package
that requires them, and then alphabetically, such as::

    # mock
    funcsigs==0.4 \
        --hash=sha256:ff5ad9e2f8d9e5d1e8bbfbcf47722ab527cf0d51caeeed9da6d0f40799383fde \
        --hash=sha256:d83ce6df0b0ea6618700fe1db353526391a8a3ada1b7aba52fed7a61da772033
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

Requirements Format
-------------------
The ``default.txt`` and ``local.txt`` should include a short comment
explaining why a requirement is used. For example::

    # Refresh stale cache items asynchronously
    django-cacheback==1.1 \
        --hash=sha256:ba7dc1525de6b6f44d13f6e5b6b93ca7a9ef0ca560315872fe40f044b7b59e95

The purpose of the comment is:

* Summarize the purpose of the requirement, to save an internet search
* Describe how the requirement is used in Kuma
* Help maintainer to prioritize upgrading requirements
* Give a hint on exploratory tests needed to ensure upgrades do not break things

Within a requirements file, requirements should be alphabetical.

Future
------
* Remove unused requirements, and refactor code to eliminate unmaintained
  requirements.
* Requirements files may be further split into roles, so that there are minimal
  requirements installed for running the web service, the async task workers,
  building static files in a deployment, etc.
* Alternatively, switching to Docker may mean a union of all requirements are
  installed in a base image.
* As pip 8.x is more widely supported by default, switch other requirements
  files to use hashes.

.. _Read the Docs: https://readthedocs.org
.. _Hash-Checking mode: http://pip.readthedocs.io/en/stable/reference/pip_install/#hash-checking-mode
.. _hashin: https://github.com/peterbe/hashin
.. _constraints feature: http://pip.readthedocs.io/en/stable/user_guide/#constraints-files
.. _pipdeptree: https://github.com/naiquevin/pipdeptree

