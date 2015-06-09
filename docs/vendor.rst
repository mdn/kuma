==============
Vendor Library
==============

The ``vendor`` directory contains the source code for Kuma libraries.

Getting the Vendor Libraries
============================

To get the ``vendor`` libraries in your Kuma clone, ::

    $ git submodule update --init

Git will fetch all the ``vendor`` submodules.

Updating the Vendor Library
===========================

.. warning::

   We are moving all libraries from vendor to pip.

We maintain requirements files in ``requirements/`` and so they **MUST**
be updated when adding or updating any vendored dependency as well.

    The requirements files are **THE ONLY SOURCE OF TRUTH** for versions.

From time to time we need to update libraries, either for new versions of
libraries or to add a new library. There are two ways to do that.

Updating a Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the library is in ``vendor/src``, it was pulled directly from version
control, and if that version control was git, update the submodule like so::

    $ cd vendor/src/$LIBRARY
    $ git fetch origin
    $ git checkout <branch or tag>
    $ cd ../../..
    $ vim requirements/source.txt  # Update library to requirements file
    $ git add requirements/source.txt vendor/src/$LIBRARY
    $ git ci -m "Updating $LIBRARY"

Just like updating any other git submodule.

Adding a New Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technically this can be done with ``pip install --no-install`` but we do this::

    $ git submodule add git://<repo> vendor/src/$LIBRARY
    $ cd vendor/src/$LIBRARY
    $ git checkout <branch or tag>
    $ cd ../../..
    $ vim vendor/kuma.pth  # Add the new library's path
    $ vim requirements/source.txt  # Add new library to requirements file
    $ git add requirements/source.txt vendor/kuma.pth vendor/src/$LIBRARY
    $ git ci -m "Adding $LIBRARY"

Using PyPI
----------

Update the ``requirements/packages.txt`` file with the package you'd like to
add. To add the package to the vendored packages do::

    $ cd vendor
    $ make packages
