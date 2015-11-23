============
Localization
============

Kuma is localized with `gettext <http://www.gnu.org/software/gettext/>`_.
User-facing strings in the code or templates need to be marked for gettext
localization.

We use `Pontoon <https://pontoon.mozilla.org/>`_ or
`Verbatim <http://localize.mozilla.org/>`_ to provide an easy interface
to localizing these files. Localizers are also free to download the PO files
and use whatever tool they are comfortable with.

See the `Django documentation on Translations`_ for how to make strings
marked for translation in Python and templates.

.. _Django documentation on Translations: https://docs.djangoproject.com/en/dev/topics/i18n/translation/

Getting the Localizations
=========================

Localizations are found in this repository under the ``locale`` folder.

Run the Django management command to update the static JavaScript
translation catalogs::

    python manage.py compilejsi18n

Updating the Localizations
==========================
When we add or update strings, we need to update `Verbatim <http://localize.mozilla.org/>`_
templates and PO files for localizers. If you commit changes to the
locale files without updating Verbatim, localizers will have merge head-aches.

#.  Run the following in the virtual machine (see :doc:`installation`)::

        $ python manage.py extract
        $ python manage.py merge
        $ rm locale/**/*.po~  # Remove .po backup files created by merge.

#.  Commit the files.

        $ cd locale
        $ git add -A
        $ git commit -m "MDN string update YYYY-MM-DD"

.. note:: You need verbatim permissions for the following. If you don't have permissions, email `groovecoder <mailto:lcrouch@mozilla.com>`_ or `mathjazz <mailto:matjaz@mozilla.com>`_ to do the following ...

#.  Go to the `MDN templates on Verbatim
    <https://localize.mozilla.org/templates/mdn/>`_

#.  Click 'Update all from VCS'

#.  ssh to sm-verbatim01 (See `L10n:Verbtim
    <https://wiki.mozilla.org/L10n:Verbatim>`_ on wiki.mozilla.org)

#.  Update all locales against templates::

        sudo su verbatim
        cd /data/www/localize.mozilla.org/verbatim/pootle_env/Pootle
        POOTLE_SETTINGS=localsettings.py python2.6 manage.py
        update_against_templates --project=mdn -v 2

Adding a new Locale
===================

#.  Follow `the "Add locale" instructions on wiki.mozilla.org
    <https://wiki.mozilla.org/L10n:Verbatim#Adding_a_locale_to_a_Verbatim_project>`_.

#.  Update `languages.json` file via product details::

        $ ./manage.py update_product_details
        $ cp ../product_details_json/languages.json kuma/languages.json

#.  Add the locale to `MDN_LANGUAGES` in `settings.py`

#.  Add the locale to the `locale/` folder by following the instructions in
   `locale/README.txt`.

#. Create the `jsi18n` file for the new locale::

        $ ./manage.py compilejsi18n

#.  Verify django loads new locale without errors by visiting the locale's home
    page. E.g., https://developer-local.allizom.org/ml/

#.  BONUS: Use `podebug` to test a fake translation of the locale::

        $ cd locale
        $ podebug --rewrite=bracket templates/LC_MESSAGES/django.pot ml/LC_MESSAGES/django.po
        $ ./compile-mo.sh .

    Restart the django server and re-visit the new locale to verify it shows
    "translated" strings in the locale.

#.  Update the `locale.tar.gz` and `product_details_json.tar.gz` files used by
    `our Travis install script`_::

        $ python manage.py update_product_details
        $ tar -czf etc/data/product_details_json.tar.gz ../product_details_json/
        $ tar -czf etc/data/locale.tar.gz locale/

#.  Commit the changes to `settings.py`, `locale.tar.gz`, and
    `product_details_json.tar.gz`


.. _our Travis install script: https://github.com/mozilla/kuma/blob/master/scripts/travis-install
