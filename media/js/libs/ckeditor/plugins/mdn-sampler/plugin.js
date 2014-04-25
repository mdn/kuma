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

				// Inject main heading
				makeElement('h2', text, { name: sampleSlug });

				// Inject Pre[html]
				makeElement('h3', gettext('HTML'));
				makeElement('pre', gettext('Sample HTML'), { 'class': 'brush: html' });

				// Inject Pre[css]
				makeElement('h3', gettext('CSS'));
				makeElement('pre', gettext('Sample CSS'), { 'class': 'brush: css' });

				// Inject Pre[js]
				makeElement('h3', gettext('JavaScript'));
				makeElement('pre', gettext('Sample JavaScript'), { 'class': 'brush: js' });

				// Inject the IFrame?
				makeElement('p', '{{ EmbedLiveSample(\'' + sampleSlug + '\') }}');


				function makeElement(type, text, attrs) {
					var element = new CKEDITOR.dom.element(type, doc);
					if(text) element.setText(gettext(text));
					if(attrs) element.setAttributes(attrs);
					editor.insertElement(element);
				}
			}
		});

		var label = gettext('Insert Code Sample Template');
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
