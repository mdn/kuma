/*
  Customized plugin added by David Walsh (:davidwalsh, dwalsh@mozilla.com)

  This plugin inserts boilerplate live sample content
*/
CKEDITOR.plugins.add('mdn-sampler', {
  icons: 'mdn-sampler-moono', // %REMOVE_LINE_%CORE

  init: function(editor) {
    editor.addCommand('mdn-sampler', {
      exec: function(editor) {
        var text = prompt(gettext('What should the sample title be?'));
        if(!text) return;

        var doc = editor.document,
        	temp = doc.createElement('div');
          sampleSlug = $.slugifyString(text);

        // Create main heading.
        makeElement('h2', text, { name: sampleSlug });

        // Create Pre[html].
        makeElement('h3', gettext('HTML Content'));
        makeElement('pre', gettext('Sample HTML Content'), { 'class': 'brush: html' });

        // Create Pre[css].
        makeElement('h3', gettext('CSS Content'));
        makeElement('pre', gettext('Sample CSS Content'), { 'class': 'brush: css' });

        // Create Pre[js].
        makeElement('h3', gettext('JavaScript Content'));
        makeElement('pre', gettext('Sample JavaScript Content'), { 'class': 'brush: js' });

        // Create the IFrame?
        makeElement('p', '{{ EmbedLiveSample(\'' + sampleSlug + '\') }}');

        editor.insertHtml(temp.getHtml());

		    function makeElement(name, text, attrs) {
		      var element = doc.createElement(name);

		      if(text)
		      	element.setText(gettext(text));
		      if(attrs)
		      	element.setAttributes(attrs);

		      temp.append(element);
		    }
      }
    });

    var label = gettext('Insert Code Sample Template');
    editor.ui.addButton('mdn-sampler', {
      icon: 'mdn-sampler-moono',
      label: label,
      toolbar: 'blocks,210',
      command: 'mdn-sampler'
    });
  }
});