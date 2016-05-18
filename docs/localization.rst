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

Run the Django management command to update the static JavaScript
translation catalogs::

    python manage.py compilejsi18n

Updating the Localizations
==========================
#.  Run the following in the virtual machine (see :doc:`installation`)::

        $ python manage.py extract
        $ python manage.py merge

#.  Commit the files::

        $ cd locale
        $ git add -A
        $ git commit -m "MDN string update YYYY-MM-DD"

Adding a new Locale
===================

#. Add the locale to `MDN_LANGUAGES` in `settings.py`

#. Add the locale to the `locale/` folder by following the instructions in
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

#.  Update the `product_details_json.tar.gz` files used by
    `our Travis install script`_::

        $ python manage.py update_product_details
        $ tar -czf etc/data/product_details_json.tar.gz ../product_details_json/

#.  Commit the changes to `settings.py` and `product_details_json.tar.gz`


.. _our Travis install script: https://github.com/mozilla/kuma/blob/master/scripts/travis-install
