==============
Vendor Library
==============

The vendor library is the easiest way to manage pure-Python dependencies. It
contains the source code for all the libraries Kuma depends on.


Getting the Vendor Library
==========================

Getting the vendor library is easy. In your Kuma clone, just type::

    $ git clone --recursive git://github.com/mozilla/kuma-lib.git vendor

Git will clone the repository and all its submodules.


Updating the Vendor Library
===========================

From time to time we need to update libraries, either for new versions of
libraries or to add a new library. There are two ways to do this. The easiest