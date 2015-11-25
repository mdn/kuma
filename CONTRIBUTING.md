Contributing Code
=================

  * You agree to license your contributions under [MPL 2][MPL2]
  * Discuss large changes on the [dev-mdn mailing list][dev-mdn]
    or on a [bugzilla bug][mdn-backlog] before coding.
  * Python code style should follow [PEP8 standards][pep8] whenever possible.
  * All commit messages must start with "bug NNNNNNN" or "fix bug NNNNNNN"
    * Reason: Make it easy for someone to consume the commit log and reach originating requests for all changes
    * Exceptions: "Merge" and "Revert" commits
    * Notes:
      * "fix bug NNNNNNN" - will trigger a github bot to automatically mark bug as "RESOLVED:FIXED"
      * If a pull request has multiple commits, we should squash commits together or re-word commit messages so that each commit message contains a bug number

  * MDN module [owner or peer][peers] must review and merge all pull requests.
    * Reason: Owner and peers are and accountable for the quality of MDN code changes
    * Exceptions: Owners/peers may commit directly to master for critical security/down-time fixes; they must file a bug for follow-up review.

  * Pull requests that contain changes to database migrations or any other code changes
    that modify the database layout MUST have been reviewed at least by two
    [peers][peers], one of which MUST be a module owner.
    * Reason: Changes to database tables are critical and may lead to loss of data.
    * Exceptions: None.
    * Notes: A great way to get a 2nd review is to explain the migration to someone who wasn't involved in its development or 1st review.

  * MDN reviewers must verify sufficient test coverage on all changes - either by new or existing tests
    * Reason: Automated tests reduce human error involved in reviews
    * Notes: The Django site has [good testing docs][django-testing]

[MPL2]: http://www.mozilla.org/MPL/2.0/
[dev-mdn]: https://lists.mozilla.org/listinfo/dev-mdn
[mdn-backlog]: http://mzl.la/mdn_backlog
[pep8]: http://www.python.org/dev/peps/pep-0008/
[django-testing]: https://docs.djangoproject.com/en/dev/topics/testing/
[peers]: https://wiki.mozilla.org/Modules/All#MDN

What to work on
===============

We keep a good list of starting mentored bugs on [the MDN "Getting Involved" page](https://wiki.mozilla.org/Webdev/GetInvolved/developer.mozilla.org#Mentored_Bugs).

If you have questions about what to work on, you can ask:

* In the #mdndev [IRC channel on irc.mozilla.org](https://wiki.mozilla.org/Irc)
* On [the dev-mdn@lists.mozilla.org mailing list](https://lists.mozilla.org/listinfo/dev-mdn)


How to submit code
==================

MDN development process is very much like [these Mozilla Webdev guidelines](http://mozweb.readthedocs.org/en/latest/guide/development_process.html).

The [GitHub Flow](https://guides.github.com/introduction/flow/) site is a great interactive guide to the flow described here.

GitHub workflow
---------------

1. [Install our development environment](http://kuma.readthedocs.org/en/latest/installation.html)
2. Create a branch for your bug:

    ```
    git checkout -b new-issue-888888
    ```

3. Code on the bug branch
4. Commit changes to bug branch:

    ```
    git add .
    git commit -m 'fix bug 888888 - commit message'
    ```

5. Push branch to GitHub:

    ```
    git push origin new-issue-888888
    ```

6. Send pull request on GitHub
