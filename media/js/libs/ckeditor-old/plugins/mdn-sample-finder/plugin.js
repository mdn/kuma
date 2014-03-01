/*
	Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)
	
	This plugin provides a popup for choosing a demo from a given page
*/
CKEDITOR.plugins.add('mdn-sample-finder', {

	requires: ['selection'],
	
	init: function(editor) {

		// Add the dialog command
		editor.addCommand( 'mdn-sample-finder', new CKEDITOR.dialogCommand('mdn-sample-finder') );

		// Register the command
		var label = gettext('Insert Code Sample iFrame');
		editor.ui.addButton('mdn-sample-finder', {
			label: label,
			title: label,
			className: 'cke_button_mdn_sample_finder',
			command: 'mdn-sample-finder',
			iconOffset: 42,
			icon: editor.skinPath + 'icons.png'
		});

		// Link the dialog resource
		CKEDITOR.dialog.add( 'mdn-sample-finder', this.path + 'dialogs/mdn-sample-finder.js' );
	}
});