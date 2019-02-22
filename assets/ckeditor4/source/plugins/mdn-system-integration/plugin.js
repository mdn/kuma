'use strict';

CKEDITOR.plugins.add('mdn-system-integration', {
  icons: 'mdn-preview,mdn-save-edit-moono,mdn-save', // %REMOVE_LINE_%CORE
  init: function(editor) {
    var buttonsContainer = CKEDITOR.document.findOne('.page-buttons'),
      buttonSaveAndEdit = buttonsContainer.findOne('.btn-save-and-edit'),
      buttonSave = buttonsContainer.findOne('.btn-save'),
      buttonPreview = buttonsContainer.findOne('.btn-preview');

    if (!buttonSave || !buttonPreview)
      throw new Error('[CKEDITOR plugin:mdn-system-integration] Page buttons have not been found');

    // Add "Save and Continue", if that button is present.
    if(buttonSaveAndEdit) {
      editor.addCommand('mdn-save-edit', {
        modes: { wysiwyg: 1, source: 1 },
        exec: function(editor) {
          editor.updateElement();
          buttonSaveAndEdit.$.click();
        }
      });
    }

    // Configure "Save and Exit".
    editor.addCommand('mdn-save', {
      modes: { wysiwyg: 1, source: 1 },
      exec: function(editor) {
        editor.updateElement();
        buttonSave.$.click();
      }
    });

    // Define command and button for "Preview".
    editor.addCommand('mdn-preview', {
      modes: { wysiwyg: 1, source: 1 },
      exec: function (editor, data) {
        editor.updateElement();
        buttonPreview.$.click();
      }
    });

    if (buttonSaveAndEdit) {
      editor.ui.addButton('MdnSaveEdit', {
        icon: 'mdn-save-edit-moono',
        label: buttonSaveAndEdit.getText(),
        command: 'mdn-save-edit',
        toolbar: 'document,100'
      });
    }

    editor.ui.addButton('MdnSave', {
      icon: 'mdn-save',
      label: buttonSave.getText(),
      command: 'mdn-save',
      toolbar: 'document,110'
    });

    editor.ui.addButton('MdnPreview', {
      icon: 'mdn-preview',
      label: buttonPreview.getText(),
      command: 'mdn-preview',
      toolbar: 'document,130'
    });
  }
});