'use strict';

(function() {

  CKEDITOR.plugins.add('mdn-image-attachment', {
    requires: 'image,mdn-attachment',

    onLoad: function() {
      CKEDITOR.on('dialogDefinition', function(evt) {
        var dialogName = evt.data.name,
          dialogDefinition = evt.data.definition;

        if (dialogName != 'image')
          return;

        var infoTab = dialogDefinition.getContents('info');

        infoTab.add({
          type: 'vbox',
          children: [{
            type: 'select',
            id: 'attachment',
            label: gettext('Attachments'),
            items: [],
            onChange: function() {
              var value = this.getValue();
              var dialog = this.getDialog();
              var attachmentAlt = mdn.ckeditor.getObjectByUrl(value);

              dialog.setValueOf('info', 'txtUrl', value);
              if (!dialog.getValueOf('info', 'txtAlt') && attachmentAlt) {
                dialog.setValueOf('info', 'txtAlt', attachmentAlt.description);
              }
            }
          }]
        });

        // Small trick - we couldn't add the attachment's vbox at the beginning,
        // because the first UI element in the image dialog does not have an id, so
        // here we pop() it from the elements and insert at the beggining.
        infoTab.elements.unshift(infoTab.elements.pop());
      });
    },

    init: function(editor) {
      // We can't use attachment's setup callback, because it won't be executed
      // when creating image, but only when editing existing one.
      // We want to update attachment's list every time we open the dialog.
      editor.on('dialogShow', function(evt) {
        var dialog = evt.data;

        if (dialog.getName() != 'image')
          return;

        var select = dialog.getContentElement('info', 'attachment');

        mdn.ckeditor.updateAttachments(select, dialog.getValueOf('info', 'txtUrl'), imageAttachmentFilter);
      });
    }
  });

  function imageAttachmentFilter(attachment) {
    var validMimes = {
      'image/png': 1, 
      'image/jpeg': 1,
      'image/jpg': 1,
      'image/pjpeg': 1,
      'image/gif': 1,
      'image/bmp': 1,
      'image/x-windows-bmp': 1,
      'image/svg+xml': 1
    };
    return attachment.mime.toLowerCase() in validMimes;
  }

})();