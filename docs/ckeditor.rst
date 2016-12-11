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

To rebuild CKEditor from a ``vagrant ssh`` shell (or locally if you have Java
installed)::

    cd kuma/static/js/libs/ckeditor/source/
    ./build.sh

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
