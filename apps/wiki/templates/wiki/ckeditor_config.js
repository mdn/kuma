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

});

CKEDITOR.editorConfig = function(config) {

    config.extraPlugins = 'autogrow,definitionlist,mdn-buttons';

    config.toolbar_MDN = [
        ['Source','-','mdnSave','mdnNewPage','mdnPreview'],
        ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Print', 'SpellChecker', 'Scayt'],
        ['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],
        ['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],
        ['NumberedList','BulletedList','DefinitionList','DefinitionTerm','DefinitionDescription','-','Outdent','Indent','Blockquote','CreateDiv'],
        ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
        ['BidiLtr', 'BidiRtl' ],
        ['Link','Unlink','Anchor'],
        ['Image','Table','HorizontalRule','SpecialChar','Iframe'],
        ['h1Button', 'h2Button', 'h3Button', 'preButton', 'codeButton', '-', 'Styles'],
        ['TextColor','BGColor'],
        ['Maximize', 'ShowBlocks','-','About']
    ];
    config.skin = 'kuma';
    config.startupFocus = true;
    config.toolbar = 'MDN';

    {{ editor_config|safe }}
};
