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

Sometimes a library isn't in a git repository. It, sadly, happens. Maybe you
can find a git mirror? If not, it might as well be installed from PyPI.


Updating a Library from PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The easiest way to update a library from PyPI is to remove it completely and
then install the new version.

::

    $ cd vendor/packages
    $ git rm -r $LIBRARY
    $ cd ..
    $ git ci -m "Removing version $VERSION of $LIBRARY"
    $ cd ..

After removing the old version, go ahead and install the new one::

    $ pip install --no-install --build=vendor/packages --src=vendor/src -I $LIBRARY

Finally, add the new library to git::

    $ cd vendor
    $ git add packages
    $ git ci -m "Adding version $VERSION of $LIBRARY"

**Caveat developer!** Sometimes a library has dependencies that are already
installed in the vendor repo. You may need to remove several of them to make
everything work easily.


Adding a Library from PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding a new library from PyPI is easy using pip::

    $ pip install --no-install --build=vendor/packages --src=vendor/src -I $LIBRARY
    $ cd vendor
    $ git add packages
    $ vim kuma.pth  # Add any new libraries' paths.
    $ git ci -m "Adding $LIBRARY"

Make sure you add any dependencies from the new library, as well.


Requirements Files
==================

We still maintain requirements files in ``requirements/``. Sometimes people
will use these to install the requirements in a virtual environment. When you
update the vendor repo, you should make sure to update version numbers (if
necessary) in the requirements files.
