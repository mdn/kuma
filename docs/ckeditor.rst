========
CKEditor
========

The Mozilla Developer Network uses a WYSIWYG editor called
`CKEditor <http://ckeditor.com>`_.  CKEditor is an open source
utility which brings the power of rich text editing to the web.  This
document details how to update CKEditor within the MDN codebase.

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

* `descriptionlist <https://github.com/Reinmar/ckeditor-plugin-descriptionlist>`_
* `scayt <https://github.com/WebSpellChecker/ckeditor-plugin-scayt>`_
* `wsc <https://github.com/WebSpellChecker/ckeditor-plugin-wsc>`_

Change to CKEditor plugins which are bundled into Kuma should be made in the
directory `/kuma/static/js/libs/ckeditor/source/ckeditor/plugins/ <https://github.com/mozilla/kuma/tree/master/kuma/static/js/libs/ckeditor/source/plugins>`_.

Once you've made changes to a plugin, be sure to build the editor and the static
resources again, as described in `Building CKEditor`_.
