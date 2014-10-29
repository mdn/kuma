'use strict';

CKEDITOR.config.mdnFormat_tags = ['pre', 'code', 'h2', 'h3', 'h4', 'h5'];

CKEDITOR.plugins.add('mdn-format', {
  icons: 'mdn-format-pre,mdn-format-code,mdn-format-h2,mdn-format-h3,mdn-format-h4,mdn-format-h5', // %REMOVE_LINE_%CORE

  init: function(editor) {
    var tags = editor.config.mdnFormat_tags,
      inlineStyleOrder = 100,
      blockStyleOrder = 100;

    if(!tags) return;

    tags.forEach(function(tag) {
      var commandName = 'mdn-format-' + tag,
        style = new CKEDITOR.style({ element: tag });

      // Workaround http://dev.ckeditor.com/ticket/10190.
      style._.enterMode = editor.enterMode;

      // Create the command that can be used to apply the style.
      editor.addCommand(commandName, new CKEDITOR.styleCommand(style));

      // Listen to contextual style activation.
      editor.attachStyleStateChange(style, function(state) {
        !editor.readOnly && editor.getCommand(commandName).setState(state);
      });

      // Register the button if the button plugin is loaded.
      if(editor.ui.addButton) {
        editor.ui.addButton('MdnFormat' + CKEDITOR.tools.capitalize(tag), {
          icon: 'mdn-format-' + tag,
          label: CKEDITOR.tools.capitalize(tag),
          command: commandName,
          // Place block styles buttons in the blocks group and
          // inline styles buttons in the basicstyles group.
          toolbar: CKEDITOR.dtd.$inline[tag] ?
            'basicstyles,' + (inlineStyleOrder += 10) :
            'blocks,' + (blockStyleOrder += 10)
        });
      }
    });
  }
});