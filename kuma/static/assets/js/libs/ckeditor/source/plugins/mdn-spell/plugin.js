'use strict';

(function() {
  CKEDITOR.plugins.add('mdn-spell', {
    icons: 'mdn-spell', // %REMOVE_LINE_%CORE

    init: function(editor) {
      var lang = editor.lang;
      editor.addCommand('mdn-spell', {
        exec: function() {
          var button = this;

          // We want to apply the reverse of button.state, since it's a toggle...
          applyState(reverseState(button.state));
          // ... and change the UI.
          button.toggleState();
        },
        state: initState(),
        canUndo: false
      });

      editor.ui.addButton('MdnSpell', {
        label: lang.native_spell_check,
        command: 'mdn-spell',
        icon: 'mdn-spell'
      });
    }
  });

  // get state from cookie (or default) and apply it
  function initState() {
    // state is 1 (on) if disable_native_spell == false; our default setting
    var state = 1;

    // we'll set this cookie anytime we set the native spellcheck setting
    var saved_state = document.cookie.replace(/(?:(?:^|.*;\s*)disable_native_spell\s*\=\s*([^;]*).*$)|^.*$/, "$1");

    // state is 2 (off) if disable_native_spell == true
    if (typeof(saved_state) != undefined && saved_state == 'true') state = 2;

    // it appears the instance isn't ready at this point, so listen
    CKEDITOR.on('instanceReady', function() {
      applyState(state);
    });

    return state;
  }

  // sometimes we need the opposite state
  function reverseState(state) {
    if (state == 1) return 2;
    return 1;
  }

  // sometimes we need to translate state into setting value
  function stateToSetting(state) {
    if (state == 2) return true;
    return false;
  }

  // apply a new_state: 1 (native spell checking on) or 2 (off)
  function applyState(new_state) {
    var editor = CKEDITOR.instances.id_content;

    // if we enable native spellchecker, disable other spell checkers
    var excludes = ['checkspell', 'scaytcheck'];
    for (var i=0; i<excludes.length; i++) {
      var command = editor.getCommand(excludes[i]);
      if (new_state == CKEDITOR.TRISTATE_ON) {
        command.disable();
      }
      else if (new_state == CKEDITOR.TRISTATE_OFF) {
        command.enable();
      }
    }

    // if ckeditor's setting is false, then browser spellcheck is true. and vice versa.
    editor.document.getBody().setAttribute('spellcheck', !stateToSetting(new_state));

    // TODO: enable right-click context menu for native spellchecker

    // save ckeditor's setting value in a cookie
    document.cookie = 'disable_native_spell='+stateToSetting(new_state)+';expires=Fri, 31 Dec 9999 23:59:59 GMT';
  }
})();