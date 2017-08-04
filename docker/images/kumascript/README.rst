kumascript
----------

The kumascript Docker image contains the kumascript rendering engine and
support files.  The environment can be customized for different deployments.

The image can be recreated locally with ``make build-kumascript``.

The image tagged ``latest`` is used by default for development. It can be
created locally with ``make build-kumascript KS_VERSION=latest``. The official
latest image is created from the master branch in Jenkins__ and published to
quay.io__.

.. __: https://ci.us-west.moz.works/blue/organizations/jenkins/mdn_multibranch_pipeline/branches/
.. __: https://quay.io/repository/mozmar/kumascript
