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

    pip install -U pip wheel magnum-pi
    mkdir -p wheel
    pip wheel --no-use-wheel --wheel-dir=wheels -r requirements/prod.txt -r requirements/dev.txt
    makeindex wheels
    tar -zcf wheels.tar.gz wheels
    aws --profile mozilla s3 sync wheels s3://pkgs.mozilla.net/python/mdn/wheels
    aws --profile mozilla s3 cp wheels.tar.gz s3://pkgs.mozilla.net/python/mdn/wheels.tar.gz

Installing the Wheels
---------------------

Tests on Travis use a tarball to download them all at once and speed things
up::

    wget https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/python/mdn/wheels.tar.gz
    tar -zxf wheels.tar.gz
    pip install --no-index --find-links=wheels -r requirements/prod.txt -r requirements/dev.txt

Alternatively, this is an experimental way to use S3 as a Python package index::

    virtualenv venv
    . ./venv/bin/activate
    pip install -U pip wheel -r requirements/compiled.txt 
    pip install --use-wheel --index-url 'http://pkgs.mozilla.net/python/mdn/wheels/index' -r requirements/prod.txt -r requirements/dev.txt

This package index approach needs improvement, though. It's currently only
working under HTTP, and should be accessible via HTTPS before it's relied upon
for anything serious.

Future Expansion
----------------

These wheels currently live in lorchard's personal people.mozilla.com
directory, which is not good. At some point in the near future, these need to
move somewhere more robust and somewhere that the core MDN dev team can update
as a group.
