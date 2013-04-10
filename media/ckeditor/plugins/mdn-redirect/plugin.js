/*
	Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)
	
	This plugin provides a popup for choosing a page to redirect to
*/
CKEDITOR.plugins.add('mdn-redirect', {

	requires: ['selection'],
	
	init: function(editor) {

		// Add the dialog command
		editor.addCommand( 'mdn-redirect', new CKEDITOR.dialogCommand('mdn-redirect') );

		// Register the command
		var label = gettext('Create a Redirect');
		editor.ui.addButton('mdn-redirect', {
			label: label,
			title: label,
			className: 'cke_button_mdn_redirect',
			command: 'mdn-redirect',
			iconOffset: 14,
			icon: editor.skinPath + 'icons.png'
		});

		// Link the dialog resource
		CKEDITOR.dialog.add( 'mdn-redirect', this.path + 'dialogs/mdn-redirect.js' );
	}
});