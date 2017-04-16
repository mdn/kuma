===============================================
 django-celery - Celery Integration for Django
===============================================

.. image:: http://cloud.github.com/downloads/ask/celery/celery_128.png

:Version: 2.5.5
:Web: http://celeryproject.org/
:Download: http://pypi.python.org/pypi/django-celery/
:Source: http://github.com/ask/django-celery/
:Keywords: celery, task queue, job queue, asynchronous, rabbitmq, amqp, redis,
  python, django, webhooks, queue, distributed

--

django-celery provides Celery integration for Django; Using the Django ORM
and cache backend for storing results, autodiscovery of task modules
for applications listed in ``INSTALLED_APPS``, and more.

.. contents::
    :local:

Using django-celery
===================

To enable ``django-celery`` for your project you need to add ``djcelery`` to
``INSTALLED_APPS``::

    INSTALLED_APPS += ("djcelery", )

then add the following lines to your ``settings.py``::

    import djcelery
    djcelery.setup_loader()

Everything works the same as described in the `Celery User Manual`_, except you
need to invoke the programs through ``manage.py``:

=====================================  =====================================
**Program**                            **Replace with**
=====================================  =====================================
``celeryd``                            ``python manage.py celeryd``
``celeryctl``                          ``python manage.py celeryctl``
``celerybeat``                         ``python manage.py celerybeat``
``camqadm``                            ``python manage.py camqadm``
``celeryev``                           ``python manage.py celeryev``
``celeryd-multi``                      ``python manage.py celeryd_multi``
=====================================  =====================================

The other main difference is that configuration values are stored in
your Django projects' ``settings.py`` module rather than in
``celeryconfig.py``.

If you're trying celery for the first time you should start by reading
`Getting started with django-celery`_

Special note for mod_wsgi users
-------------------------------

If you're using ``mod_wsgi`` to deploy your Django application you need to
include the following in your ``.wsgi`` module::

    import djcelery
    djcelery.setup_loader()

Documentation
=============

The `Celery User Manual`_ contains user guides, tutorials and an API
reference. Also the `django-celery documentation`_, contains information
about the Django integration.

.. _`django-celery documentation`: http://django-celery.readthedocs.org/
.. _`Celery User Manual`: http://docs.celeryproject.org/
.. _`Getting started with django-celery`:
    http://django-celery.readthedocs.org/en/latest/getting-started/first-steps-with-django.html

Installation
=============

You can install ``django-celery`` either via the Python Package Index (PyPI)
or from source.

To install using ``pip``,::

    $ pip install django-celery

To install using ``easy_install``,::

    $ easy_install django-celery

You will then want to create the necessary tables. If you are using south_
for schema migrations, you'll want to::

    $ python manage.py migrate djcelery

For those who are not using south, a normal ``syncdb`` will work::

    $ python manage.py syncdb

.. _south: http://pypi.python.org/pypi/South/

Downloading and installing from source
--------------------------------------

Download the latest version of ``django-celery`` from
http://pypi.python.org/pypi/django-celery/

You can install it by doing the following,::

    $ tar xvfz django-celery-0.0.0.tar.gz
    $ cd django-celery-0.0.0
    # python setup.py install # as root

Using the development version
------------------------------

You can clone the git repository by doing the following::

    $ git clone git://github.com/ask/django-celery.git

Getting Help
============

Mailing list
------------

For discussions about the usage, development, and future of celery,
please join the `celery-users`_ mailing list. 

.. _`celery-users`: http://groups.google.com/group/celery-users/

IRC
---

Come chat with us on IRC. The `#celery`_ channel is located at the `Freenode`_
network.

.. _`#celery`: irc://irc.freenode.net/celery
.. _`Freenode`: http://freenode.net


Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them
to our issue tracker at http://github.com/ask/django-celery/issues/

Wiki
====

http://wiki.github.com/ask/celery/

Contributing
============

Development of ``django-celery`` happens at Github:
http://github.com/ask/django-celery

You are highly encouraged to participate in the development.
If you don't like Github (for some reason) you're welcome
to send regular patches.

License
=======

This software is licensed under the ``New BSD License``. See the ``LICENSE``
file in the top distribution directory for the full license text.

.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround

