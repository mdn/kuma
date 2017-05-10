============
Localization
============

Kuma is localized with `gettext <http://www.gnu.org/software/gettext/>`_.
User-facing strings in the code or templates need to be marked for gettext
localization.

We use `Pontoon`_ to provide an easy interface to localizing these files.
Pontoon allows translators to use the web UI as well as download the PO files,
use whatever tool the translator feels comfortable with and upload it back to
Pontoon.

.. Note::

   We do not accept pull requests for updating translated strings. Please
   use `Pontoon`_ instead.


See the `Django documentation on Translations`_ for how to make strings
marked for translation in Python and templates.

Unless otherwise noted, run all the commands in this document inside the
development environment.

For Docker on Linux, set ``UID`` in ``.env`` or enter the environment with
``docker-compose run --rm --user $(id -u) web bash``, to ensure that created
files are owned by your development user.

.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/
.. _Django documentation on Translations: https://docs.djangoproject.com/en/dev/topics/i18n/translation/

Getting the localizations
=========================
Localizations are found in this repository under the ``locale`` folder.

The gettext portable object (``.po``) files need to be compiled into the
gettext machine object (``.mo``) files before translations will appear. This
is done once during initial setup and provisioning, but will be out of date
when the kuma locales are updated.

To refresh the translations, enter the development environment, then:

#. Compile the ``.po`` files::

    make localecompile

#. Update the static JavaScript translation catalogs::

    make compilejsi18n

#. Collect the built files so they are served with requests::

    make collectstatic

.. _Update the Localizations:

Updating the localizations
==========================
When localizable strings are added, changed, or removed in the code, they need
to be gathered into ``.po`` files for translation.

.. Note::

   This work is done only during the preparation to push to production. You do
   not need to do this for your PR.


To update the localizations:

#. Update ``kuma/settings/common.py``, and bump the version in
   ``PUENTE['VERSION']``.

#. Inside the development environment, extract and rebuild the translations::

    make localerefresh

#. On the host system, review the changes to source English strings::

    git diff locale/templates/LC_MESSAGES

#. Finally, commit the files::

    git add --all locale
    git commit

Adding a new locale (UI strings)
================================
The process for getting a new locale on MDN is documented at
`Starting a new MDN localization`_. One step is to enable translation of the
UI strings.

This example shows adding a Bulgarian (bg) locale. Change ``bg`` to the locale
code of the language you are adding.

#. `Update the Localizations`_ as above, so that your commit will be limited to
   the new locale.

#. Add the locale to ``CANDIDATE_LANGUAGES`` in ``kuma/settings/common.py``.

#. Download the latest ``languages.json`` from
   https://product-details.mozilla.org/1.0/languages.json
   and place it at ``kuma/settings/languages.json``.

#. Add the locale to ``translate_locales.html`` and the ``locale/`` folder::

    make locale LOCALE=bg

#. Generate the compiled files for all the locales, including the new one::

    make localerefresh

#. Commit the changes to ``locale``,
   ``jinja2/includes/translate_locales.html``, and ``kuma/settings``.
   The other locales should include a new string representing the new language.

When the change is merged to master, enable the language in Pontoon_ as well,
and notify the language community to start UI translation.

.. _Starting a new MDN localization: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Localize/Starting_a_localization

Adding a New Locale (Page Translations)
=======================================
Once the new translation community has completed the rest of the process for
`starting a new MDN localization`_, it is time to enable the language for page
translations:

#. Move the locale from ``CANDIDATE_LANGUAGES`` to ``MDN_LANGUAGES`` in
   ``kuma/settings/common.py``.

#. Restart the web server and verify that Django loads the new locale without
   errors by visiting the locale's home page, for example
   http://localhost:8000/bg/.

#. Commit the change to ``kuma/settings/common.py``.

When the change is merged and deployed, inform the localization lead and the
community that they can begin translating content.
