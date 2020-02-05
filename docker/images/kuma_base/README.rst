kuma_base
---------
The kuma_base Docker image contains the OS and libraries (C, Python, and
Node.js) that support the kuma project.  The kuma image extends this by
installing the kuma source and building assets needed for production.

The image can be recreated locally with ``make build-base``.

The image tagged ``latest`` is used by default for development. It can be
created locally with ``make build-base VERSION=latest``. The official
latest image is created from the master branch in Jenkins__ and published to
DockerHub__

.. __: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches/
.. __: https://hub.docker.com/r/mdnwebdocs/kuma_base/
