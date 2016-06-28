(function () {
  'use strict';

  CKEDITOR.on('instanceReady', function(evt) {
    var writer = evt.editor.dataProcessor.writer;

    // Tighten up the indentation a bit from the default of wide tabs.
    writer.indentationChars = ' ';

    // Configure this set of tags to open and close all on the same line, if
    // possible.
    var oneliner_tags = [
      'hgroup', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'th', 'td', 'li'
    ];

    for(var i = 0, tag; tag = oneliner_tags[i]; i++) {
      writer.setRules(tag, {
        indent: true,
        breakBeforeOpen: true,
        breakAfterOpen: false,
        breakBeforeClose: false,
        breakAfterClose: true
      });
    }

    // By default autogrow is executed for the first time on
    // editor#focus. We want to resize editor after it loads.
    evt.editor.execCommand('autogrow');

    // Callback for inline, if necessary.
    var callback = CKEDITOR.inlineCallback;
    callback && callback(evt);
  });

  // Provide redirect pattern for corresponding plugin.
  mdn.ckeditor.redirectPattern = '{{ redirect_pattern|safe }}';

  // Tell CKEditor that <i> elements are block so empty <i>'s aren't removed.
  // This is essentially for Font-Awesome.
  CKEDITOR.dtd.$block['i'] = 1;
  delete CKEDITOR.dtd.$removeEmpty['i'];

  CKEDITOR.editorConfig = function(config) {
    // Should be kept in sync with the list in ckeditor/source/build-config.js.
    // Defining plugins list explicitly lets us to switch easily between dev and build versions.
    config.plugins =
      'a11yhelp,autogrow,basicstyles,bidi,blockquote,clipboard,contextmenu,dialogadvtab,elementspath,enterkey,' +
      'entities,find,htmlwriter,image,indentlist,language,link,list,liststyle,magicline,maximize,pastefromword,' +
      'pastetext,removeformat,scayt,showblocks,showborders,sourcearea,stylescombo,tab,table,tabletools,' +
      'toolbar,undo,wsc,wysiwygarea,' +
      // MDN's plugins.
      'mdn-attachment,mdn-format,mdn-sticky-toolbar,mdn-image-attachment,mdn-link-customization,mdn-link-launch,' +
      'mdn-redirect,mdn-sample-finder,mdn-sampler,mdn-syntaxhighlighter,mdn-system-integration,mdn-table-customization,' +
      'mdn-toggle-block,mdn-wrapstyle,mdn-youtube,' +
      // Other plugins.
      'descriptionlist,tablesort,texzilla';

    config.removeButtons = 'Cut,Copy,PasteFromWord,Language';
    config.toolbarGroups = [
      { name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
      { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
      { name: 'editing', groups: [ 'find', 'selection', 'spellchecker'] },
      { name: 'forms' },
      { name: 'tools' },
      { name: 'others' },
      { name: 'about' },
      { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
      { name: 'colors' },
      { name: 'links' },
      '/',
      { name: 'styles', groups: [ 'styles', 'blocks' ] },
      { name: 'paragraph', groups: [ 'list', 'indent', 'align', 'bidi' ] },
      { name: 'insert' }
    ];

    // Disable the Advanced Content Filter because too many pages
    // use unlimited HTML.
    config.allowedContent = {
        $1: {
            // Use the ability to specify elements as an object.
            elements: '{{ allowed_tags }}',
            attributes: true,
            styles: true,
            classes: true
        }
    };
    config.disallowedContent = 'iframe; *[on*]';

    // Don't use HTML entities in the output except basic ones (config.basicEntities).
    config.entities = false;

    // Allows section editing to be used immediately and not lose focus on desired element
    // http://docs.ckeditor.com/#!/guide/dev_autogrow
    if(window.waffle && window.waffle.flag_is_active('section_edit')) {
        config.autoGrow_onStartup = true;
    }

    config.startupFocus = true;
    config.bodyClass = 'text-content redesign';
    config.contentsCss = mdn.assets.css['editor-content'];

    config.dialog_backgroundCoverColor = 'black';
    config.dialog_backgroundCoverOpacity = 0.3;
    config.dialog_noConfirmCancel = true;

    if(!CKEDITOR.stylesSet.registered['default']) {
      CKEDITOR.stylesSet.add('default', [
        { name: 'None', element: 'p' },
        { name: 'Note box', element: 'div', attributes: { 'class': 'note' }, type: 'wrap' },
        { name: 'Warning box', element: 'div', attributes: { 'class': 'warning' }, type: 'wrap' },
        { name: 'Two columns', element: 'div', attributes: { 'class': 'twocolumns' }, type: 'wrap' },
        { name: 'Three columns', element: 'div', attributes: { 'class': 'threecolumns' }, type: 'wrap' },
        { name: 'Article Summary', element: 'p', attributes: { 'class': 'summary' } },
        { name: 'Syntax Box', element: 'div', attributes: { 'class': 'syntaxbox' } },
        { name: 'SEO Summary', element: 'span', attributes: { 'class': 'seoSummary' } }
      ]);
    }

    config.keystrokes = [
      // CTRL+0
      [ CKEDITOR.CTRL + 48, 'removeFormat' ],
      // CTRL+2
      [ CKEDITOR.CTRL + 50, 'mdn-format-h2' ],
      // CTRL+3
      [ CKEDITOR.CTRL + 51, 'mdn-format-h3' ],
      // CTRL+4
      [ CKEDITOR.CTRL + 52, 'mdn-format-h4' ],
      // CTRL+5
      [ CKEDITOR.CTRL + 53, 'mdn-format-h5' ],
      // CTRL+O
      [ CKEDITOR.CTRL + 79, 'mdn-format-code' ],
      // CTRL+P
      [ CKEDITOR.CTRL + 80, 'mdn-format-pre' ],
      // CTRL+K
      [ CKEDITOR.CTRL + 75, 'link' ],
      // CTRL+SHIFT+K
      [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 75, 'unlink' ],
      // CTRL+SHIFT+L
      [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 76, 'mdn-toggle-block' ],
      // CTRL+S
      [ CKEDITOR.CTRL + 83, 'mdn-save-edit' ],
      // CTRL+SHIFT+S
      [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 83, 'mdn-save' ],
      // CTRL+SHIFT+O
      [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 79, 'source' ]
    ];

    // Additinal keystrokes that should be blocked in both modes (wysiwyg and source).
    // Extends CKEDITOR.config.blockedKeystrokes.
    config.blockedKeystrokes = config.blockedKeystrokes.concat( [
      // TAB
      9,
      // SHIFT+TAB
      CKEDITOR.SHIFT + 9,
      // CTRL+S
      CKEDITOR.CTRL + 83,
      // CTRL+SHIFT+S
      CKEDITOR.CTRL + CKEDITOR.SHIFT + 83,
      // CTRL+O
      CKEDITOR.CTRL + 79,
      // CTRL+P
      CKEDITOR.CTRL + 80
    ] );

    {{ editor_config|safe }}
  };
})();
