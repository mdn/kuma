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

  (function() {
    // Tell CKEditor that <i> elements are block so empty <i>'s aren't removed.
    // This is essentially for Font-Awesome.
    CKEDITOR.dtd.$block['i'] = 1;
    delete CKEDITOR.dtd.$removeEmpty['i'];

    // Manage key presses.
    var keys = mdn.ckeditor.keys = {
      control2: CKEDITOR.CTRL + 50,
      control3: CKEDITOR.CTRL + 51,
      control4: CKEDITOR.CTRL + 52,
      control5: CKEDITOR.CTRL + 53,
      control6: CKEDITOR.CTRL + 54,
      controlK: CKEDITOR.CTRL + 75,
      controlL: CKEDITOR.CTRL + 76,
      controlShiftL: CKEDITOR.CTRL + CKEDITOR.SHIFT + 76,
      controlS: CKEDITOR.CTRL + 83,
      controlO: CKEDITOR.CTRL + 79,
      controlP: CKEDITOR.CTRL + 80,
      controlShiftO: CKEDITOR.CTRL + CKEDITOR.SHIFT + 79,
      controlShiftS: CKEDITOR.CTRL + CKEDITOR.SHIFT + 83,
      shiftSpace: CKEDITOR.SHIFT + 32,
      tab: 9,
      shiftTab: CKEDITOR.SHIFT + 9,
      enter: 13,
      back: 1114149,
      forward: 1114151
    };
    var block = function(k) {
      return CKEDITOR.config.blockedKeystrokes.push(keys[k]);
    };

    // Prevent key handling
    block('tab');
    block('shiftTab');
    block('control2');
    block('control3');
    block('control4');
    block('control5');
    block('control6');
    block('controlO');
    block('controlS');
    block('controlShiftL');
    block('controlShiftO');
  })();

  CKEDITOR.timestamp = '{{ BUILD_ID_JS }}';

  CKEDITOR.editorConfig = function(config) {
    // Should be kept in sync with the list in ckeditor/source/build-config.js.
    // Defining plugins list explicitly lets us to switch easily between dev and build versions.
    config.plugins =
      'a11yhelp,about,basicstyles,bidi,blockquote,clipboard,contextmenu,dialogadvtab,elementspath,enterkey,' +
      'entities,find,htmlwriter,image,indentlist,language,link,list,liststyle,magicline,maximize,pastefromword,' +
      'pastetext,preview,removeformat,resize,scayt,showblocks,showborders,sourcearea,stylescombo,table,tabletools,' +
      'toolbar,undo,wsc,wysiwygarea,' +
      // MDN's plugins.
      'mdn-format,mdn-syntaxhighlighter,mdn-system-integration';

    // Need to be ported to v4.
    // config.extraPlugins = 'definitionlist,mdn-buttons,mdn-link,mdn-syntaxhighlighter,mdn-keystrokes,mdn-attachments,mdn-image,mdn-enterkey,mdn-wrapstyle,mdn-table,tablesort,mdn-sampler,mdn-sample-finder,mdn-maximize,mdn-redirect,youtube,autogrow,texzilla';

    // Don't use HTML entities in the output except basic ones (config.basicEntities).
    config.entities = false;

    config.startupFocus = true;
    config.tabSpaces = 2;
    config.bodyClass = 'text-content redesign';
    config.contentsCss = [
      mdn.mediaPath + 'css/wiki-screen.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'redesign/css/main.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'redesign/css/wiki-wysiwyg.css?{{ BUILD_ID_JS }}',
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

    {{ editor_config|safe }}
  };
})();