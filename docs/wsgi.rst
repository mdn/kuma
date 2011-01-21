=============================
Running Kitsune with mod_wsgi
=============================


Requirements
============

* See `the installation docs <installation.rst>`_.
* `Apache HTTP server <http://httpd.apache.org/>`_
* mod_rewrite
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
* Set up WSGI itself.


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
