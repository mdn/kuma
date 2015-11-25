=================
Celery and Rabbit
=================

Kuma uses `Celery <http://celeryproject.org/>`_ to enable offline task
processing for long-running jobs like sending email notifications and
re-rendering the Knowledge Base.

Though Celery supports multiple message backends, we use, and recommend that
you use, `RabbitMQ <http://www.rabbitmq.com/>`_. RabbitMQ is an AMQP message
broker written in Erlang.


When is Celery Appropriate
==========================

You can use Celery to do any processing that doesn't need to happen in the
current request-response cycle. Examples are generating thumbnails, sending out
notification emails, updating content that isn't about to be displayed to the
user, and others.

Ask yourself the question: "Is the user going to need this data on the page I'm
about to send them?" If not, using a Celery task may be a good choice.


RabbitMQ
========


Installing
----------

RabbitMQ should be installed via your favorite package manager. It can be
installed from source but has a number of Erlang dependencies.

Configuring
-----------

RabbitMQ takes very little configuration.

::

    # Start the server.
    sudo rabbitmq-server -detached

    # Set up the permissions.
    sudo rabbitmqctl add_user kuma kuma
    sudo rabbitmqctl add_vhost kuma
    sudo rabbitmqctl set_permissions -p kuma kuma ".*" ".*" ".*"

That should do it. You may need to use ``sudo`` for ``rabbitmqctl``. It depends
on the OS and how Rabbit was installed.


Celery
======


Installing
----------

Celery (and Django-Celery) is part of our :doc:`vendor library <vendor>`. You
shouldn't need to do any manual installation.


Configuring and Running
-----------------------

We set some reasonable defaults for Celery in ``settings.py``. These can be
overriden either in ``settings_local.py`` or via the command line when running
``manage.py celeryd``.

In ``settings_local.py`` you should set at least this, if you want to use
Celery::

    CELERY_ALWAYS_EAGER = False

This defaults to ``True``, which causes all task processing to be done online.
This lets you run Kuma even if you don't have Rabbit or want to deal with
running workers all the time.

You can also configure the log level or concurrency. Here are the defaults::

    CELERYD_LOG_LEVEL = logging.INFO
    CELERYD_CONCURRENCY = 4

Then to start the Celery workers, you just need to run::

    ./manage.py celeryd

This will start Celery with the default number of worker threads and the
default logging level. You can change those with::

    ./manage.py celeryd --log-level=DEBUG -c 10

This would start Celery with 10 worker threads and a log level of ``DEBUG``.
