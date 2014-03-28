Contributing Code
=================

  *  You agree to license your contributions under [MPL 2][MPL2]
  *  Discuss large changes on the [dev-mdn mailing list][dev-mdn]
     or on a [bugzilla bug][mdn-backlog] before coding.
  *  Python code style should follow [PEP8 standards][pep8] whenever possible.
  *  Write tests!  The Django site has [good testing docs][django-testing]

[MPL2]: http://www.mozilla.org/MPL/2.0/
[dev-mdn]: https://lists.mozilla.org/listinfo/dev-mdn
[mdn-backlog]: http://mzl.la/mdn_backlog
[pep8]: http://www.python.org/dev/peps/pep-0008/
[django-testing]: https://docs.djangoproject.com/en/dev/topics/testing/

What to work on
===============

Good starting projects are listed on [GitHub][github] and [Bugzilla][bugzilla]. If you have any questions, just ask in the #mdndev IRC channel on irc.mozilla.org!

[github]: https://github.com/mozilla/kuma/issues?labels=good+first+issue&milestone=&page=1&state=open
[bugzilla]: https://bugzilla.mozilla.org/buglist.cgi?status_whiteboard_type=allwordssubstr&status_whiteboard=[mentor%3D&resolution=---&query_format=advanced&product=Mozilla%20Developer%20Network&list_id=9797391

How to submit code
==================

GitHub workflow
---------------

   1. Most devs use the [Vagrant Installation](https://github.com/mozilla/kuma/blob/master/docs/installation-vagrant.rst#getting-up-and-running).
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
