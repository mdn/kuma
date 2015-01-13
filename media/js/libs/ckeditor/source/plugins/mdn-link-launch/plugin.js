'use strict';

CKEDITOR.plugins.add('mdn-link-launch', {
  requires: 'link',

  init: function(editor) {
    editor.addCommand('launchLink', new CKEDITOR.launchCommand());

    if ( editor.addMenuItems ) {
      editor.addMenuItems({
        launchLink: {
          label: gettext('Launch'),
          command: 'launchLink',
          group: 'link',
          order: 6
        }
      });
    }

    if ( editor.contextMenu ) {
      editor.contextMenu.addListener( function( element, selection ) {
        if ( !element || element.isReadOnly() )
          return null;

        if ( !CKEDITOR.plugins.link.tryRestoreFakeAnchor( editor, element ) &&
          !CKEDITOR.plugins.link.getSelectedLink( editor ) )
          return null;

        return {
          launchLink: CKEDITOR.TRISTATE_OFF
        };
      });
    }
  }
});

CKEDITOR.launchCommand = function() {};
CKEDITOR.launchCommand.prototype = {
  exec: function(editor) {
    var link = CKEDITOR.plugins.link.getSelectedLink(editor);

    if(link && link.$) {
      window.open(link.$.href);
    }
  }
};