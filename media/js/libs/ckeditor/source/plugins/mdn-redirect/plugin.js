/*
  Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)
  
  This plugin provides a popup for choosing a page to redirect to
*/

CKEDITOR.plugins.add('mdn-redirect', {  
  icons: 'mdn-redirect', // %REMOVE_LINE_%CORE

  init: function(editor) {
    // Add the dialog command.
    editor.addCommand('mdn-redirect', new CKEDITOR.dialogCommand('mdn-redirect'));

    // Register the command.
    editor.ui.addButton('MdnRedirect', {
      icon: 'mdn-redirect',
      label: gettext('Create a Redirect'),
      command: 'mdn-redirect',
      toolbar: 'links,100'
    });

    // Link the dialog resource.
    CKEDITOR.dialog.add( 'mdn-redirect', this.path + 'dialogs/mdn-redirect.js' );
  }
});