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

Good starting projects are listed on [GitHub][github] and [Bugzilla][bugzilla]. If you have any questions, just ask in the #mdndev IRC channel on irc.mozilla.org!

[github]: https://github.com/mozilla/kuma/issues?labels=good+first+issue&milestone=&page=1&state=open
[bugzilla]: https://bugzilla.mozilla.org/buglist.cgi?bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&columnlist=short_desc%2Ccomponent%2Cchangeddate&list_id=9799718&product=Mozilla%20Developer%20Network&query_format=advanced&status_whiteboard=[good%20first%20bug]&status_whiteboard_type=allwordssubstr&query_based_on=

How to submit code
==================

GitHub workflow
---------------

   1. [Install our development environment](http://kuma.readthedocs.org/en/latest/installation-vagrant.html)
   2. Set up mozilla remote ($ git remote add mozilla git://github.com/mozilla/kuma.git)
   3. Create a branch for a bug ($ git checkout -b new-issue-888888)
   4. Develop on bug branch.

   [Time passes, the mozilla/kuma repository accumulates new commits]
   5. Commit changes to bug branch ($ git add . ; git commit -m 'fix bug 888888 - commit message')
   6. Fetch mozilla ($ git fetch mozilla)
   7. Update local master ($ git checkout master; git pull mozilla master)

   Repeat steps 4-7 till dev is complete

   8. Rebase issue branch ($ git checkout new-issue-888888; git rebase master)
   9. Push branch to GitHub ($ git push origin new-issue-888888)
   10. Issue pull request (Click Pull Request button)
