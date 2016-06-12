===============
Feature Toggles
===============

MDN uses `feature toggles`_ to integrate un-finished feature changes as early
as possible, and to control the behavior of finished features.

Some site features are controlled using `django-waffle`_. You control these
features in the django admin site's `waffle section`_.

Some site features are controlled using `constance`_. You control these
features in the django admin site's `constance section`_.

Waffle Features
===============

Switches
--------

`Waffle switches`_ are simple booleans - they are either on or off.

* ``application_ACAO`` - Enable Access-Control-Allow-Origin=0 header
* ``dumb_doc_urls`` - (deprecated) Disable the render-time changing of /docs/
  URLs to the equivalent Zone URLs (see `PR 3331`_ for reasoning).
* ``enable_optimizely`` - Enable the Optimizely JavaScript
* ``store_revision_ips`` - Save request data, including the IP address, to
  enable marking revisions as spam.
* ``welcome_email`` - send welcome email to new user registrations
* ``wiki_error_on_delete`` - throw an error if a user tries to delete a page
* ``wiki_force_immediate_rendering`` - force wiki pages to render immediately
  in the same http request in which they are saved (not in a background
  process)

Flags
-----

`Waffle flags`_ control behavior by specific users, groups, percentages, and
other advanced criteria.

* ``compat_api`` - View the new API-backed compatibility tables
* ``kumabanned`` - (deprecated) added to users to mark them as banned
* ``kumaediting`` - enable/disable wiki editing
* ``page_move`` - (deprecated) enable/disable page move feature
* ``registration_disabled`` - enable/disable new user registration
* ``search_doc_navigator`` - show the search doc navigator feature
* ``search_suggestions`` - show the advanced search filter suggestions
  interface
* ``section_edit`` - Show section edit buttons
* ``spam_admin_override`` - Tell Akismet that edits are never spam
* ``spam_spammer_override`` - Tell Akismet that edits are always spam
* ``spam_testing_mode`` - Tell Akismet that edits are tests, not real content
* ``spam_checks_enabled`` - toggle spam checks site wide
* ``spam_submissions_enabled`` - toggle Akismet spam/spam submission ability
* ``wiki_samples`` - Add button to open samples in Codepen or jsFiddle
* ``wiki_spam_exempted`` - exempt users and user groups from checking
  submissions for spam
* ``wiki_spam_training`` - Call Akismet to check submissions, but don't block
  due to detected spam or Akismet errors.

Constance Features
------------------

Constance configs let us set operational *values* for certain features in the
database - so we can control them without changing code. They are all listed
and documented in the admin site's `constance section`_.

.. _feature toggles: https://en.wikipedia.org/wiki/Feature_toggle
.. _django-waffle: http://waffle.readthedocs.org/en/latest/
.. _waffle section: https://developer-local.allizom.org/admin/waffle/
.. _constance: https://github.com/comoga/django-constance
.. _constance section: https://developer-local.allizom.org/admin/constance/config/
.. _Waffle switches: http://waffle.readthedocs.org/en/latest/types/switch.html
.. _Waffle flags: http://waffle.readthedocs.org/en/latest/types/flag.html
.. _PR 3331: https://github.com/mozilla/kuma/pull/3331
