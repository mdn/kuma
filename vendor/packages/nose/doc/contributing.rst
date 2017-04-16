Contributing to nose
====================

You'd like to contribute to nose? Great! Now that nose is hosted under
`GitHub <http://github.com/>`__, contributing is even easier.

Get the code!
-------------

Start by getting a local working copy of nose from github::

  git clone https://github.com/nose-devs/nose

If you plan to submit changes back to the core repository, you should set up a
public fork of your own somewhere (`GitHub <http://github.com/>`__ is a good
place to do that). See GitHub's `help <http://help.github.com/>`__ for details
on how to contribute to a Git hosted project like nose.

Running nose's tests
--------------------

nose runs its own test suite with `tox
<http://codespeak.net/tox/>`. You don't have to install tox to run
nose's test suite, but you should, because tox makes it easy to run
all tests on all supported python versions. You'll also need python
2.4, 2.5, 2.6, 2.7, 3.1 and jython installed somewhere in your $PATH.

Discuss
-------

Join the `nose developer list
<http://groups.google.com/group/nose-dev>`__ at google groups. It's
low-traffic and mostly signal.

What to work on?
----------------

You can find a list of open issues at nose's `issue tracker
<http://github.com/nose-devs/nose/issues>`__. If you'd like to
work on an issue, leave a comment on the issue detailing how you plan
to fix it, or simply submit a pull request.

I have a great idea for a plugin...
-----------------------------------

Great! :doc:`Write it <plugins/writing>`. Release it on `pypi
<http://pypi.python.org>`__. If it gains a large following, and
becomes stable enough to work with nose's 6+ month release cycles, it
may be a good candidate for inclusion in nose's builtin plugins.

