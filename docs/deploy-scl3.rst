=================
Deploying to SCL3
=================

MDN is served from SLC3, a data center in Santa Clara, California.  It is
deployed on several persistent virtual machines, managed by Mozilla WebOps.
Deploying new code to SCL3 takes several steps.  It takes a couple of hours to
deploy, and the deployer is responsible for emergency issues for the next 24
hours. This means that there are 1-3 deployments per week, usually between 7 AM
and 1 PM Pacific, Monday through Thursday.

.. Note::

   This page describes deployment performed by MDN staff. It requires
   additional setup and permissions not described here. Deployments will
   not work for non-staff developers, and should not be attempted.

Pre-Deployment: Update Submodules
---------------------------------
* Check that the Kuma_ and the KumaScript_ builds are passing.

.. _Kuma: https://travis-ci.org/mozilla/kuma/
.. _KumaScript: https://travis-ci.org/mdn/kumascript

* Commit or stash any changes you have to prepare to change branches
* Create a pre-push branch from master::

    git remote -v | grep origin
    # origin  git@github.com:mozilla/kuma.git (fetch)
    # origin  git@github.com:mozilla/kuma.git (push)
    git fetch origin
    git checkout -b pre-push-2017-08-08 origin/master

* Update the submodules::

    git submodule update --remote
    git diff
    git commit kumascript locale

  For bonus points, the commit message should mention the KumaScript PRs::

    Update locales, KumaScript PRs 235,271,275,277,278,280

    * mdn/kumascript#235 - TopicBox: Add de translation
    * mdn/kumascript#271 - GroupData: Update WebVR sidebar
    * mdn/kumascript#275 - Move mozilla/kumascript to mdn/kumascript
    * mdn/kumascript#277 - EmbedInteractiveExample: Update URL
    * mdn/kumascript#278 - GroupData: Add Nav.mediaDevices.getUserMedia
    * mdn/kumascript#280 - Spec2: Mark SIMD Obsolete

  This will add references to the PRs back to the commit where there were
  deployed. You can see the commits from the `What's Deployed`_ page, or by
  using `GitHub's compare view`_::

    # This long command is needed once
    # On OSX, change "echo" to "open" to open in browser
    git config --add alias.submodule-compare-urls "submodule foreach --quiet 'echo \"https://github.com/\`git remote get-url origin | cut -d: -f2 | cut -d. -f1\`/compare/\$sha1...\`git rev-parse @\`\"'"

    # And then can be used to print the URLs
    git submodule-compare-urls

  You can just see the merge commits with ``git log --merges``::

    git submodule foreach 'git log --merges HEAD...$sha1'

.. _`What's Deployed`: https://whatsdeployed.io/s-FHK
.. _`GitHub's compare view`: https://github.com/blog/612-introducing-github-compare-view

* Push the branch and open a pull request::

    git push -u origin pre-push-2017-08-08

* Check that tests pass. The ``TOXENV=locales`` job, which uses Dennis_ to
  check strings, is the job that occasionally fails. This is due to a
  string change committed in Pontoon_ that will break rendering in production.
  If this happens, fix the incorrect translation, push to master on
  mdn-l10n_, and update the submodule in the pull request. Wait for the
  tests to pass.

.. _Dennis: https://github.com/willkg/dennis
.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/
.. _mdn-l10n: https://github.com/mozilla-l10n/mdn-l10n

* Merge the PR. A "Rebase and merge" is preferred, to avoid a merge commit
  with little long-term value. Delete the pre-push branch.


Deploy to Staging
-----------------
The staging site is located at https://developer.allizom.org.  It runs on the
same Kuma code as production, but against a different database, other backing
services, and with less resources. It is used for verifying code changes before
pushing to production.

* Start the staging push. There are two methods for pushing, the chief website
  (a.k.a the Big Red Button) and the command line tool james_. Both require VPN
  access, and a commit hash you want to push.  ``james`` defaults to your current working
  copy::

    git fetch origin
    git checkout origin/master
    james stage

  This will confirm the commits you wish to push, and then run
  _`the deployment script`.

.. _james: https://github.com/mythmon/chief-james

* Prepare for testing on staging:

  * Look at the changes to be pushed, and report bug numbers and PRs in IRC.
    ``firebot`` will give handy links to Bugzilla. Committers and bug assignees
    can see that their changes are being deployed.
  * Think about manual tests to confirm the code changes work without errors.
  * Monitor the push in the ``#mdndev`` IRC channel. The final message is
    something like::

        jwhitlock pushed mdn-stage 840af1d2a75b7684775129e7a4f0c4b9e86523c1

* Merge and push to the ``stage-integration-tests`` branch::

    git checkout stage-integration-tests
    git merge --ff-only origin/master
    git push

  This will kick off `functional tests`_ in Jenkins_.

.. _`functional tests`: https://ci.us-west.moz.works/blue/organizations/jenkins/mdn_multibranch_pipeline/branches/
.. _Jenkins: https://ci.us-west.moz.works

* Manually test changes on https://developer.allizom.org. Look for server
  errors on homepage and article pages. Try to verify features in the newly
  pushed code. Check the `functional tests`_.

* Announce in IRC that staging looks good, and you are pushing to production.

Deploy to Production
--------------------
The production site is located at https://developer.mozilla.org. It is
monitored by the development team and WebOps.

* Pick a push song on https://www.youtube.com. Post link to IRC.

* Start the production push::

    james prod

* Monitor the push in the ``#mdndev`` IRC channel. The final message is
  something like::

    jwhitlock pushed mdn 840af1d2a75b7684775129e7a4f0c4b9e86523c1

* For the next 30-60 minutes,

  * Watch https://developer.mozilla.org
  * Monitor MDN in New Relic for about an hour after the push, for increased
    errors or performance changes.
  * Close bugs that are now fixed by the deployment
  * Move relevant Taiga cards to Done
  * Move relevant Paper cut cards to Done

.. `the deployment script`_

The Deployment Script
---------------------
The deployment script is chief_deploy.py_, checked into the Kuma repository.
The last updated version of the script is run, so changes to the script take
two deploys to take effect, first to update the script and second to run the
new script.

.. _chief_deploy.py: https://github.com/mozilla/kuma/blob/master/scripts/chief_deploy.py

The deployment steps are:

* ``pre_update``

  * ``update_code`` - checks out the desired Kuma commit
  * ``setup_dependencies`` - Remove the Python virtualenv and recreate it with
    the current dependencies. Remove the node.js node_modules folder and
    recreate it with the current dependencies.
  * ``update_info`` - Print the date, git branch, last 3 commits, repository and
    submodule status, and database migrations, for the deployment logs.
    Record the commit number to media/revision.txt, for later tools and live
    access.

* ``update``

  * ``update_assets`` - compiles stylesheets to CSS, extracts strings from JS
    files, gathers assets to the file serving location, and creates
    “cache-busting” variants that incorporate the MD5 hash of the contents in
    the file name.
  * ``update_locales`` - lints and compiles locale (translation) files
  * ``database`` - runs database migrations

* ``deploy``

  * ``checkin_changes`` - On the admin server, run the WebOps-managed deployment
    script, which rsyncs the project (excluding source control metadata like
    the .git folder) to the deployment folder on the file server.
  * ``deploy_app`` - On the remote Web and Async nodes, run the WebOps-managed
    deployment script, which rsyncs the project from the deployment folder on
    the file server to the runtime folder on the local disk.
  * ``restart_web`` - On the remote Web and Async nodes, restart Apache.
  * ``restart_kumascript`` - On the remote Web and Async nodes, stop the
    KumaScript service (nicely then firmly), and start it.
  * ``restart_celery`` - On the remote Async nodes, restart the celery tasks,
    including the ``celerybeat`` and ``celerycam`` tasks on the first node.
  * ``ping_newrelic`` - Report the deployment and commit number to New Relic.

A log file collects the output of the push, for debugging issues.  Bots
``mdnstagepush`` and ``mdnprodpush`` watch the deployment progress and prints
the steps to the #mdndev IRC channel.
