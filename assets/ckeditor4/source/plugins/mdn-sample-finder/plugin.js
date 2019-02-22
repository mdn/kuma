/*
  Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)
  
  This plugin provides a popup for choosing a demo from a given page.
*/

'use strict';

CKEDITOR.plugins.add('mdn-sample-finder', {
  icons: 'mdn-sample-finder-moono', // %REMOVE_LINE_%CORE

  init: function(editor) {
    // Add the dialog command.
    editor.addCommand('mdn-sample-finder', new CKEDITOR.dialogCommand('mdn-sample-finder'));

    // Register the button.
    var label = gettext('Insert Code Sample iFrame');
    editor.ui.addButton('mdn-sample-finder', {
      icon: 'mdn-sample-finder-moono',
      label: label,
      toolbar: 'blocks,220',
      command: 'mdn-sample-finder'
    });

    // Link the dialog resource.
    CKEDITOR.dialog.add('mdn-sample-finder', this.path + 'dialogs/mdn-sample-finder.js');
  }
});