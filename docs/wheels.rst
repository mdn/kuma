==============
Wheels for Pip
==============

Wheels are a way to bundle & distribute Python dependencies. We are
experimenting with using them in tests and to someday replace the vendor
library.

Updating the Wheels
-------------------

This is very ad-hoc right now, and only lorchard can do it::

     pip install -U pip wheel magnum-pi
     mkdir wheel
     pip wheel --no-use-wheel --wheel-dir=wheels -r requirements/prod.txt -r requirements/dev.txt
     makeindex wheels
     tar -zcf wheels.tar.gz wheels
     rsync -vruz wheels/ people:public_html/kuma/wheels/
     rsync -vruz wheels.tar.gz people:public_html/kuma/wheels.tar.gz

Installing the Wheels
---------------------

If you are setting up a native instance of Kuma - i.e. not running within a
virtual machine via Vagrant - this may be a helpful sequence of commands::

    virtualenv venv
    . ./venv/bin/activate
    pip install -U pip wheel -r requirements/compiled.txt 
    pip install --use-wheel --index-url 'https://people.mozilla.com/~lorchard/kuma/wheels/index' -r requirements/prod.txt -r requirements/dev.txt

Alternatively, if you don't feel like downloading all the wheels separately,
tests on Travis use a tarball to download them all at once and speed things up::

    wget http://people.mozilla.org/~lorchard/kuma/wheels.tar.gz
    tar -zxf wheels.tar.gz
    pip install --no-index --find-links=wheels -r requirements/prod.txt -r requirements/dev.txt

Future Expansion
----------------

These wheels currently live in lorchard's personal people.mozilla.com
directory, which is not good. At some point in the near future, these need to
move somewhere more robust and somewhere that the core MDN dev team can update
as a group.
