==============
Vendor Library
==============

The vendor library is the easiest way to manage pure-Python dependencies. It
contains the source code for all the library Kuma depends on.


Getting the Vendor Library
==========================

Getting the vendor library is easy. In your Kuma clone, just type::

    $ git clone --recursive git://github.com/mozilla/kuma-lib.git vendor

Git will clone the repository and all its submodules.


Updating the Vendor Library
===========================

From time to time we need to update libraries, either for new versions of
libraries or to add a new library. There are two ways to do that. The easiest
and prefered way is pure git.


Using Git Submodules
--------------------

Using git submodules is prefered because it is much easier to maintain, and it
keeps the repository size small. Upgrading is as simple as updating a
submodule.


Updating a Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the library is in ``vendor/src``, it was pulled directly from version
control, and if that version control was git, updating the submodule is as easy
as::

    $ cd vendor/src/$LIBRARY
    $ git fetch origin
    $ git checkout <REFSPEC>
    $ cd ../..
    $ git add src/$LIBRARY
    $ git ci -m "Updating $LIBRARY"

Easy! Just like updating any other git submodule.


Adding a New Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technically this can be done with ``pip install --no-install`` but there's an
even easier method when installing a new library from a git repo::

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

We still maintain requirements files in ``requirements/``. Sometimes people
will use these to install the requirements in a virtual environment. When you
update the vendor repo, you should make sure to update version numbers (if
necessary) in the requirements files.
