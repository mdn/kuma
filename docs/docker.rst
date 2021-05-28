======
Docker
======

Docker__ is used for development and for deployment.

.. __: https://www.docker.com

Docker Images
=============
Docker images are used in development, usually with the local
working files mounted in the images to set behaviour.

Images are built by Jenkins__, after tests pass, and are
published to DockerHub__.  We try to
`store the configuration in the environment`_, so that the
published images can be used in deployments by setting
environment variables to deployment-specific values.

.. __: https://ci.us-west-2.mdn.mozit.cloud
.. __: https://hub.docker.com/r/mdnwebdocs/kuma/
.. _`store the configuration in the environment`: https://12factor.net/config

Here are some of the images used in the Kuma project:

.. Published images
.. include:: ../docker/images/kuma/README.rst
.. include:: ../docker/images/kuma_base/README.rst
