'use strict';

CKEDITOR.config.mdnFormat_formats = [
    {
        tag: 'code',
        title: 'Inline Code',
        key: CKEDITOR.CTRL + 79,
        icon: 'mdn-format-code'
    },
    {
        tag: 'kbd',
        title: 'Keystroke or User-entered Text',
        key: CKEDITOR.CTRL + CKEDITOR.ALT + 79,
        icon: 'mdn-format-kbd'
    },
    {
        tag: 'h2',
        title: 'Heading Level 2',
        key: CKEDITOR.CTRL + 50,
        icon: 'mdn-format-h2'
    },
    {
        tag: 'h3',
        title: 'Heading Level 3',
        key: CKEDITOR.CTRL + 51,
        icon: 'mdn-format-h3'
    },
    {
        tag: 'h4',
        title: 'Heading Level 4',
        key: CKEDITOR.CTRL + 52,
        icon: 'mdn-format-h4'
    },
    {
        tag: 'h5',
        title: 'Heading Level 5',
        key: CKEDITOR.CTRL + 53,
        icon: 'mdn-format-h5'
    },
    {
        tag: 'pre',
        title: 'Preformatted Text',
        key: CKEDITOR.CTRL + 80,
        icon: 'mdn-format-pre'
    }
];

CKEDITOR.plugins.add('mdn-format', {
  init: function(editor) {
    var formats = editor.config.mdnFormat_formats,
      inlineStyleOrder = 100,
      blockStyleOrder = 100;

    // If there aren't any formats to install, abort now.

    if (!formats || !formats.length) {
        return;
    }

    // Iterate over the formats list and build each command and its button.

    formats.forEach(function(format) {
      var commandName = 'mdn-format-' + format.tag,
        style = new CKEDITOR.style({ element: format.tag });

      // Workaround http://dev.ckeditor.com/ticket/10190.
      style._.enterMode = editor.enterMode;

      // Create the command that can be used to apply the style.
      editor.addCommand(commandName, new CKEDITOR.styleCommand(style));

      // Add the keystroke, if one is specified.

      if (format.key) {
          editor.setKeystroke(format.key, commandName);
      }

      // Listen to contextual style activation.
      editor.attachStyleStateChange(style, function(state) {
        !editor.readOnly && editor.getCommand(commandName).setState(state);
      });

      // Register the button if the button plugin is loaded.
      if (editor.ui.addButton) {
        var fullLabel = format.title;

        // If there's a key shortcut, we want to add that to the label.

        if (format.key) {
            var modifiers = "";

            if (format.key & CKEDITOR.ALT) {
                modifiers += "Alt-";
            }
            if (format.key & CKEDITOR.CTRL) {
                modifiers += "Ctrl-";
            }
            if (format.key & CKEDITOR.SHIFT) {
                modifiers += "Shift-";
            }

            if (modifiers.length) {
                fullLabel += " (" + modifiers + String.fromCharCode(format.key & 0xffff) + ")";
            }
        }

        editor.ui.addButton('MdnFormat' + CKEDITOR.tools.capitalize(format.tag), {
          icon: format.icon,
          label: fullLabel,
          command: commandName,
          // Place block styles buttons in the blocks group and
          // inline styles buttons in the basicstyles group.
          toolbar: CKEDITOR.dtd.$inline[format.tag] ?
            'basicstyles,' + (inlineStyleOrder += 10) :
            'blocks,' + (blockStyleOrder += 10)
        });
      }
    });
  }
});
