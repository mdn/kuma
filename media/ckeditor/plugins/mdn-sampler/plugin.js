/*
	Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)
	
	This plugin inserts boilerplate live sample content
*/
CKEDITOR.plugins.add('mdn-sampler', {

	requires: ['selection'],
	
	init: function(editor) {

		editor.addCommand('mdnSampler', {
			exec: function (editor, data) {

				var text = prompt(gettext('What should the sample title be?'));
				if(!text) return;

				var doc = editor.document,
					sampleSlug = $.slugifyString(text);

				// Inject heading
				var heading = new CKEDITOR.dom.element('h2', doc);
				heading.setText(text);
				heading.setAttribute('name', sampleSlug);
				editor.insertElement(heading);

				// Inject Pre[html]
				var htmlPre = new CKEDITOR.dom.element('pre', doc);
				htmlPre.setText(gettext('Sample HTML Content'));
				htmlPre.setAttribute('class', 'brush: html');
				editor.insertElement(htmlPre);

				// Inject Pre[css]
				var cssPre = new CKEDITOR.dom.element('pre', doc);
				cssPre.setText(gettext('Sample CSS Content'));
				cssPre.setAttribute('class', 'brush: css');
				editor.insertElement(cssPre);

				// Inject Pre[js]
				var jsPre = new CKEDITOR.dom.element('pre', doc);
				jsPre.setText(gettext('Sample JS Content'));
				jsPre.setAttribute('class', 'brush: js');
				editor.insertElement(jsPre);

				// Inject the IFrame?
				var templateP = new CKEDITOR.dom.element('p', doc);
				templateP.setText('{{ EmbedLiveSample(\'' + sampleSlug + '\') }}');
				editor.insertElement(templateP);
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