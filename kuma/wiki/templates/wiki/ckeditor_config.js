(function () {
  'use strict';

  CKEDITOR.on('instanceReady', function(ev) {
    var writer = ev.editor.dataProcessor.writer;

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

    // Need to be ported to v4.
    // Retrieve nodes important to moving the path bar to the top
    // var tbody = ev.editor._.cke_contents.$.parentNode.parentNode;
    // var pathP = tbody.lastChild.childNodes[0].childNodes[1];
    // var toolbox = tbody.childNodes[0].childNodes[0].childNodes[0];

    // if(toolbox && pathP) {
    //   toolbox.appendChild(pathP);
    // }

    // Callback for inline, if necessary.
    var callback = CKEDITOR.inlineCallback;
    callback && callback(ev);
  });

  // Provide redirect pattern for corresponding plugin.
  mdn.ckeditor.redirectPattern = '{{ redirect_pattern|safe }}';

  // Tell CKEditor that <i> elements are block so empty <i>'s aren't removed.
  // This is essentially for Font-Awesome.
  CKEDITOR.dtd.$block['i'] = 1;
  delete CKEDITOR.dtd.$removeEmpty['i'];

  CKEDITOR.timestamp = '{{ BUILD_ID_JS }}';

  CKEDITOR.editorConfig = function(config) {
    // Should be kept in sync with the list in ckeditor/source/build-config.js.
    // Defining plugins list explicitly lets us to switch easily between dev and build versions.
    config.plugins =
      'a11yhelp,about,basicstyles,bidi,blockquote,clipboard,contextmenu,dialogadvtab,elementspath,enterkey,' +
      'entities,find,htmlwriter,image,indentlist,language,link,list,liststyle,magicline,maximize,pastefromword,' +
      'pastetext,preview,removeformat,resize,scayt,showblocks,showborders,sourcearea,stylescombo,tab,table,tabletools,' +
      'toolbar,undo,wsc,wysiwygarea,' +
      // MDN's plugins.
      'mdn-attachment,mdn-format,mdn-link-launch,mdn-redirect,mdn-sample-finder,mdn-sampler,mdn-syntaxhighlighter,' +
      'mdn-system-integration,mdn-table-customization,mdn-toggle-block,' +
      // Other plugins.
      'descriptionlist,tablesort,texzilla';

    // Need to be ported to v4.
    // config.extraPlugins = 'mdn-link,mdn-image,mdn-wrapstyle,youtube';

    // Add the spellchecker to the top bar
    // if(window.waffle && waffle.FLAGS.wiki_spellcheck) {
    //    config.extraPlugins += ',mdn-spell';
    //    config.toolbar_MDN[0].splice(10, 0, 'mdn-spell');
    //    config.toolbar_MDN[0].join();
    // }

    // Disable the Advanced Content Filter because too many pages
    // use unlimited HTML.
    config.allowedContent = true;

    // Don't use HTML entities in the output except basic ones (config.basicEntities).
    config.entities = false;

    config.startupFocus = true;
    config.bodyClass = 'text-content redesign';
    config.contentsCss = [
      mdn.mediaPath + 'redesign/css/main.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'redesign/css/wiki.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'redesign/css/wiki-wysiwyg.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'redesign/css/wiki-syntax.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'css/libs/font-awesome/css/font-awesome.min.css?{{ BUILD_ID_JS }}',
      '/en-US/docs/Template:CustomCSS?raw=1'
    ];

    config.dialog_backgroundCoverColor = 'black';
    config.dialog_backgroundCoverOpacity = 0.3;
    config.dialog_noConfirmCancel = true;

    if(!CKEDITOR.stylesSet.registered['default']) {
      CKEDITOR.stylesSet.add('default', [
        { name: 'None', element: 'p' },
        { name: 'Note box', element: 'div', attributes: { 'class': 'note' }, wrap: true },
        { name: 'Warning box', element: 'div', attributes: { 'class': 'warning' }, wrap: true },
        { name: 'Callout box', element: 'div', attributes: { 'class': 'geckoVersionNote' }, wrap: true },
        { name: 'Two columns', element: 'div', attributes: { 'class': 'twocolumns' }, wrap: true },
        { name: 'Three columns', element: 'div', attributes: { 'class': 'threecolumns' }, wrap: true },
        { name: 'SEO Summary', element: 'span', attributes: { 'class': 'seoSummary' }, wrap: false },
        { name: 'Article Summary', element: 'div', attributes: { 'class': 'summary' }, wrap: true },
        { name: 'Syntax Box', element: 'div', attributes: { 'class': 'syntaxbox' }, wrap: false },
        { name: 'Right Sidebar', element: 'div', attributes: { 'class': 'standardSidebar' }, wrap: false }
      ]);
    }

    config.keystrokes = [
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
      // CTRL+SHIFT+L
      [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 76, 'mdn-toggle-block' ],
      // CTRL+S
      [ CKEDITOR.CTRL + 83, 'mdn-save' ],
      // CTRL+SHIFT+S
      [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 83, 'mdn-save-exit' ],
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
      CKEDITOR.CTRL + 80,
      // Back
      1114149,
      // Forward
      1114151
    ] );

    {{ editor_config|safe }}
  };
})();