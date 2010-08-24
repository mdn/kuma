==============
Vendor Library
==============

If you don't want to go mucking about with a virtual environment, or you
want to share compiled packages between several installations, you can use
the kitsune-lib vendor library. This is just a git repo with all our
dependencies in it.

The vendor library includes all the dependencies for both production and
development environments.


Using the Vendor Library
========================

Check out the library like so::

    git clone --recursive git://github.com/jsocol/kitsune-lib.git ./vendor

You'll want to stick that right in the Kitsune check out. Then all that's
left is to install the compiled packages::

    pip install -r requirements/compiled.txt

You may need to ``sudo`` that, depending on your environment.
