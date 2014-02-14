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
    mkdir ~/.aws
    cat >> ~/.aws/config
    [profile mozilla]
    aws_access_key_id=YOUR_KEY_ID_HERE
    aws_secret_access_key=YOUR_ACCESS_KEY_HERE
    region=us-west-2

Then, you can update the wheels like so:

    pip install -U pip wheel
    mkdir -p wheel
    pip wheel --no-use-wheel --wheel-dir=wheels -r requirements/prod.txt -r requirements/dev.txt
    tar -zcf wheels.tar.gz wheels
    aws --profile mozilla s3 cp wheels.tar.gz s3://pkgs.mozilla.net/python/mdn/wheels.tar.gz

Installing the Wheels
---------------------

You can download the wheels all at once as a tarball::

    wget https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/python/mdn/wheels.tar.gz
    tar -zxf wheels.tar.gz
    pip install --no-index --find-links=wheels -r requirements/prod.txt -r requirements/dev.txt
