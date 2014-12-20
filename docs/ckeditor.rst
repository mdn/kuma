========
CKEditor
========

The Mozilla Developer Network uses a WYSIWYG editor called
`CKEditor <http://ckeditor.com>`_.  CKEditor is an open source
utility which brings the power of rich text editing to the web.  This
document details how to update CKEditor within the MDN codebase.

Building CKEditor
-----------------

Building CKEditor is quite easy!

*  `cd media/js/libs/ckeditor/source/` - Go to the working directory for CKEditor source
*  `git submodule update --init --recursive` -  Update submodules for CKEditor
*  `./build.sh` - Run the build script to build served CKEditor files

Portions of the build process will take a few minutes so don't expect an immediate result

Updating CKEditor Version
-------------------------

To update the CKEditor versions, you'll need to navigate to the CKEditor submodule and
use git to check out a different tag of the project.

Updating will be important so that we can keep MDN secure and functional as CKEditor updates.
