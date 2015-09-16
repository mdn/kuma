'use strict';

CKEDITOR.plugins.add('mdn-table-customization', {
  requires: 'table',

  onLoad: function() {
    CKEDITOR.on('dialogDefinition', function(evt) {
      var dialogName = evt.data.name,
        dialogDefinition = evt.data.definition;

      if (dialogName != 'table' && dialogName != 'tableProperties')
        return;

      var infoTab = dialogDefinition.getContents('info');

      infoTab.remove('txtWidth');
      infoTab.remove('txtHeight');
      infoTab.remove('txtCellSpace');
      infoTab.remove('txtCellPad');
      infoTab.remove('txtBorder');

      var advTab = dialogDefinition.getContents('advanced');

      advTab.get('advCSSClasses')['default'] = 'standard-table';
    });
  }
});