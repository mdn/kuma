integration-tests
-----------------
The integration-tests Docker image contains browser-based integration tests
that check the functionality of a running Kuma deployment.

The image can be recreated locally with
``docker build -f docker/images/integration-tests/ .``, but this is only
necessary for image development. Most developer will follow the
`Client-side testing documentation`_ to develop and run these integration tests.

.. _`Client-side testing documentation`: https://kuma.readthedocs.io/en/latest/tests-ui.html

The image is built and used in Jenkins__ in the ``stage-integration-tests`` and
``prod-integration-tests`` pipelines, configured by scripts in the
``Jenkinsfiles`` folder.  It is not published to quay.io.

.. __: https://ci.us-west.moz.works/blue/organizations/jenkins/mdn_multibranch_pipeline/activity
