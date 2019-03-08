========
CKEditor
========

MDN Web Docs uses a WYSIWYG editor called CKEditor_.  CKEditor
is an open source utility which brings the power of rich text editing to the
web.  This document details how to update CKEditor within the MDN codebase.

Building CKEditor
-----------------
To rebuild CKEditor, run this on the host system::

    cd kuma/static/js/libs/ckeditor/
    ./docker-build.sh  # Creates a Java container, builds CKEditor
    docker-compose exec web make build-static

This builds CKEditor within a Docker VM, using the Java ``ckbuilder`` tool
from CKSource, then builds static resources so that the updated editor
is installed where it belongs.

To rebuild CKEditor locally, if you have Java installed::

    cd kuma/static/js/libs/ckeditor/source/
    ./build.sh
    docker-compose exec web make build-static

Portions of the build process will take a few minutes so don't expect an
immediate result.

Updating CKEditor
-----------------
To update the CKEditor version, you'll need to edit ``build.sh`` and change
the value of ``CKEDITOR_VERSION``.  Updating is important to keep MDN in sync
with CKEditor's functional and security updates.

Updating CKEditor plugins
-------------------------
Some plugins are maintained by MDN staff in the Kuma repo. Others are updated
to the tag or commit number specified in ``build.sh``:

* descriptionlist_
* scayt_
* wsc_
* wordcount_

Change to CKEditor plugins which are bundled into Kuma should be made in the
directory `/kuma/static/js/libs/ckeditor/source/ckeditor/plugins/`_.

Once you've made changes to a plugin, be sure to build the editor and the static
resources again, as described in `Building CKEditor`_.

Interactively developing CKEditor plugins
-----------------------------------------
For small changes, it may be fastest to rebuild CKEditor for each change. For
more involved changes, you can load CKEditor in development mode.

To interactively develop CKEditor plugins, first download the CKEditor source
code on the host system::

    cd kuma/static/js/libs/ckeditor/source/
    ./build.sh --download

Enable development mode by adding a line to ``.env``::

    CKEDITOR_DEV=True

Restart Docker with ``docker-compose restart web`` to apply the new setting. This
will switch to a mode where plugins are loaded dynamically, based on the list
in `/kuma/wiki/jinja2/wiki/includes/ckeditor_scripts.html`_, and you can see
your changes by reloading the browser.

When you are done, disable development mode in ``.env``::

    CKEDITOR_DEV=False  # Or comment out the line

Restart Docker with ``docker-compose restart web``, and follow the instructions
above for `Building CKEditor`_, to delete the CKEditor source code and
rebuild CKEditor with your changes.


Committing Changes
------------------
When updating CKEditor, adding a plugin, or changing the configuration,
CKEditor should be rebuilt, and the results added to a new pull request. We
currently do not check-in CKEditor source, but do add third-party plugin
sources. We check in the "built" files, which combine CKEditor with plugins and
configuration, so that they do not need to be rebuilt by the static files
process. This is enforced by ``.gitignore``, so ``git add`` can be used::

    git add kuma/static/js/libs/ckeditor/

Reviewers should rebuild CKEditor to ensure this was done correctly. Building
is not atomic, because a hex-encoded timestamp is embedded in some minified
files::

    kuma/static/js/libs/ckeditor/build/ckeditor/ckeditor.js
    skins/moono/editor.css
    skins/moono/editor_*.css

Small changes (with big diffs) to these files are expected. Changes to other
files are not expected.

.. _CKEditor: http://ckeditor.com
.. _descriptionlist: https://github.com/Reinmar/ckeditor-plugin-descriptionlist
.. _scayt: https://github.com/WebSpellChecker/ckeditor-plugin-scayt
.. _wsc: https://github.com/WebSpellChecker/ckeditor-plugin-wsc
.. _wordcount: https://github.com/w8tcha/CKEditor-WordCount-Plugin
.. _`/kuma/static/js/libs/ckeditor/source/ckeditor/plugins/`:
   https://github.com/mozilla/kuma/tree/master/kuma/static/js/libs/ckeditor/source/plugins
.. _`/kuma/wiki/jinja2/wiki/includes/ckeditor_scripts.html`:
   https://github.com/mozilla/kuma/tree/master/kuma/wiki/jinja2/wiki/includes/ckeditor_scripts.html
