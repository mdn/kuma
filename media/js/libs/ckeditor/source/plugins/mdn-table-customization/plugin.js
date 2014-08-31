'use strict';

CKEDITOR.plugins.add('mdn-table-customization', {
  requires: 'table',

  init: function(editor) {
    CKEDITOR.on('dialogDefinition', function(evt) {
      var dialogName = evt.data.name,
        dialogDefinition = evt.data.definition;

      if (dialogName != 'table')
        return;

      var infoTab = dialogDefinition.getContents('info'),
        borderWidthField = infoTab.elements[0].children[0].children[4],
        tableWidthField = infoTab.elements[0].children[1].children[0].children[0],
        tableHeightField = infoTab.elements[0].children[1].children[1].children[0],
        cellSpacingField = infoTab.elements[0].children[1].children[3],
        cellPaddingField = infoTab.elements[0].children[1].children[4];

      borderWidthField.style = 'display:none';
      borderWidthField['default'] = 0;

      delete tableWidthField.setup;
      delete tableWidthField['default'];
      tableWidthField.style = 'display:none';

      tableHeightField.style = 'display:none';

      delete cellSpacingField['default'];
      cellSpacingField.style = 'display:none';

      delete cellPaddingField['default'];
      cellPaddingField.style = 'display:none';

      var advTab = dialogDefinition.getContents('advanced'),
        classesField = advTab.elements[0].children[1].children[1].children[0];

      classesField['default'] = 'standard-table';
    });
  }
});