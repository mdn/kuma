===============
Feature toggles
===============

MDN uses `feature toggles`_ to integrate un-finished feature changes as early
as possible, and to control the behavior of finished features.

Some site features are controlled using `django-waffle`_. You control these
features in the django admin site's `waffle section`_.

Waffle features
===============

Switches
--------

`Waffle switches`_ are simple booleans - they are either on or off.

* ``welcome_email`` - Send welcome email to new user registrations.
* ``developer_needs`` - Enable/disable the developer needs survey banner

.. _feature toggles: https://en.wikipedia.org/wiki/Feature_toggle
.. _django-waffle: https://waffle.readthedocs.io/en/latest/
.. _waffle section: http://localhost.org:8000/admin/waffle/
.. _Waffle switches: https://waffle.readthedocs.io/en/latest/types/switch.html
