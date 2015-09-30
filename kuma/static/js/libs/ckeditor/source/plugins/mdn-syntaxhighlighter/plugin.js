'use strict';

CKEDITOR.config.mdnSyntaxhighlighter_brushes = [
  { name: 'Bash', brush: 'bash' },
  { name: 'C/C++', brush: 'cpp' },
  { name: 'CSS', brush: 'css' },
  { name: 'HTML', brush: 'html' },
  { name: 'Java', brush: 'java' },
  { name: 'JavaScript', brush: 'js' },
  { name: 'JSON', brush: 'json' },
  { name: 'PHP', brush: 'php' },
  { name: 'Python', brush: 'python' },
  { name: 'SQL', brush: 'sql' },
  { name: 'XML', brush: 'xml' }
];

CKEDITOR.plugins.add('mdn-syntaxhighlighter', {
  requires: 'menubutton,mdn-format',
  icons: 'mdn-syntaxhighlighter-moono', // %REMOVE_LINE_%CORE

  init: function(editor) {
    var plugin = this,
      supportedBrushes = editor.config.mdnSyntaxhighlighter_brushes,
      label = gettext('Syntax Highlighter'),
      items = {},
      i, brush;

    // Create menu items.
    items.none = {
      label: gettext('No Highlight'),
      group: 'mdn-syntaxhighlighter',
      order: 0,
      onClick: function() {
        editor.execCommand('mdn-syntaxhighlighter', 'none');
      }
    };

    supportedBrushes.forEach(function(brush, i) {
      items[brush.brush] = {
        label: brush.name,
        brushId: brush.brush,
        group: 'mdn-syntaxhighlighter',
        order: i + 1,
        onClick: function() {
          editor.execCommand('mdn-syntaxhighlighter', this.brushId);
        }
      };
    });

    // Register menu items.
    editor.addMenuGroup('mdn-syntaxhighlighter', 1);
    editor.addMenuItems(items);

    // Register command.
    editor.addCommand('mdn-syntaxhighlighter', {
      contextSensitive: true,

      exec: function(editor, brushId) {
        var item = items[brushId],
          pre = editor.elementPath().contains('pre');

        if(!item) return;

        // Not in a <pre>. Try to create it and continue.
        if(!pre) {
          editor.execCommand('mdn-format-pre');
          pre = editor.elementPath().contains('pre');
          // Pre couldn't be created in currect context - abort.
          if(!pre) return;
        }

        pre.$.className = brushId == 'none' ? '' : 'brush: ' + brushId;

        // Refresh, because class change is not a context change,
        // so refresh will not be called automatically.
        this.refresh(editor, editor.elementPath());
      },

      refresh: function(editor, path) {
        // Set state to on when in <pre> which has some brush applied.
        this.setState( plugin.getBrushId(path) != 'none' ?
          CKEDITOR.TRISTATE_ON : CKEDITOR.TRISTATE_OFF );
      }
    } );

    // Register menu button.
    editor.ui.add( 'MdnSyntaxhighlighter', CKEDITOR.UI_MENUBUTTON, {
      icon: 'mdn-syntaxhighlighter-moono',
      label: label,
      toolbar: 'blocks,200',
      command: 'mdn-syntaxhighlighter',
      onMenu: function() {
        var activeItems = {},
          currentBrushId = plugin.getBrushId(editor.elementPath());

        for(var brushId in items) {
          activeItems[brushId] = currentBrushId == brushId ? CKEDITOR.TRISTATE_ON : CKEDITOR.TRISTATE_OFF;
        }

        return activeItems;
      }
    } );
  },

  // Gets brush id from the currently selected <pre> element
  // by parsing <pre>'s class names. Returns 'none' if selection isn't
  // located in any <pre> element or <pre> hasn't got any brush applied.
  getBrushId: function(path) {
    var pre = path.contains('pre');

    // Selection isn't inside <pre> element.
    if(!pre) return 'none';

    var brushId = 'none',
      className = pre.$.className,
      brushMatch, split;

    if(className) {
      brushMatch = className.match(/brush\:(.*?);?$/);
      if(brushMatch != null) {
        split = brushMatch[1].split(';');
        brushId = split[0].replace(/^\s+|\s+$/g, '');
      }
    }

    return brushId;
  }
});