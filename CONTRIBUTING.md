Things to know when contributing code
=====================================
* You agree to license your contributions under [MPL 2][MPL2].
* You agreed to follow the [Code of Conduct][coc].
* Discuss large changes in [Discourse][discourse] or on a
  [GitHub issue][bugs] before coding.
* We don't accept pull requests for translated strings (anything under
  ``locale/``). Please use [Pontoon][pontoon] instead.

[MPL2]: http://www.mozilla.org/MPL/2.0/
[coc]: https://github.com/mdn/kuma/blob/master/CODE_OF_CONDUCT.md
[discourse]: https://discourse.mozilla.org/c/mdn
[bugs]: https://github.com/mdn/kuma/issues
[pontoon]: https://pontoon.mozilla.org/projects/mdn/

What to work on
===============
The MDN platform is a mature product, which means there aren't always bugs that
are suitable for new contributors. We keep a list of starting mentored bugs on
the [MDN "Getting Involved" page][get-involved]. There are interesting
[MDN projects][mdn-projects] outside of writing Python for the platform, but
they may be harder to find. If you have questions about what to work on, you
can ask:

* In the #mdn [Matrix room on chat.mozilla.org][matrix-howto].
* In the [MDN Topic][discourse] in Discourse.

[get-involved]: https://wiki.mozilla.org/Webdev/GetInvolved/developer.mozilla.org#Mentored_Bugs
[matrix-howto]: https://wiki.mozilla.org/Matrix
[mdn-projects]: https://github.com/mdn

How to submit code
==================
The MDN development process is similar to [GitHub Flow][gh-flow]. The general
steps are:

1. [Install our development environment][install].
2. Create a branch for your bug.
3. Make your changes, and create one or more commits.
4. Push your branch to your fork.
5. Open a pull request (PR).
6. Fix any issues identified by [TravisCI][travisci], our automated testing
   provider.
7. Fix any issues identified by code review.

MDN staff will take a look at your PR in 1 to 2 business days, either to review
and give feedback, or to tell you when we plan to review it.

[gh-flow]: https://guides.github.com/introduction/flow/
[install]: https://kuma.readthedocs.io/en/latest/installation.html
[travisci]: https://travis-ci.com/mdn/kuma/pull_requests

Conventions
===========
Contributors should follow MDN conventions as much as possible. This maintains
code quality and makes it easier to research problems. At the same time, we
don't expect new contributors to be familiar with all the rules. Pull requests
will not be rejected just because they don't follow conventions. Depending on
your experience level, reviewers may ask you to bring your PR up to standards,
or may make the changes themselves before merging. As you become more
experienced, you will be expected to make these changes yourself.

Code
----
Python code style should follow [PEP8 standards][pep8]. The required subset
of PEP8 is checked by ``flake8`` (``make lint``). Other PEP8
and [PEP257][pep257] (docstring) conventions are encouraged but not yet
enforced.

In Python code, we prefer ``'single quotes'`` for code strings and
``"""triple double-quotes"""`` for docstrings. There are other style
conventions (such as import statement order and indenting) which can be
determined by reading existing code.

Similar standards are enforced for front-end assets like CSS and
JavaScript. Some are checked by tools, and other by code review.

[pep8]: http://www.python.org/dev/peps/pep-0008/
[pep257]: https://www.python.org/dev/peps/pep-0257/

Branches
--------
We prefer that branch names have a descriptive summary and the bug number. MDN
staff are working with multiple branches at a time, and this makes it easier
to remember which is which. ``noun-###`` or ``verb-noun-####`` are good
patterns to follow.  Some good branch names:

* ``cache-control-headers-1431259``
* ``update-requests-1399639``

Some bad branch names:

* ``bug973612`` - This name requires looking up bug details in Bugzilla.
* ``fix-973612`` - This still doesn't communicate what the branch changes.
* ``create-page`` - This doesn't include the bug number, which suggests the
  author isn't linking changes to a bug.
* ``1431259-cache-control-headers`` - Putting the bug number first makes it
  more difficult to use tab-completion.

Exceptions are branches used in the deployment process, such as
``stage-push`` and ``prod-push``, and submodule update branches, such as
``pre-push-2018-02-21``.

In general, we prefer branches are stored on a fork, rather than the origin
repository. There are exceptions, such as the ``stage-push`` and
the ``prod-push`` branches, when we want the branch to run on our continuous
integration server.

It is recommended and safe to delete branches after the pull request is closed.
GitHub will remember the code changes in the context of the pull request. Less
stale branches mean less clutter and confusion.

Commits
-------
We prefer one-commit pull requests that are small and focused.  Multiple commit
PRs are good when the solution naturally breaks into multiple steps. The test
suite should pass for each commit.

Once a pull request is open, we prefer changes as additional commits. This
makes it easier to review just the changes since the last review. Once a
pull request is approved, the commits can be "squashed" into a single commit
before merging. Squashing is usually decided by the reviewer, but feel free
to squash commits yourself, ask for commits to be squashed, or ask for them to
be kept separate.

All commit messages must start with ``bug NNNNNNN``. This format makes it
easier to consume the commit log and get back to the Bugzilla bug.  Bugzilla
is where proposed changes are discussed, where one or more related changes are
linked, and where regressions are tracked.  We sometimes omit a bug or bug
number for non-code commits such as merge commits, submodule updates, and
updating translatable strings.

``fix bug NNNNNNN`` can also be used. When these commits are merged, the bug is
marked RESOLVED: FIXED. ``fix bug`` can be used when merging will fix the
bug, such as documentation updates or build fixes. ``fix bug`` is discouraged
when the code needs to be deployed to production to fix the issue, or when
multiple PRs are expected.

The rules for a [great commit message](https://chris.beams.io/posts/git-commit/)
should be followed:

1. Separate the subject line from the body with a blank line.
2. Limit the subject line to 50 characters.
3. Capitalize the subject line.
4. Do not end the subject line with a period.
5. Use the imperative mood in the subject line.
6. Wrap the body at 72 characters.
7. Use the body to explain what and why versus how.

Here's an example of a decent commit message (which ends up much longer than
[the commit itself][crawl-delay-commit]!):

```
bug 1316610: Drop Crawl-delay, etc from robots.txt

Googlebot doesn't respect Crawl-delay, but instead watches to see how
fast it can index your site without breaking it.

Request-rate isn't known by Googlebot, and doesn't appear to be supported
by many crawlers.

MDN can be accessed faster than 5 pages per second, and we shouldn't
penalize scrapers that respect robots.txt.
```

[crawl-delay-commit]: https://github.com/mdn/kuma/commit/4ba37df42531589c4276ea2b4c44270ac1c49210

Testing
-------
MDN uses automated tests to prevent regressions and ensure that new code does
what it claims. Tests are required for new functionality, as measured by code
coverage tools, and all tests must pass before merging.

We use [TravisCI][travisci] to automatically run tests and quality checks when
a pull request is opened. If TravisCI identifies problems, we expect them to
be fixed before the code review starts.

It is a good idea to run the tests that apply to your change before opening a
pull request. It is useful to know [how to run the test suite][testing], and
how to run a subset of the tests.

Automated tests are in the process of being converted to [pytest][pytest], but
a lot of the old-style code remains. Contributors can write new tests in the
style of existing tests. They can also join MDN staff in converting to the new
style.  MDN staff is updating tests as we add or update functionality, so
seldom-updated code is more likely to have old-style tests. We expect a full
conversion to take a few more years.

We **avoid** old-style tests that use Django's
[TestCase testing classes][testcase], [fixture files][fixture_files] and
general-purpose factory functions like [get_user][get_user], [document][document],
and [revision][revision].

We **prefer** test functions, a small number of global
[pytest fixtures][pytest-fixtures] like [root_doc][root_doc] and
[wiki_user][wiki_user], adding application- and file-local fixtures
that customize the global fixtures, and using [assert][assert] for test
assertions.

[travisci]: https://travis-ci.com/mdn/kuma/pull_requests
[testing]: https://kuma.readthedocs.io/en/latest/tests.html#running-the-test-suite
[testcase]: https://docs.djangoproject.com/en/1.8/topics/testing/tools/#testcase
[fixture_files]: https://docs.djangoproject.com/en/1.8/topics/testing/tools/#fixture-loading
[eq]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/core/tests/__init__.py#L16
[ok]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/core/tests/__init__.py#L26
[get_user]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/core/tests/__init__.py#L36
[document]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/wiki/tests/__init__.py#L29
[revision]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/wiki/tests/__init__.py#L43
[pytest-fixtures]: https://docs.pytest.org/en/latest/fixture.html
[root_doc]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/conftest.py#L35
[wiki_user]: https://github.com/mdn/kuma/blob/6f31cbc22e72827e4832b3ed6ca542132bf41f83/kuma/conftest.py#L18
[assert]: https://docs.pytest.org/en/latest/assert.html
[pytest]: https://docs.pytest.org/en/latest/

We have a functional test suite that runs against a running MDN instance.
It can be challenging to run or alter these tests. A reviewer can determine if
changes are needed to functional tests, and if they need to be included in the
pull request or can be written (usually by staff) in a new PR.

Pull Requests
-------------
The author should include the bug number and a summary of the change as the
pull request title, and a description of the change as the pull request body.
A good commit message often makes a good PR message. An empty PR body is
rarely appropriate.

For bug fixes, it can be useful to include steps needed to reproduce the bug
in a development environment. It can also be useful to suggest manual tests
that a reviewer should try.

Do not double-submit a change as a patch in Bugzilla. If you like, you can
update the bug to link to your pull request and mark yourself as the assignee.

Code Reviews
------------
Code reviews help us maintain and improve code quality. It can also be
stressful to have your work criticized. Code reviewers should point out
good code as well as bad, be clear when changes are needed, and offer
suggestions for fixing code. Code authors should ask questions when a
suggestion is unclear, and ask for help if needed. On both sides, the review
should be about the code, not the person, and the [code of conduct][coc] must
be followed.

An MDN module [owner or peer][peers] must review and merge all pull requests.
Owner and peers are accountable for the quality of MDN code changes, and
often know when a change will have a wider than expected impact. In an
emergency, code may be merged without review, but a bug should be filed for a
follow-up review. There may also be exceptions for changes that don't impact
production.

[peers]: https://wiki.mozilla.org/Modules/All#MDN

Pull requests that modify the database must be reviewed by a module owner.
Changes to database tables are critical and may lead to loss of data. They are
also tricky to deploy, usually requiring multiple deployments.

Security changes should be reviewed outside of the public repository. They are
manually merged by a peer, and the commit should include a comment such as
``r=username`` to say who the reviewer was.

A reviewer may identify a "nit", which is a style preference that isn't
important enough to reject a pull request. Feel free to fix or ignore nits if
desired.

We use the following labels for pull requests:
* **manual merge**: This pull request is ready, but additional steps outside
  of code review are needed to merge it.
* **not ready**: The author says this pull request isn't ready to review. For
  example, it requires tests or documentation.

In general, the reviewer merges the pull request. When reviewing a PR from a
staff member, a reviewer may approve the PR with nits, and let the author
merge after fixing minor issues.

Deployment and Closing Bugs
---------------------------
MDN staff deploy new code one to three times a week. Currently deployed code can be seen on the
[What's Deployed?](https://whatsdeployed.io/s-HC0) page.

Once a bug fix is in production, the bug can be marked as RESOLVED:FIXED.
