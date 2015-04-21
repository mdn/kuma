==========================
Running Kuma with mod_wsgi
==========================


Requirements
============

* See :doc:`the installation docs <installation>`.
* `Apache HTTP server <http://httpd.apache.org/>`_
* mod_rewrite
* mod_headers
* mod_expires
* `mod_wsgi <http://code.google.com/p/modwsgi/>`_
* **Not** ``mod_python``! It is incompatible with ``mod_wsgi``.


Overview
========

Setting up Kuma to run as a WSGI application is fairly straightforward. You
will need to install the requirements and clone the vendor repo as described in
the :doc:`installation docs <installation>`.

There are 3 steps once Kuma is installed:

* Set the document root.
* Set up aliases.
* Some file permissions.
* Set up WSGI itself.


Apache Modules
--------------

Most of the Apache modules are part of a default Apache install, but may need
to be activated. If they aren't installed, all of them, including ``mod_wsgi``
should be installable via your favorite package manager.


WSGI Configuration
------------------

In the Apache config (or ``<VirtualHost>``) you will need the following:

*Note that values may be slightly different.*

::

    DocumentRoot /path/to/kuma/webroot/

    <Directory "/path/to/kuma/webroot/">
        Options +FollowSymLinks
    </Directory>

    Alias /media/ "/path/to/kuma/media/"
    Alias /admin-media/ \
        "/path/to/kuma/vendor/src/django/django/contrib/admin/media/"

    WSGISocketPrefix /var/run/wsgi

    WSGIDaemonProcess kuma processes=8 threads=1 \
        maximum-requests=4000
    WSGIProcessGroup kuma

    WSGIScriptAlias /k "/path/to/kuma/wsgi/kuma.wsgi"

``WSGISocketPrefix``:
    May or may not be necessary. It was for me.

``WSGIDaemonProcess``:
    ``processes`` should be set to the number of cores.
    ``threads`` should probably be left at 1. ``maximum-requests`` is good at
    between 4000 and 10000.

``WSGIScriptAlias``:
    Will make Kuma accessible from ``http://domain/k``, and we use rewrites
    in ``webroot/.htaccess`` to hide the ``/k``. This will change soon, and the
    ``.htaccess`` file won't be necessary.

The ``Alias`` directives let Kuma access its CSS, JS, and images through
Apache, reducing the load on Django.


Configuration
-------------

Most of our ``settings.py`` is under version control, but can be overridden
in a file called ``.env`` in the root of the kuma directory (the same
place as ``README.rst``).

File Permissions
================

To upload files, the webserver needs write access to ``media/uploads`` and all
its subdirectories. The directories we currently use are::

    media/uploads
    media/uploads/avatars
    media/uploads/images
    media/uploads/images/thumbnails
    media/uploads/gallery/images
    media/uploads/gallery/images/thumbnails
    media/uploads/gallery/videos
    media/uploads/gallery/videos/thumbnails

``media/uploads`` and its subdirectories should never be added to version
control, as they are installation-/content-specific.

Product Details JSON
--------------------

Some people have issues with ``django-mozilla-product-details`` and file
permissions. The management command ``manage.py update_product_details`` writes
a number of JSON files to disk, and the webserver then needs to read them.

If you get file system errors from ``product_details``, make sure the files are
readable by the webserver (should be by default) and the directory is readable
and executable.

By default, ``product_details`` stores the JSON files in::

    vendor/src/django-mozilla-product-details/product_details/json

This is configurable. If you have multiple web servers, they should share this
data. You can set the ``PROD_DETAILS_DIR`` variable in ``.env`` to
a different path, for example on NFS.

Debugging
=========

Debugging via WSGI is a little more interesting than via the dev server. One
key difference is that you **cannot** use ``pdb``. Writing to ``stdout`` is not
allowed within the WSGI process, and will result in a Internal Server Error.

There are three relevant cases for debugging via WSGI (by which I mean, where
to find stack traces):

Apache Error Page
-----------------

So you've got a really bad error and you aren't even seeing the Kuma error
page! This is usually caused by an uncaught exception during the WSGI
application start-up. Our `WSGI script
<https://github.com/mozilla/kuma/blob/master/wsgi/kuma.wsgi>`_ tries to run
all the initial validation that the dev server runs, to catch these errors
early.

So where *is* the stack trace? You'll need to look in your Apache error logs.
Where these are is OS-dependent, but a good place to look is
``/var/log/httpd``. If you are using SSL, also check the SSL ``VirtualHost``'s
logs, for example ``/var/log/httpd/ssl_error_log``.

With ``DEBUG=True``
-------------------

With ``DEBUG = True`` in your ``.env`` (also the default for local
development), you will see a stack trace in the browser on error.
Problem solved!

With ``DEBUG=False``
--------------------

With ``DEBUG = False`` in your ``.env``, you'll see our Server
Error message. You can still get stack traces, though, by setting the
``ADMINS`` variable in ``.env``::

    ADMIN_EMAILS = 'my@email.address'

Django will email you the stack trace. Provided you've set up :doc:`email
<email>`.
