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

.. _add-wiki-doc:

Create the Sample Database
==========================
These scraping tools are used to create a sample database of public
information, which is used for development environments and functional
testing without exposing any private production data.

When it is time to create a new sample database, an MDN staff person runs
the commamd in the the container::

    time scripts/create_sample_db.sh

This takes 2 to 2½ hours with a good internet connection.  This is then
uploaded to the ``mdn-downloads`` site:

* https://mdn-downloads.s3-us-west-2.amazonaws.com/index.html
* https://mdn-downloads.s3-us-west-2.amazonaws.com/mdn_sample_db.sql.gz

This uses the specification at ``etc/sample_db.json``, which includes the
sources for scraping, as well as fixtures needed for a working development
and testing environment.

Load Custom Data
================
The ``sample_mdn`` command does the work of creating the sample database. It
can also be used with a different specification to load custom fixtures and
scrape additional data for your local environment.

For example, loading a new sample database wipes out existing data, so you'll
need to run the instructions in :ref:`enable-github-auth` again. Instead, you
can create a specification for your development user and GitHub OAuth
application::

    {
      "sources": [
        ["user",
         "my_username",
         {
           "social": true,
           "email": "my_email@example.com"
         }
        ]
      ],
      "fixtures": {
        "users.user": [
          {
            "username": "my_username",
            "email": "my_email@example.com",
            "is_staff": true,
            "is_superuser": true
          }
        ],
        "socialaccount.socialapp": [
          {
            "name": "GitHub",
            "client_id": "client_id_from_github",
            "secret": "secret_from_github",
            "provider": "github",
            "sites": [ [1] ]
          }
        ],
        "socialaccount.socialaccount": [
          {
            "uid": "uid_from_github",
            "user": ["my_username"],
            "provider": "github"
          }
        ],
        "account.emailaddress": [
          {
            "user": ["my_username"],
            "email": "my_email@example.com",
            "verified": true
          }
        ]
      }
    }

To use this, you'll need to replace the placeholders:

* ``my_username`` - your MDN username
* ``my_email@example.com`` - your email address, verified on GitHub
* ``client_id_from_github`` - from your GitHub OAuth app
* ``secret_from_github`` - from your GitHub OAuth app
* ``uid_from_github`` - from your MDN SocialAccount_

Save it, for example as ``my_data.json``, and, after loading the sample
database, load the extra data::

    ./manage.py sample_mdn my_data.json

This will allow you to quickly log in again using GitHub auth after loading the
sample database.

.. _SocialAccount: http://localhost:8000/admin/socialaccount/socialaccount/

Anonymized Production Data
==========================
The production database contains confidential user information, such as email
addresses and authentication tokens, and it is not distributed.  We try to make
the sample database small but useful, and provide scripts to augment it for
specific uses, reducing the need for production data.

Production-scale data is occasionaly needed for development, such as testing
the performance of data migrations and new algorithms, and for the
`staging site`_.  In these cases, we generate an anonymized copy of production
data, which deletes authentication keys and anonymizes user records.

This is generated with the script ``scripts/clone_db.py`` on a recent backup of
the production database. You can see a faster and less resource-intensive
version of the process by running it against the sample database::

    scripts/clone_db.py -H mysql -u root -p kuma -i mdn_sample_db.sql.gz anon_db

This will generate a file ``anon_db-anon-20170606.sql.gz``, where the date is
today's date.  To check that the anonymize script ran correctly, load the
anonymized database dump and run the check script::

    zcat anon_db-anon-20170606.sql.gz | ./manage.py dbshell
    cat scripts/check_anonymize.sql | ./manage.py dbshell

This runs a set of counting queries that should return 0 rows.

A similar process is used to anonymize a recent production database dump.
The development environment is not tuned for the I/O, memory, and disk
requirements, and will fail with an error.  Instead, a host-installed version
of MySQL is used, with the custom collation.  The entire process, from getting
a backup to uploading a confirmed anonymized database, takes about half a day.

We suspect that a clever user could de-anonymize the data in the full
anonymized database, so we do not distribute it, and try to limit our own use
of the database.

.. _`staging site`: https://developer.allizom.org
