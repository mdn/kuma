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

The strings are stored in a separate repository,
https://github.com/mozilla-l10n/mdn-l10n

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

Build the localizations
=======================
Localizations are found in this repository under the ``locale`` folder.
This folder is a `git submodule`, linked to the mdn-l10n_ repository.

The gettext portable object (``.po``) files need to be compiled into the
gettext machine object (``.mo``) files before translations will appear. This
is done once during initial setup and provisioning, but will be out of date
when the kuma locales are updated.

To refresh the translations, first update the submodule in your host system::

    git submodule update --init --depth=10 locale

Next, enter the development environment, then:

#. Compile the ``.po`` files::

    make localecompile

#. Update the static JavaScript translation catalogs::

    make compilejsi18n

#. Collect the built files so they are served with requests::

    make collectstatic

.. _`git submodule`: https://www.git-scm.com/docs/git-submodule
.. _`mdn-l10n`: https://github.com/mozilla-l10n/mdn-l10n

.. _Update the Localizations:

Update the localizations in Kuma
================================

To get the latest localization from Pontoon users, you need to update the
submodule.

.. Note::

   This task is done by MDN staff or by automated tools during the push to
   production. You should not do this as part of a code-based Pull Request.

On the host system:

#. Create a new branch from kuma master::

    git remote -v | grep origin  # Should be main kuma repo
    git fetch origin
    git checkout origin/master
    git checkout -b update-locales  # Pick your own name. Can be combined
                                    # with updating the kumascript submodule.

#. Update the locale submodule to master::

    cd locale
    git fetch
    git checkout origin/master
    cd ..

#. Commit the update::

    git commit locale -m "Updating localizations"

#. Push to GitHub (your fork or main repository), and open a Pull Request.

It is possible to break deployments by adding a bad translation. The TravisCI_
job ``TOXENV=locales`` will test that the deployment should pass, and should
pass before merging the PR.

.. _`TravisCI`: https://travis-ci.com/mdn/kuma

.. _Updating the localizable strings in Pontoon:

Update the localizable strings in Pontoon
=========================================
When localizable strings are added, changed, or removed in the code, they need
to be gathered into ``.po`` files for translation. The TravisCI_ job
``TOXENV=locales`` attempts to detect when strings change by displaying the
differences in ``locale/templates/LC_MESSAGES/django.pot``, but only when a
``msgid`` changes.

When this happens, the strings need to be exported to the mdn-l10n_ repository
so that they are available in Pontoon. If done incorrectly, then the work of
localizers can be lost. This task is done by staff when
:ref:`preparing for deployment <Pre-Deployment>`.

Add a new locale to Pontoon
===========================
The process for getting a new locale on MDN is documented at
`Starting a new MDN localization`_. One step is to enable translation of the
UI strings. This will also enable the locale in development environments and
on https://developer.allizom.org.

.. Note::

   This task is done by MDN staff.

This example shows adding a Bulgarian (bg) locale. Change ``bg`` to the locale
code of the language you are adding.

#. `Updating the localizable strings in Pontoon`_ as above, so that your
   commit will be limited to the new locale.

#. In ``kuma/settings/common.py``, add the locale to ``ACCEPTED_LOCALES`` and
   ``CANDIDATE_LOCALES``, and increase ``PUENTE['VERSION']``.

#. Download the latest ``languages.json`` from
   https://product-details.mozilla.org/1.0/languages.json
   and place it at ``kuma/settings/languages.json``.

#. Add the locale to ``translate_locales.html`` and the ``locale/`` folder::

    make locale LOCALE=bg

#. Generate the compiled files for all the locales, including the new one::

    make localerefresh

#. Restart the web server and verify that Django loads the new locale without
   errors by visiting the locale's home page, for example
   http://localhost:8000/bg/.

#. Commit the locale submodule and push to `mdn-l10n`_, as described above in
   `Updating the localizable strings in Pontoon`_.  The other locales should
   include a new string representing the new language.

#. (Optional) Generate migrations that includes the new locale::

   ./manage.py makemigrations users wiki --name update_locale

#. Commit the changes to ``locale``,
   ``jinja2/includes/translate_locales.html``, and ``kuma/settings``, and open
   a Pull Request.

#. Enable the language in Pontoon_, and notify the language community to start
   UI translations.

.. _Starting a new MDN localization: https://developer.mozilla.org/en-US/docs/MDN/Contribute/Localize/Starting_a_localization

Enable a new locale on MDN
==========================
Once the new translation community has completed the rest of the process for
`starting a new MDN localization`_, it is time to enable the language for page
translations:

.. Note::

   This task is done by MDN staff.

#. Remove the locale from ``CANDIDATE_LOCALES`` in
   ``kuma/settings/common.py``. Ensure it remains in ``ACCEPTED_LOCALES``.

#. Restart the web server and verify that Django loads the new locale without
   errors by visiting the locale's home page, for example
   http://localhost:8000/bg/.

#. Commit the change to ``kuma/settings/common.py`` and open a Pull Request.

When the change is merged and deployed, inform the localization lead and the
community that they can begin translating content.
