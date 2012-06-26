CKEDITOR.on('instanceReady', function (ev) {

    var writer = ev.editor.dataProcessor.writer;

    // Tighten up the indentation a bit from the default of wide tabs.
    writer.indentationChars = '  ';
    
    // Configure this set of tags to open and close all on the same line, if
    // possible.
    var oneliner_tags = [
        'hgroup', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'p', 'th', 'td', 'li'
    ]
    for (var i=0,tag; tag=oneliner_tags[i]; i++) {
        writer.setRules(tag, {
            indent: true,
            breakBeforeOpen: true,
            breakAfterOpen: false,
            breakBeforeClose: false,
            breakAfterClose: true
        });
    }
    
    //  Retrieve nodes important to moving the path bar to the top
    var tbody = ev.editor._.cke_contents.$.parentNode.parentNode,
        pathP = tbody.lastChild.childNodes[0].childNodes[1],
        toolbox = tbody.childNodes[0].childNodes[0].childNodes[0];
    toolbox.appendChild(pathP);
});

(function() {

    var keys = CKEDITOR.mdnKeys = {
            control1: CKEDITOR.CTRL + 49,
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
            controlShiftO: CKEDITOR.CTRL + CKEDITOR.SHIFT + 79,
            controlShiftS: CKEDITOR.CTRL + CKEDITOR.SHIFT + 83,
            shiftSpace: CKEDITOR.SHIFT + 32,
            tab: 9,
            shiftTab: CKEDITOR.SHIFT + 9
        },
        block = function(k) {
            return CKEDITOR.config.blockedKeystrokes.push(keys[k]);
        };

    // Prevent key handling
    block('tab');
    block('shiftTab');
    block('control1');
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

CKEDITOR.editorConfig = function(config) {

    config.extraPlugins = 'autogrow,definitionlist,mdn-buttons,mdn-link,mdn-syntaxhighlighter,mdn-keystrokes';
    config.removePlugins = 'link,tab';
    
    config.toolbar_MDN = [
        ['Source', 'mdnSaveExit', 'mdnSave', '-', 'PasteText', 'PasteFromWord', '-', 'SpellChecker', 'Scayt', '-', 'Find', 'Replace', '-', 'ShowBlocks'],
        ['BulletedList', 'NumberedList', 'DefinitionList', 'DefinitionTerm', '-', 'Outdent', 'Indent', 'Blockquote', '-', 'Image', 'Table', '-', 'TextColor', 'BGColor', '-', 'BidiLtr', 'BidiRtl'],
        ['Maximize'],
        '/',
        ['h1Button', 'h2Button', 'h3Button', 'h4Button', 'h5Button', 'h6Button', '-', 'preButton', 'mdn-syntaxhighlighter', 'Styles'],
        ['Link', 'Unlink', 'Anchor', '-', 'Bold', 'Italic', 'Underline', 'codeButton', 'Strike', 'Superscript', 'RemoveFormat', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyLeft']
    ];
    
    config.skin = 'kuma';
    config.startupFocus = true;
    config.toolbar = 'MDN';

    config.autoGrow_minHeight = 600;
    config.contentsCss = '/media/css/wiki-edcontent.css'; 
    config.toolbarCanCollapse = false;
    config.resize_enabled = false;
    config.dialog_backgroundCoverColor = 'black';
    config.dialog_backgroundCoverOpacity = 0.3;
    config.docType = '<!DOCTYPE html>';
    
    CKEDITOR.stylesSet.add('default',[
        { name: "None", element: 'p' },
        { name: "Note box", element: 'div', attributes: { 'class': 'note' }},
        { name: "Warning box", element: 'div', attributes: { 'class': 'warning' }},
        { name: "Callout box", element: 'div', attributes: { 'class': 'geckoVersionNote' }},
        { name: "Plaintext (nowiki)", element: 'span', attributes: { 'class': 'plain' }},
        { name: "Two columns", element: 'div', attributes: { 'class': 'twocolumns' }},
        { name: "Three columns", element: 'div', attributes: { 'class': 'threecolumns' }}
    ]);

    {{ editor_config|safe }}    
};
