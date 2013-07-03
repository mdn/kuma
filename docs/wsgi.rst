.. This Source Code Form is subject to the terms of the Mozilla Public
.. License, v. 2.0. If a copy of the MPL was not distributed with this
.. file, You can obtain one at http://mozilla.org/MPL/2.0/.

=============================
Running Kitsune with mod_wsgi
=============================


Requirements
============

* See `the installation docs <installation.rst>`_.
* `Apache HTTP server <http://httpd.apache.org/>`_
* mod_rewrite
* mod_headers
* mod_expires
* `mod_wsgi <http://code.google.com/p/modwsgi/>`_
* **Not** ``mod_python``! It is incompatible with ``mod_wsgi``.


Overview
========

Setting up Kitsune to run as a WSGI application is fairly straightforward. You
will need to install the requirements and clone the vendor repo as described in
`installation.rst <installation.rst>`_.

There are 3 steps once Kitsune is installed:

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

    DocumentRoot /path/to/kitsune/webroot/

    <Directory "/path/to/kitsune/webroot/">
        Options +FollowSymLinks
    </Directory>

    Alias /media/ "/path/to/kitsune/media/"
    Alias /admin-media/ \
        "/path/to/kitsune/vendor/src/django/django/contrib/admin/media/"

    WSGISocketPrefix /var/run/wsgi

    WSGIDaemonProcess kitsune processes=8 threads=1 \
        maximum-requests=4000
    WSGIProcessGroup kitsune

    WSGIScriptAlias /k "/path/to/kitsune/wsgi/kitsune.wsgi"

``WSGISocketPrefix``:
    May or may not be necessary. It was for me.

``WSGIDaemonProcess``:
    ``processes`` should be set to the number of cores.
    ``threads`` should probably be left at 1. ``maximum-requests`` is good at
    between 4000 and 10000.

``WSGIScriptAlias``:
    Will make Kitsune accessible from ``http://domain/k``, and we use rewrites
    in ``webroot/.htaccess`` to hide the ``/k``. This will change soon, and the
    ``.htaccess`` file won't be necessary.

The ``Alias`` directives let Kitsune access its CSS, JS, and images through
Apache, reducing the load on Django.


Configuration
-------------

Most of our ``settings.py`` is under version control, but can be overridden
in a file called ``settings_local.py`` in the base of the app (the same
place as ``settings.py``). You can see example settings in
`docs/settings/settings_local.prod.py <settings/settings_local.prod.py>`_:

.. literalinclude:: settings/settings_local.prod.py


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
data. You can set the ``PROD_DETAILS_DIR`` variable in ``settings_local.py`` to
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

So you've got a really bad error and you aren't even seeing the Kitsune error
page! This is usually caused by an uncaught exception during the WSGI
application start-up. Our `WSGI script <../wsgi/kitsune.wsgi>`_ tries to run
all the initial validation that the dev server runs, to catch these errors
early.

So where *is* the stack trace? You'll need to look in your Apache error logs.
Where these are is OS-dependent, but a good place to look is
``/var/log/httpd``. If you are using SSL, also check the SSL ``VirtualHost``'s
logs, for example ``/var/log/httpd/ssl_error_log``.


With ``DEBUG=True``
-------------------

With ``DEBUG = True`` in your ``settings_local.py``, you will see a stack trace
in the browser on error. Problem solved!


With ``DEBUG=False``
--------------------

With ``DEBUG = False`` in your ``settings_local.py``, you'll see our Server
Error message. You can still get stack traces, though, by setting the
``ADMINS`` variable in ``settings_local.py``::

    ADMINS = (
        ('me', 'my@email.address'),
    )

Django will email you the stack trace. Provided you've set up `email
<email.rst>`_.


Reloading WSGI
==============

WSGI keeps Python and Kitsune running in an isolated process. That means code
changes aren't automatically reflected on the server. In most default
configurations of ``mod_wsgi``, you can simply do this::

    touch wsgi/kitsune.wsgi

That will cause the WSGI process to reload.
