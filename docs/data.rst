============
Getting Data
============

A Kuma instance without data is useless. You can view the front page, but
almost all interactive testing requires users, wiki documents, and other data.

The Sample Database
===================
The sample database has a minimal set of data, based on production data, that
is useful for manual and automated testing.  This includes:

- All documents linked from the English homepage, including:

  - Translations
  - Some historical revisions
  - Minimal author profiles for revisions

- Additional documents for automated testing and feature coverage
- Good defaults for contance variables ``KUMASCRIPT_TIMEOUT`` and
  ``KUMASCRIPT_MAX_AGE``
- Waffle flags and switches
- Search filters and tags (but not a search index, which must be created
  locally - see :ref:`indexing-documents`)
- The Mozilla Hacks feed
- Test users, with appropriate groups and permissions:

  - ``test-super`` - A user with full permissions
  - ``test-moderator`` - A staff content moderator
  - ``test-new`` - A regular user account
  - ``test-banned`` - A banned user
  - ``viagra-test-123`` - An unbanned spammer

Test accounts can be accessed by entering the password ``test-password`` in the
`Django admin`_, and then returning to the site_.

See :ref:`provision-the-database` for instructions on loading the latest sample
database.

.. _`Django admin`: localhost:8000/admin/login/?next=/
.. _site: http://localhost:8000/en-US/

Add an MDN User
===============
If you need a user profile that is not in the sample database, you can scrape
it from production or another Kuma instance, using the ``scrape_user``
command.  In the container (after ``make bash`` or similar), run the
following, replacing ``username`` with the desired user's username::

    ./manage.py scrape_user username
    ./manage.py scrape_user https://developer.mozilla.org/en-US/profiles/username

Some useful options:

``--email user@example.com``
  Set the email for the user, which can't be scraped from the profile. With
  the correct email, the user's profile image will be available.

``--social``
  Scrape social data for the user, which is not scraped by default

``--force``
  If a user exists in the current database, update it with scraped data.

For full options, see ``./manage.py scrape_user --help``

A local user can be promoted to staff with the command::

    ./manage.py ihavepower username --password=password

Add an MDN Wiki Document
========================
If you need a wiki page that is not in the sample database, you can scrape it
from production or another Kuma instance, using the ``scrape_document``
command.  In the container (after ``make bash`` or similar), run the
following, using the desired URL::

    ./manage.py scrape_document https://developer.mozilla.org/en-US/docs/Web/CSS/display

Scraping a document includes:

- The parent documents (such as ``Web`` and ``Web/CSS`` for ``Web/CSS/display``)
- The zone, if needed
- A revision for each document, and the author for each revision
- The English variant, if a translation is requested
- Redirects, if a page move is detected

It does not include:

- Attachment data, or the attachments themselves. These will continue to use
  production URLs.

Some useful options:

``--revisions REVS``
  Scrape more than one revision

``--translations``
  Scrape the translations of a page as well

``--depth DEPTH``
  Scrape one or more levels of child pages as well

``--force``
  Refresh an existing Document, instead of skipping

For full options, see ``./manage.py scrape_document --help``
