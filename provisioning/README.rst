Provisioning
============

This is the provisioning folder which is partially managed automatically
by ansible's package manager, ansible-galaxy. It is currently used in
TravisCI, but is planned for removal (bug 1352232).

.. warn::

    Don't modify anything in ``provisioning/roles`` other than the kuma role!
    See below for instructions how to update the roles.

Updating vendored roles
-----------------------

To update vendored roles in the ``roles/`` directory you can simply call
this Make task::

    make roles

This will call Ansible's package manager ansible-galaxy with the ``roles.txt``
file that is the equivalent to pip's ``requirements.txt`` file format.
