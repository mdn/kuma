'use strict';

CKEDITOR.plugins.add('texzilla', {
  icons: 'texzilla', // %REMOVE_LINE_CORE%

  init: function(editor) {
    CKEDITOR.dialog.add('texzilla', this.path + 'dialogs/texzilla.js');

    editor.addCommand('texzilla', new CKEDITOR.dialogCommand('texzilla'));
    editor.ui.addButton('texzilla', {
      label: 'Insert MathML based on (La)TeX',
      command: 'texzilla',
      toolbar: 'insert'
    });
  }
});
