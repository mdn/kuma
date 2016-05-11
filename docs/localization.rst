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

.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/
.. _Django documentation on Translations: https://docs.djangoproject.com/en/dev/topics/i18n/translation/

Getting the Localizations
=========================

Localizations are found in this repository under the ``locale`` folder.

The gettext portable object (.po) files need to be compiled into the gettext
machine object (.mo) files before translations will appear. This is performed
during vagrant provisioning but if you need to update them at any time you can
compile the files via the following command within the vagrant environment::

    make localecompile

To update the static JavaScript translation catalogs, run the following django
management command::

    make compilejsi18n

The above command will build the JavaScript l10n files in the ``build/locale/``
folder. To collect these files for serving you must run the
``collectstatic`` command::

    make collectstatic

Updating the Localizations
==========================
#.  Run the following in the virtual machine (see :doc:`installation`)::

        make localerefresh

#.  Commit the files::

        git add --all locale
        git commit -m "MDN string update YYYY-MM-DD"

Adding a new Locale
===================
The examples shows adding a Bulgarian (bg) locale. Change ``bg`` to the locale
code of the language you are adding.

#. Update the Localizations as above, so that your commit will be limited to
   the new locale.

#. Add the locale to ``MDN_LANGUAGES`` in ``kuma/settings/common.py``

#. Add the locale to the ``locale/`` folder::

        make locale LOCALE=bg

#. Generate the compiled filed for all the locales, including the new one::

        make localerefresh

#. Restart the web server and verify that Django loads the new locale without
   errors by visiting the locale's home page, for example
   https://developer-local.allizom.org/bg/

#. Update the ``product_details_json.tar.gz`` files used by
   `our Travis install script`_::

        python manage.py update_product_details
        tar -czf etc/data/product_details_json.tar.gz ../product_details_json/

#. Commit the changes to ``locale/bg``, ``kuma/settings/common.py`` and
   ``etc/data/product_details_json.tar.gz``. Verify that the other locales are
   just timestamp updates before reverting them.

#. BONUS: Use ``podebug`` to test a fake translation of the locale::

        cd locale
        podebug --rewrite=bracket templates/LC_MESSAGES/django.pot bg/LC_MESSAGES/django.po
        ./compile-mo.sh bg  # Edit and repeat until any errors are fixed
        cd ..
        make localerefresh

   Dennis also has a `debug translation feature`_ you could use instead::

        cd locale
        dennis-cmd locale/bg/LC_MESSAGES/django.po
        ./compile-mo.sh bg  # Edit and repeat until any errors are fixed
        cd ..
        make localerefresh

   Restart the django server and re-visit the new locale to verify it shows
   "translated" strings in the locale.  Don't commit the debug translation.

.. _our Travis install script: https://github.com/mozilla/kuma/blob/master/scripts/travis-install
.. _debug translation feature: http://dennis.readthedocs.io/en/latest/translating.html
