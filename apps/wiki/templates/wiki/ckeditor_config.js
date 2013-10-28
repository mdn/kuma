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
  
  // Retrieve nodes important to moving the path bar to the top
  var tbody = ev.editor._.cke_contents.$.parentNode.parentNode,
    pathP = tbody.lastChild.childNodes[0].childNodes[1],
    toolbox = tbody.childNodes[0].childNodes[0].childNodes[0];

  if(toolbox && pathP) {
    toolbox.appendChild(pathP);
  }

  // Callback for inline, if necessary
  var callback = CKEDITOR.inlineCallback;
  callback && callback(ev);
});

// Provide redirect pattern for corresponding plugin
mdn.ckeditor.redirectPattern = '{{ redirect_pattern|safe }}';

(function() {
  // Brick dialog "changed" prompts
  var originalOn = CKEDITOR.dialog.prototype.on;
  CKEDITOR.dialog.prototype.on = function(event, callback) {
    // If it's the cancel event that pops up the confirmation, just get out
    if(event == 'cancel' && callback.toString().indexOf('confirmCancel') != -1) {
      return true;
    }
    originalOn.apply(this, arguments);
  };

  // <time> elements should be inline
  CKEDITOR.dtd.$inline['time'] = 1;
  delete CKEDITOR.dtd.$block['time'];

  // Tell CKEditor that <i> elements are block so empty <i>'s aren't removed
  // This is essentially for Font-Awesome
  CKEDITOR.dtd.$block['i'] = 1;
  delete CKEDITOR.dtd.$removeEmpty['i'];

  // Manage key presses
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
    },
    block = function(k) {
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

   config.extraPlugins = 'definitionlist,mdn-buttons,mdn-link,mdn-syntaxhighlighter,mdn-keystrokes,mdn-attachments,mdn-image,mdn-enterkey,mdn-wrapstyle,mdn-table,tablesort,mdn-sampler,mdn-sample-finder,mdn-maximize,mdn-redirect,youtube,autogrow';
    config.removePlugins = 'link,image,tab,enterkey,table,maximize';
    config.entities = false;
  
    var inlineHeight = CKEDITOR.inlineHeight;
    config.autoGrow_minHeight = (!inlineHeight || inlineHeight < 150 ? 500 : inlineHeight);
    
    config.toolbar_MDN = [
        ['Source', 'mdnSave', 'mdnSaveExit', '-', 'PasteText', 'PasteFromWord', '-', 'SpellChecker', 'Scayt', '-', 'Find', 'Replace', '-', 'ShowBlocks'],
        ['BulletedList', 'NumberedList', 'DefinitionList', 'DefinitionTerm', 'DefinitionDescription', '-', 'Outdent', 'Indent', 'Blockquote', '-', 'Image', 'MDNTable', '-', 'TextColor', 'BGColor', '-', 'BidiLtr', 'BidiRtl'],
        ['Maximize'],
        '/',
        ['h1Button', 'h2Button', 'h3Button', 'h4Button', 'h5Button', 'h6Button', 'Styles'],
        ['preButton', 'mdn-syntaxhighlighter', 'mdn-sampler', 'mdn-sample-finder', 'mdn-redirect', 'youtube'],
        ['Link', 'Unlink', 'Anchor', '-', 'Bold', 'Italic', 'Underline', 'codeButton', 'Strike', 'Superscript', 'RemoveFormat', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight']
    ];
    
    config.skin = 'kuma';
    config.startupFocus = true;
    config.toolbar = 'MDN';
    config.tabSpaces = 2;
    config.contentsCss = [mdn.mediaPath + 'css/wiki-screen.css?{{ BUILD_ID_JS }}'];
    if(mdn.waffles.redesign) config.contentsCss.push(mdn.mediaPath + 'redesign/css/main.css?{{ BUILD_ID_JS }}');
    config.contentsCss.push(
      mdn.mediaPath + 'css/wiki-edcontent.css?{{ BUILD_ID_JS }}',
      mdn.mediaPath + 'css/libs/font-awesome/css/font-awesome.min.css?{{ BUILD_ID_JS }}',
      '/en-US/docs/Template:CustomCSS?raw=1'
    );
    
    config.toolbarCanCollapse = false;
    config.resize_enabled = false;
    config.dialog_backgroundCoverColor = 'black';
    config.dialog_backgroundCoverOpacity = 0.3;
    config.docType = '<!DOCTYPE html>';
    config.bodyClass = 'page-content';
    if(mdn.waffles.redesign) config.bodyClass = 'text-content redesign-content redesign';
  
    
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