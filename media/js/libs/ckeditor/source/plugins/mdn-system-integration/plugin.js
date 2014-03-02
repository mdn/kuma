'use strict';

CKEDITOR.plugins.add('mdn-system-integration', {
  init: function(editor) {
    var $saveButton = $('#btn-save'),
      $saveContinueButton = $('#btn-save-and-edit');

      // Configure "Save and Exit".
      editor.addCommand('mdn-save-exit', {
        modes: { wysiwyg: 1, source: 1 },
        exec: function(editor) {
          if(!$saveButton.length) {
            $saveButton = $('.edited-section-ui.current .btn-save');
          }

          editor.updateElement();
          $saveButton.click();
        }
      });

      // Add "Save and Continue", if that button is present.
      if($saveContinueButton.length) {
        editor.addCommand('mdn-save', {
          modes: { wysiwyg: 1, source: 1 },
          exec: function(editor) {
            editor.updateElement();

            var saveCallback = $saveContinueButton.data('save_cb');
            if(saveCallback) {
              saveCallback();
            } else {
              $saveContinueButton.click();
            }
          }
        });
      }

      // Some localized strings are stashed on #page-buttons...
      var pb = $('#page-buttons');

      // Define command and button for "New Page".
      editor.addCommand('mdn-newpage', {
        exec: function(editor) {
          // Treat this as cancellation for inline editor.
          var cancelBtn = $('.edited-section-ui.current .cancel');
          if(cancelBtn.length) {
            return cancelBtn.click();
          }

          // Otherwise, try treating as a new wiki page.
          var msg = pb.attr('data-new-page-msg'),
            href = pb.attr('data-new-page-href');

          if(!msg || !href) { return; }
          if(window.confirm(msg)) {
            window.location.href = href;
          }
        }
      });

      // Define command and button for "Preview".
      editor.addCommand('mdn-preview', {
        exec: function (editor, data) {
          editor.updateElement();
          $('#btn-preview').click();
        }
      });

      editor.ui.addButton('MdnSaveExit', {
        label: gettext('Save and Exit'),
        className: 'cke_button_save_exit',
        command: 'mdn-save-exit',
        toolbar: 'document,100'
      });

      if($saveContinueButton.length) {
        editor.ui.addButton('MdnSave', {
          label: $saveContinueButton.text(),
          className: 'cke_button_save',
          command: 'mdn-save',
          toolbar: 'document,110'
        });
      }

      editor.ui.addButton('MdnNewPage', {
        label: pb.attr('data-new-page-label'),
        className: 'cke_button_newpage',
        command: 'mdn-newpage',
        toolbar: 'document,120'
      });

      editor.ui.addButton('MdnPreview', {
        label: $('#btn-preview').text(),
        className: 'cke_button_preview',
        command: 'mdn-preview',
        toolbar: 'document,130'
      });
  }
});