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

For Docker, enter the environment with
``docker-compose run --rm --user $(id -u) web bash``, to ensure that created
files are owned by your development user.

For Vagrant, enter the environment with ``vagrant ssh``.

.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/
.. _Django documentation on Translations: https://docs.djangoproject.com/en/dev/topics/i18n/translation/

Getting the Localizations
=========================
Localizations are found in this repository under the ``locale`` folder.

The gettext portable object (``.po``) files need to be compiled into the
gettext machine object (``.mo``) files before translations will appear.  This
is done once during initial setup and provisioning, but will be out of date
when the Kuma locales are updated.

To refresh the translations, enter the development environment, then:

#. Compile the ``.po`` files::

    make localecompile

#. Update the static JavaScript translation catalogs::

    make compilejsi18n

#. Collect the built files so they are served with requests::

    make collectstatic

.. _Update the Localizations:

Updating the Localizations
==========================
When localizable strings are added, changed, or removed in the code, they need
to be gathered into ``.po`` files for translation.

To update the localizations:

#. Inside the development environment, extract and rebuild the translations::

    make localerefresh

#. On the host system, review the changes to source English strings::

    git diff locale/templates/LC_MESSAGES

#. Finally, commit the files::

    git add --all locale
    git commit -m "MDN string update YYYY-MM-DD"

Adding a new Locale
===================
This example shows adding a Bulgarian (bg) locale. Change ``bg`` to the locale
code of the language you are adding.

#. `Update the Localizations`_ as above, so that your commit will be limited to
   the new locale.

#. Add the locale to ``MDN_LANGUAGES`` in ``kuma/settings/common.py``

#. Download the latest ``languages.json`` from
   https://product-details.mozilla.org/1.0/languages.json
   and place it at ``kuma/settings/languages.json``.

#. Add the locale to the ``locale/`` folder::

    make locale LOCALE=bg

#. Generate the compiled filed for all the locales, including the new one::

    make localerefresh

#. Restart the web server and verify that Django loads the new locale without
   errors by visiting the locale's home page, for example
   http://localhost:8000/bg/ (https://developer-local.allizom.org/bg/
   if you are using Vagrant)

#. Commit the changes to ``locale/bg`` and ``kuma/settings``.
   Verify that the other locales are just timestamp updates before reverting
   them.

#. BONUS: Use the  `debug translation feature`_ of ``dennis-cmd`` to test a
   fake translation of the locale::

        cd locale
        dennis-cmd locale/bg/LC_MESSAGES/django.po
        ./compile-mo.sh bg  # Edit and repeat until any errors are fixed
        cd ..
        make localerefresh

   Restart the django server and re-visit the new locale to verify it shows
   "translated" strings in the locale.  Don't commit the debug translation.

.. _our Travis install script: https://github.com/mozilla/kuma/blob/master/scripts/travis-install
.. _debug translation feature: http://dennis.readthedocs.io/en/latest/translating.html
