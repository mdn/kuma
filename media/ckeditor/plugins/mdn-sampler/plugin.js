/*
	Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)
	
	This plugin inserts boilerplate live sample content
*/
CKEDITOR.plugins.add('mdn-sampler', {

	requires: ['selection'],
	
	init: function(editor) {

		editor.addCommand('mdnSampler', {
			exec: function (editor, data) {

				// Inject heading
				var heading = new CKEDITOR.dom.element('h2', editor.document);
				heading.setText(gettext('Sample Title'));
				editor.insertElement(heading);

				// Inject Pre[html]
				var htmlPre = new CKEDITOR.dom.element('pre', editor.document);
				htmlPre.setText(gettext('Sample HTML Content'));
				htmlPre.setAttribute('class', 'brush:html;');
				editor.insertElement(htmlPre);

				// Inject Pre[css]
				var cssPre = new CKEDITOR.dom.element('pre', editor.document);
				cssPre.setText(gettext('Sample CSS Content'));
				cssPre.setAttribute('class', 'brush:css;');
				editor.insertElement(cssPre);

				// Inject Pre[js]
				var jsPre = new CKEDITOR.dom.element('pre', editor.document);
				jsPre.setText(gettext('Sample JS Content'));
				jsPre.setAttribute('class', 'brush:js;');
				editor.insertElement(jsPre);
			}
		});

		var label = 'Insert Code Sample Template';
		editor.ui.addButton('mdn-sampler', {
			label: label,
			title: label,
			className: 'cke_button_mdn_sampler',
			command: 'mdnSampler',
			iconOffset: 43,
			icon: editor.skinPath + 'icons.png'
		});
	}
});