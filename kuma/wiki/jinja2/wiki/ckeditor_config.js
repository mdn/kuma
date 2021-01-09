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
      'a11ychecker,a11yhelp,autogrow,balloonpanel,basicstyles,bidi,blockquote,clipboard,contextmenu,dialogadvtab,elementspath,enterkey,' +
      'entities,find,htmlwriter,image,indentlist,language,link,list,liststyle,magicline,maximize,pastefromword,' +
      'pastetext,removeformat,scayt,showblocks,showborders,sourcearea,stylescombo,tab,table,tabletools,' +
      'toolbar,undo,wsc,wysiwygarea,' +
      // MDN's plugins.
      'mdn-attachment,mdn-format,mdn-sticky-toolbar,mdn-image-attachment,mdn-link-customization,mdn-link-launch,' +
      'mdn-redirect,mdn-sample-finder,mdn-sampler,mdn-syntaxhighlighter,mdn-system-integration,mdn-table-customization,' +
      'mdn-toggle-block,mdn-wrapstyle,mdn-youtube,' +
      // Other plugins.
      'descriptionlist,tablesort,texzilla,wordcount';

    config.fillEmptyBlocks = false;
    config.removeButtons = 'Cut,Copy,PasteFromWord,Language';
    config.toolbarGroups = [
      { name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
      { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
      { name: 'editing', groups: [ 'find', 'selection', 'spellchecker' ] },
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

    // Enable the spell checker by default
    // Disabled to avoid auto-loading JS and advertisements
    // config.scayt_autoStartup = true;

    // Ignore words in all caps, or in CamelCase
    config.scayt_ignoreAllCapsWords = true;
    config.scayt_ignoreWordsWithMixedCases = true;

    // Multiple language support
    config.scayt_multiLanguageMode = true;
    config.scayt_disableOptionsStorage = 'all';
    var lang = 'en-US';
    var pathname = document.location.pathname;
    if (pathname && pathname.split('/').length >= 2) {
        lang = pathname.split('/')[1];
    }

    // SCAYT expects underscores rather than dashes
    lang = lang.replace(/-/g, "_");

    // Also, some of the names we use are different, so fix those too
    var langTable = {
      'nl': 'nl_NL',
      'fi': 'fi_FI',
      'fr': 'fr_FR',
      'de': 'de_DE',
      'el': 'el_GR',
      'it': 'it_IT',
      'es': 'es_ES'
    };

    if (lang in langTable) {
      lang = langTable[lang];
    }

    config.scayt_sLang = lang;

    // Adjust the spell checker's items in the context menu
    config.scayt_contextCommands = "ignore|ignoreall|add|option|language";

    config.startupFocus = true;
    config.bodyClass = 'text-content';
    config.contentsCss = mdn.assets.css['editor-content'];

    config.dialog_backgroundCoverColor = 'black';
    config.dialog_backgroundCoverOpacity = 0.3;
    config.dialog_noConfirmCancel = true;

    if(!CKEDITOR.stylesSet.registered['default']) {
      CKEDITOR.stylesSet.add('default', [
        { name: 'None', element: 'p' },
        { name: 'Note Box', element: 'div', attributes: { 'class': 'blockIndicator note', 'role': 'complementary' }, type: 'wrap' },
        { name: 'Warning Box', element: 'div', attributes: { 'class': 'blockIndicator warning', 'role': 'region', 'aria-label': gettext('Important note') }, type: 'wrap' },
        { name: 'Two Columns', element: 'div', attributes: { 'class': 'twocolumns' }, type: 'wrap' },
        { name: 'Three Columns', element: 'div', attributes: { 'class': 'threecolumns' }, type: 'wrap' },
        { name: 'Syntax Box', element: 'pre', attributes: { 'class': 'syntaxbox' } },
        { name: 'Summary', element: 'span', attributes: { 'class': 'seoSummary' } },
        { name: 'Hidden When Reading', element: 'div', attributes: { 'class': 'hidden' }, type: 'wrap' }
      ]);
    }

    config.keystrokes = [
      // CTRL+0
      [ CKEDITOR.CTRL + 48, 'removeFormat' ],
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

    // Configure the word count plugin. It will ignore the following:
    //
    // * <div> and <p> blocks with the class "hidden" applied
    // * <div> blocks with the class "prevnext" (that is, Previous and
    //   Next buttons at the top and/or bottom of pages)
    //
    // NOTE: The docs for the wordcount plugin say that the notification
    //       plugin is required; that is only true if you set maximum
    //       character, word, or paragraph counts, which we do not.

    config.wordcount = {
        showParagraphs: true,
        showWordCount: true,
/*--- For more on filters:
 *        https://github.com/w8tcha/CKEditor-WordCount-Plugin
 *        http://docs.ckeditor.com/#!/api/CKEDITOR.htmlParser.filter
 *        https://github.com/w8tcha/CKEditor-WordCount-Plugin/blob/master/wordcount/plugin.js#L58
*/
        filter: new CKEDITOR.htmlParser.filter({
            elements: {
                div: function(element) {
                    if (element.hasClass("hidden") ||
                        element.hasClass("prevnext")) {
                        element.setHtml("");
                    }
                },
                p: function(element) {
                    if (element.hasClass("hidden")) {
                        element.setHtml("");
                    }
                }
            }
        })
    };

    {{ editor_config|safe }}
  };
})();
