=============
Deploying MDN
=============

MDN is served from `Amazon Web Services`_ in the US West (Oregon)
datacenters. MDN is deployed as Docker_ containers managed by Kubernetes_. The
infrastructure is defined within MDN's `infra repository`_, including the tools
used to `deploy and maintain MDN`_.

.. _`Amazon Web Services`: https://en.wikipedia.org/wiki/Amazon_Web_Services
.. _Docker: https://www.docker.com/
.. _Kubernetes: https://kubernetes.io/
.. _`infra repository`: https://github.com/mdn/infra
.. _`deploy and maintain MDN`: https://github.com/mdn/infra/tree/master/apps/mdn/mdn-aws

Deploying new code to AWS takes several steps, and about 60 minutes for the
full process. The deployer is responsible for emergency issues for the next 24
hours. There are 1-3 deployments per week, usually between 7 AM and 1 PM
Pacific, Monday through Thursday.

.. Note::

   This page describes deployment performed by MDN staff. It requires
   additional setup and permissions not described here. Deployments will
   not work for non-staff developers, and should not be attempted.

.. _Pre-Deployment:

Pre-Deployment
--------------

Before deploying, a staff member should:

* (Once a week) Check that the latest `mdn-browser-compat-data`_ node package
  is included in the KumaScript image. The latest package is installed when the
  image is created, during the ``RUN npm update`` step, and can be verified by
  reading the build logs or running the image.

* (Once a week) Update the ``locale`` and ``kumascript`` submodules. The ``locale``
  submodule must be updated to apply new translations to production. The
  ``kumascript`` submodule is not used for deployment, but updating it keeps
  the development environment in sync.

    - Commit or stash any changes in your working copy.
    - Create a pre-push branch from master::

        git fetch origin
        git checkout -b pre-push-`date +"%Y-%m-%d"` origin/master

    - Update the submodules::

        git submodule update --remote
        git commit -m "Updating submodules" kumascript locale

    - Push new localizable strings. This step is only necessary when there
      are new strings. The TravisCI job ``TOXENV=locales`` checks for new
      strings, and you can examine the output of the recent
      `master build`_ to see if there are differences. At the same time, it's
      not too hard to run locally and then revert if there are no useful
      changes.

      #. On the host system, checkout the master ``locale`` branch::

          cd locale
          git checkout master
          git pull

      #. Update ``kuma/settings/common.py``, and bump the version in
         ``PUENTE['VERSION']``.

      #. Inside the development environment, extract and rebuild the
         translations::

          make localerefresh

      #. On the host system (still in the ``locale`` subfolder), review the
         changes to source English strings::

          git diff templates/LC_MESSAGES

      #. If there are useful changes (ignore comment lines and look for
         ``msgid`` as the changed line), commit the files in the locale
         submodule::

          git add --all .
          git commit

         For the commit message, use the ``PUENTE['VERSION']`` in the commit
         subject, and summarize the string changes in the commit body, like::

          Update strings 2018.08

          * Add "View All" text for document history pagination

         Attempt to push to the mdn-l10n_ repository::

          git push

         If this fails, **do not force with --force**, or attempt to pull and
         create a merge commit.  Someone has added a translation while you were
         working, and you need to start over to preserve their work::

          git fetch
          git reset --hard @{u}

         This resets your locale submodule to the new master. Start over on
         step 3 (``make localerefresh``).

         If the push to mdn-l10n_ is a success, commit your Kuma changes::

          cd ..
          git commit kuma/settings/common.py locale

         You can use the same commit message used for the ``locale`` commit.

      #. If there are no new strings, throw the changes away, starting in the
         ``locale`` folder::

          git checkout -- .
          cd ..
          git checkout -- kuma/settings/common.py

    - Push the branch and `open a pull request`_::

        git push -u origin pre-push-`date +"%Y-%m-%d"`

    - Check that tests pass. The ``TOXENV=locales`` job, which uses Dennis_ to
      check strings, is the job that occasionally fails. This is due to a
      string change committed in Pontoon_ that will break rendering in
      production.  If this happens, fix the incorrect translation, push to
      master on mdn-l10n_, and update the submodule in the pull request. Wait
      for the tests to pass.

    - Merge the pull request. A "Rebase and merge" is preferred, to avoid a
      merge commit with little long-term value. Delete the pre-push branch.

* Check the latest images from master are built by Jenkins_
  (`Kuma master build`_, `KumaScript master build`_, both private to staff),
  and uploaded to the DockerHub_ repositories
  (`Kuma images`_, `KumaScript images`_).

.. _Dennis: https://github.com/willkg/dennis
.. _Jenkins: https://ci.us-west-2.mdn.mozit.cloud
.. _Kuma: https://github.com/mdn/kuma/actions
.. _KumaScript: https://travis-ci.org/mdn/kumascript
.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/
.. _`Kuma images`: https://hub.docker.com/r/mdnwebdocs/kuma/tags/
.. _`Kuma master build`: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/activity/?branch=master
.. _`KumaScript images`: https://hub.docker.com/r/mdnwebdocs/kumascript/tags/
.. _`KumaScript master build`: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kumascript/activity?branch=master
.. _`master build`: https://travis-ci.com/mdn/kuma
.. _`mdn-browser-compat-data`: https://www.npmjs.com/package/mdn-browser-compat-data
.. _`open a pull request`: https://github.com/mdn/kuma
.. _mdn-l10n: https://github.com/mozilla-l10n/mdn-l10n
.. _DockerHub: https://hub.docker.com/


Deploy to Staging
-----------------
The staging site is located at https://developer.allizom.org.  It runs on the
same Kuma code as production, but against a different database, other backing
services, and with less resources. It is used for verifying code changes before
pushing to production.

* Start the staging push, by updating and pushing the ``stage-push`` branches::

    git fetch origin
    git checkout stage-push
    git merge --ff-only origin/master
    git push
    cd kumascript
    git fetch origin
    git checkout stage-push
    git merge --ff-only origin/master
    git push
    cd ..

* Prepare for testing on staging:

  * Look at the changes to be pushed (`What's Deployed on Kuma`_, and
    `What's deployed on KumaScript`_). To enlist the help of pull request
    authors and others, you can report bug numbers and PRs in Matrix.
  * Think about manual tests to confirm the code changes work without errors.

* Merge and push to the ``stage-integration-tests`` branch::

    git checkout stage-integration-tests
    git merge --ff-only origin/master
    git push

  This will kick off `functional tests`_ in Jenkins_, which will also report
  to ``#mdndev``.

* Manually test changes on https://developer.allizom.org. Look for server errors
  on homepage and article pages. Try to verify features in the newly pushed
  code. Check the `functional tests`_.

* Announce in Slack (#mdn-dev) that staging looks good, and you are pushing to production.

.. _Jenkins: https://ci.us-west-2.mdn.mozit.cloud
.. _`What's Deployed on KumaScript`: https://whatsdeployed.io/s-SWJ
.. _`What's Deployed on Kuma`: https://whatsdeployed.io/s-HC0
.. _`functional tests`: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches

Deploy to Production
--------------------
The production site is located at https://developer.mozilla.org. It is
monitored by the development team and MozMEAO.

* Pick a push song on https://www.youtube.com. Post link to Matrix.

* Start the production push::

    git fetch origin
    git checkout prod-push
    git merge --ff-only origin/master
    git push
    cd kumascript
    git fetch origin
    git checkout prod-push
    git merge --ff-only origin/master
    git push
    cd ..

* For the next 30-60 minutes,

  * Watch https://developer.mozilla.org
  * Monitor MDN in New Relic for about an hour after the push, for increased
    errors or performance changes.
  * Start the :ref:`standby environment deployment <Deploy to Standby Environment>`
  * Close bugs that are now fixed by the deployment
  * Move relevant Taiga cards to Done
  * Move relevant Paper cut cards to Done

.. _Deploy to Standby Environment:

Deploy to Standby Environment
-----------------------------
The standby environment is located in the AWS EU Frankfurt datacenter. It runs
the same code and database as production, but runs in read-only
:ref:`maintenance mode <maintenance-mode>` and on minimal resources. It will
be scaled up and handle MDN traffic if there is a critical failure in
the AWS US West datacenter.

* Start the standby environment push::

    git fetch origin
    git checkout standby-push
    git merge --ff-only origin/master
    git push
    cd kumascript
    git fetch origin
    git checkout standby-push
    git merge --ff-only origin/master
    git push
    cd ..
