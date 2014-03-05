==============
Wheels for Pip
==============

Wheels are a way to bundle & distribute Python dependencies. We are
experimenting with using them in tests and to someday replace the vendor
library.

Updating the Wheels
-------------------

Wheels are stored on Amazon S3 at pkgs.mozilla.net - file an IT bug to get
yourself a set of AWS credentials. Once that's done, you can set up AWS CLI
tools like so:

    sudo pip install awscli
    cat >> ~/src/.awsconfig
    [profile mozilla]
    aws_access_key_id=YOUR_KEY_ID_HERE
    aws_secret_access_key=YOUR_ACCESS_KEY_HERE
    region=us-west-2

.. note::

    We're storing the AWS config in the ``~/src`` directory as it's the only
    way to persist the credentials between recreation of Vagrant instances.
    We're ignoring the file ``~/src/.awsconfig`` by default in our
    ``.gitignore`` file though, so it should never land in a public space.
    To make use of that config file we're setting the ``AWS_CONFIG_FILE``
    environment variable to ``/home/vagrant/src/.awsconfig`` when you run the
    upload invoke task (unless you're specifying it otherwise).

Then, you can update the wheels like so::

    sudo pip install -U pip wheel awscli
    invoke build

If you'd like to only build one of the possible wheel files use the ``--only``
option::

    invoke build --only=travis

After that you should have a directory called ``wheelhouse`` with some tar.gz
files. After that you want to upload them to the Amazon S3 bucket by running::

    invoke upload

If you only want to upload one of the built wheels use the ``--name`` option::

    invoke upload --only=travis

Installing the Wheels
---------------------

.. note::

    This is done by Puppet by default and shouldn't be needed.

If you're ready to update your requirements manually run this::

    inv install base
