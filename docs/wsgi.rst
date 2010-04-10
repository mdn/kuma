.. _wsgi:

=============================
Running Kitsune with mod_wsgi
=============================


Requirements
------------

* See ``docs/installation.rst``.
* `virtualenv <http://pypi.python.org/pypi/virtualenv>`_
* `Apache HTTP server <http://httpd.apache.org/>`_
* `mod_wsgi <http://code.google.com/p/modwsgi/>`_
* **Not** ``mod_python``! It is incompatible with ``mod_wsgi``.


Overview
--------

Kitsune will require two seperate virtual environments for ``mod_wsgi`` to
run correctly. One should be kept empty, and is used to ensure no system
packages sneak into the Kitsune virtualenv.

Kitsune should be cloned into a directory named ``kitsune`` outside of the
web root for the server or ``<VirtualHost>``. It will be aliased to the
correct location.
    

WSGI Configuration
------------------

In the Apache config (or ``<VirtualHost>``) you will need the following:

*Note that values may be slightly different.*

::

    WSGIPythonHome /path/to/empty/virtualenv
    WSGISocketPrefix /var/run/wsgi

    WSGIDaemonProcess kitsune processes=8 threads=1 \
        python-path=/home/james/.virtualenvs/kitsune/lib/python2.6/site-packages
    WSGIProcessGroup kitsune

    WSGIScriptAlias /k "/path/to/kitsune/wsgi/kitsune.wsgi"

    Alias /media/ "/path/to/kitsune/media/"

``WSGIPythonHome`` points to an empty, pristine virtual environment.

``WSGISocketPrefix`` may or may not be necessary. It was for me.

``WSGIDaemonProcess``: ``processes`` should be set to the number of cores.
``threads`` should probably be left at 1. ``python-path`` is set to the
``site-packages`` directory of the Kitsune virtual environment.

``WSGIScriptAlias`` will make Kitsune accessible from ``http://domain/k``,
and we use rewrites in ``.htaccess`` to hide the ``/k``. *This may change
when we remove the TikiWiki portion of SUMO.*

The ``Alias`` lets Kitsune access its CSS, JS, and images through Apache,
reducing the load on Django.


Configuration
-------------

Most of our ``settings.py`` is under version control, but can be overridden
in a file called ``settings_local.py`` in the base of the app (the same
place as ``settings.py``). You can see example settings in 
``/docs/settings/settings_local.prod.py``:

.. literalinclude:: /settings/settings_local.prod.py
