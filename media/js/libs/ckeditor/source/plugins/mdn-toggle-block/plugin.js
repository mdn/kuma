'use strict';

CKEDITOR.plugins.add('mdn-toggle-block', {
  init: function(editor) {

    // Toggles block in following order:
    // * normal block (e.g. paragraph or heading)
    // * numbered list
    // * bulleted list
    //
    // If we're in sublist it only toggles between numbered and bulleted lists.
    editor.addCommand('mdn-toggle-block', {
      exec: function(editor) {
        var commandName;

        if(getState(editor, 'numberedlist') == CKEDITOR.TRISTATE_ON) {
          commandName = 'bulletedlist';
        } else if(getState(editor, 'bulletedlist') == CKEDITOR.TRISTATE_ON) {
          // Check if we're in sub list - in such case don't execute "bulletedlist"
          // again to escape it, but instead switch to numbered list.
          commandName = inSubList(editor) ? 'numberedlist' : 'bulletedlist';
        } else {
          commandName = 'numberedlist';
        }

        editor.execCommand(commandName);
      }
    });

    function getState(editor, command) {
      return editor.getCommand(command).state;
    }

    // Checks if selection is placed in a sub list.
    function inSubList(editor) {
      var path = editor.elementPath(),
        // Create sub path between first <li> and block limit (unsplittable block).
        // This way we're not checking lists beyond the limit we can modify.
        subPath = new CKEDITOR.dom.elementPath(path.contains('li'),path.blockLimit),
        elements = subPath.elements,
        listsCount = 0;

      for(var i = 0; i < elements.length; ++i) {
        if(elements[i].is({ ul: 1, ol: 1 }))
          listsCount++;

        if (listsCount > 1)
          return true;
      }
      return false;
    }
  }
});