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

.. DANGER::
   We are moving all libraries from vendor to pip. Any pull requests with
   vendor updates will be rejected unless it is an emergency situation.

From time to time we need to update libraries, either for new versions of
libraries or to add a new library. There are two ways to do that.


Updating a Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the library is in ``vendor/src``, it was pulled directly from version
control, and if that version control was git, update the submodule like so::

    $ cd vendor/src/$LIBRARY
    $ git fetch origin
    $ git checkout <REFSPEC>
    $ cd ../..
    $ git add src/$LIBRARY
    $ git ci -m "Updating $LIBRARY"

Just like updating any other git submodule.


Adding a New Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technically this can be done with ``pip install --no-install`` but we do this::

    $ cd vendor/src
    $ git clone git://<repo>
    $ cd ../..
    $ ./addsubmodules.sh
    $ vim kuma.pth  # Add the new library's path
    $ git add kuma.pth
    $ git ci -m "Adding $LIBRARY"


Using PyPI
----------

Follow `the playdoh instructions for non-git based repos
<http://playdoh.readthedocs.org/en/latest/packages.html#non-git-based-repos-hg-cvs-tarball>`_, replacing
`vendor-local` with `vendor`.


Requirements Files
==================

We are in the process of moving all our libraries to pip requirements.

We still maintain requirements files in ``requirements/``. Sometimes people
will use these to install the requirements in a virtual environment. When you
update the vendor repo, you should make sure to update version numbers (if
necessary) in the requirements files.
