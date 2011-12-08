CKEDITOR.editorConfig = function(config) {
    CKEDITOR.config.toolbar_MDN = [
        ['Source','-','Save','NewPage','Preview','-','Templates'],
        ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Print', 'SpellChecker', 'Scayt'],
        ['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],
        '/',
        ['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],
        ['NumberedList','BulletedList','DefinitionList','DefinitionTerm','DefinitionDescription','-','Outdent','Indent','Blockquote','CreateDiv'],
        ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
        ['BidiLtr', 'BidiRtl' ],
        ['Link','Unlink','Anchor'],
        ['Image','Table','HorizontalRule','SpecialChar','Iframe'],
        '/',
        ['h1Button', 'h2Button', 'h3Button', 'preButton', 'codeButton', '-', 'Styles'],
        ['TextColor','BGColor'],
        ['Maximize', 'ShowBlocks','-','About']
    ];
    config.skin = 'kuma';
    config.startupFocus = true;
    config.toolbar = 'MDN';
    config.extraPlugins = 'autogrow,definitionlist,mdn-buttons';
};
