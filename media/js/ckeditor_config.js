CKEDITOR.editorConfig = function(config) {
    CKEDITOR.config.toolbar_MDN = [
        ['Source','-','Save','NewPage','Preview','-','Templates'],
        ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Print', 'SpellChecker', 'Scayt'],
        ['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],
        '/',
        ['codeButton', 'preButton', 'dlButton', 'dtButton', 'ddButton', '-', 'Bold','Italic','Underline','Strike','-','Subscript','Superscript'],
        ['NumberedList','BulletedList','-','Outdent','Indent','Blockquote','CreateDiv'],
        ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
        ['BidiLtr', 'BidiRtl' ],
        ['Link','Unlink','Anchor'],
        ['Image','Table','HorizontalRule','SpecialChar','Iframe'],
        '/',
        ['Styles','Format',],
        ['TextColor','BGColor'],
        ['Maximize', 'ShowBlocks','-','About']
  ];
    config.skin = 'kuma';
    config.startupFocus = true;
    config.toolbar = 'MDN';
    config.extraPlugins = 'autogrow,mdn-buttons';
}
