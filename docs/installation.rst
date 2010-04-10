============
Installation
============


Requirements
------------

* Python 2.6
* `setuptools <http://pypi.python.org/pypi/setuptools#downloads>`_
* `Hunspell <http://hunspell.sourceforge.net/>`_ (Specifically, headers for
  `PyHunspell <http://code.google.com/p/pyhunspell/>`_.)
  * With Hunspell, you will also need dictionaries, either from Hunspell or
    MySpell, to provide spelling suggestions on search queries.
  * Note that Hunspell is required even if no dictionaries are installed.


Additional Requirements
~~~~~~~~~~~~~~~~~~~~~~~

Besides the Pythonic requirements, you'll probably want this software to make
things happen:

* Git, obviously.
* Memcached - the server, since the client is included in requirements.txt.
* Sphinx - the server. We're currently on 0.9.9-release.


Getting the Source
------------------

Grab the source from Github using::

    git clone git://github.com/jsocol/kitsune.git


virtualenv
----------

`virtualenv <http://pypi.python.org/pypi/virtualenv>`_ is a tool to create
isolated Python environments.  We're going to be installing a bunch of packages,
but we don't want your system littered with all these things you only need for
zamboni.  Some other piece of software might want an older version than zamboni
wants, which can create quite a mess.  ::

    easy_install virtualenv

virtualenv is the only package I install system-wide.  Everything else goes in a
virtual environment.


virtualenvwrapper
-----------------

`virtualenvwrapper <http://www.doughellmann.com/docs/virtualenvwrapper/>`_
complements virtualenv by installing some shell functions that make environment
management smoother.

Install it like this::

    wget http://bitbucket.org/dhellmann/virtualenvwrapper/raw/tip/virtualenvwrapper_bashrc -O ~/.virtualenvwrapper
    mkdir ~/.virtualenvs

Then put these lines in your ``~/.bashrc``::

    export WORKON_HOME=$HOME/.virtualenvs
    source $HOME/.virtualenvwrapper

``exec bash`` and you're set.


virtualenvwrapper Hooks
~~~~~~~~~~~~~~~~~~~~~~~

virtualenvwrapper lets you run hooks when creating, activating, and deleting
virtual environments.  These hooks can change settings, the shell environment,
or anything else you want to do from a shell script.  For complete hook
documentation, see
http://www.doughellmann.com/docs/virtualenvwrapper/hooks.html.

You can find some lovely hooks to get started at http://gist.github.com/234301.
The hook files should go in ``$WORKON_HOME`` (``$HOME/.virtualenvs`` from
above), and ``premkvirtualenv`` should be made executable.


premkvirtualenv
***************

This hook installs pip and ipython into every virtualenv you create.


postactivate
************

This runs whenever you start a virtual environment.  If you have a virtual
environment named ``kitsune``, ``postactivate`` switches the shell to
``~/dev/kitsune`` if that directory exists.


Getting Packages
----------------

Now we're ready to go, so create an environment for kitsune::

    mkvirtualenv --no-site-packages kitsune

That creates a clean environment named kitsune and (for convenience) initializes
the environment.  You can get out of the environment by restarting your shell or
calling ``deactivate``.

To get back into the kitsune environment later, type::

    workon kitsune

If you keep your Python binary in a special place (i.e. you don't want to use
the system Python), pass the path to mkvirtualenv with ``--python``::

    mkvirtualenv --python=/usr/local/bin/python2.6 --no-site-packages kitsune


pip
~~~

We're going to use pip to install Python packages from `pypi
<http://pypi.python.org/pypi>`_ and github. ::

    easy_install pip

Since we're in our kitsune environment, pip was only installed locally, not
system-wide.

kitsune uses a requirements file to tell pip what to install.  Get just the
basics you need by running ::

    pip install -r requirements.txt

from the root of your kitsune checkout. For a development environment, you'll
want to use ``requirements-dev.txt`` instead ::

    pip install -r requirements-dev.txt


Settings
--------

Most of kitsune is configured in ``settings.py``, but it's incomplete since we
don't want to put database passwords into version control.  Put any local
settings into ``settings_local.py``.  Make sure you have ::

    from settings import *

in your ``settings_local.py`` so that all of the configuration is included.

I'm overriding the database parameters from ``settings.py`` and then extending
``INSTALLED_APPS`` and ``MIDDLEWARE_CLASSES`` to include the `Django Debug
Toolbar <http://github.com/robhudson/django-debug-toolbar>`_.  It's awesome,
and I recommend you do the same.


Database
--------

For now, you'll need a dump of the SUMO database. It's unfortunate, but we're 
working on it.
