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

* ``welcome_email`` - send welcome email to new user registrations
* ``wiki_force_immediate_rendering`` - force wiki pages to render immediately in
  the same http request in which they are saved (not in a background process)
* ``wiki_error_on_delete`` - throw an error if a user tries to delete a page
* ``render_stale_document_async`` - render stale documents in a background
  sub-task

Flags
-----

`Waffle flags`_ control behavior by specific users, groups, percentages, and
other advanced criteria.

* ``events_map`` - show the map on the events page
* ``search_explanation`` - show search results scoring details
* ``search_doc_navigator`` - show the search doc navigator feature
* ``search_drilldown_faceting`` - treat search filters as "drill-down" filters
  - i.e., combine them with "AND" logic
* ``search_suggestions`` - show the advanced search filter suggestions
  interface
* ``registration_disabled`` - enable/disable new user registration
* ``social_account_research`` - enable/disable social account research on the
  "Sign in to Edit" page
* ``kumaediting`` - enable/disable wiki editing
* ``kumabanned`` - (deprecated) added to users to mark them as banned
* ``enable_customcss`` - enable/disable Template:CustomCSS styles in wiki pages
* ``top_contributors`` - enable/disable the "Top Contributors" feature on wiki
  pages
* ``page_move`` - enable/disable page move feature

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
