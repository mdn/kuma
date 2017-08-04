kuma_base
---------
The kuma_base Docker image contains the OS and libraries (C, Python, and
Node.js) that support the kuma project.  The kuma image extends this by
installing the kuma source and building assets needed for production.

The image can be recreated locally with ``make build-base``.

The image tagged ``latest`` is used by default for development. It can be
created localled with ``make build-base VERSION=latest``. The official
latest image is created from the master branch in Jenkins__ and published to
quay.io__

.. __: https://ci.us-west.moz.works/blue/organizations/jenkins/mdn_multibranch_pipeline/branches/
.. __: https://quay.io/repository/mozmar/kuma_base
