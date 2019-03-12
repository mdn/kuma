'use strict';

(function() {

  CKEDITOR.plugins.add('mdn-sticky-toolbar', {
    init: function(editor) {
      var relativeContainer,
        floatingContainer,
        topSpace,
        bottomSpace,
        topSpacePlaceholder,
        bottomSpacePlaceholder,
        fixed = false,
        loaded = false,
        relativeContainerWidth,
        relativeContainerHeight,
        window = CKEDITOR.document.getWindow();

      CKEDITOR.document.on('scroll', checkScroll);

      editor.on('loaded', function() {
        topSpace = editor.ui.space('top');
        bottomSpace = editor.ui.space('bottom');
        relativeContainer = new CKEDITOR.dom.element('div');
        floatingContainer = new CKEDITOR.dom.element('div');
        topSpacePlaceholder = new CKEDITOR.dom.element('span');
        bottomSpacePlaceholder = new CKEDITOR.dom.element('span');

        topSpacePlaceholder.setStyle('display', 'none');
        bottomSpacePlaceholder.setStyle('display', 'none');

        // Insert the outer <div> before editor's main element.
        relativeContainer.insertBefore(editor.container);
        relativeContainer.append(floatingContainer);

        moveSpacesToFloatingContainer();

        relativeContainerWidth = relativeContainer.getSize('width');
        relativeContainerHeight = relativeContainer.getSize('height');
        // Copy width, so when floatingContainer gets position:fixed it won't lose
        // its width.
        floatingContainer.setStyle('width', relativeContainerWidth + 'px');
        // Set the height, so when floatingContainer gets position:fixed relativeContainer
        // keeps the same height.
        relativeContainer.setStyle('height', relativeContainerHeight + 'px');

        loaded = true;

        // Check initial scroll (on CTRL+R/back browsers remember scroll position).
        setTimeout(function() {
          checkScroll();
        }, 500); // I'm too lazy to sync it with window#load.
      }, null, null, 999); // Execute after creators/themedui's listener.

      // Undo the DOM changes when maximizing editor and do again when leaving maximized state.
      editor.on('beforeCommandExec', function(evt) {
        if (evt.data.name != 'maximize')
          return;

        if (evt.data.command.state == CKEDITOR.TRISTATE_OFF) {
          moveSpacesToEditorContainer();
        } else {
          moveSpacesToFloatingContainer();
        }
      });

      function checkScroll() {
        if (!loaded)
          return;

        var scrollPos = window.getScrollPosition().y,
          containerPos = relativeContainer.getDocumentPosition().y,
          editorClientRect = editor.container.getClientRect();

        // If top of the toolbar container isn't visible && bottom of the editor area
        // is still visible, make the toolbar fixed.
        if ((scrollPos > containerPos) && (editorClientRect.bottom > relativeContainerHeight)) {
          if (fixed)
            return;

          fixed = true;

          floatingContainer.setStyles({
            position: 'fixed',
            top: 0
          });
        } else {
          if (!fixed)
            return;

          fixed = false;

          floatingContainer.setStyles({
            position: 'relative'
          });
        }
      }

      function moveSpacesToFloatingContainer() {
        // Replace spaces with placeholders, so we can revert that before editor is maximized.
        topSpacePlaceholder.replace(topSpace);
        bottomSpacePlaceholder.replace(bottomSpace);
        // Move top and botom UI spaces to the floating container.
        floatingContainer.append(topSpace);
        floatingContainer.append(bottomSpace);

        // Small UI tweaks.
        bottomSpace.setStyle('border-top', null);
        floatingContainer.setStyle('border', '1px solid #B6B6B6');
      }

      function moveSpacesToEditorContainer() {
        topSpace.replace(topSpacePlaceholder);
        bottomSpace.replace(bottomSpacePlaceholder);

        // Undo the UI tweaks.
        bottomSpace.removeStyle('border-top');
        floatingContainer.removeStyle('border');
      }
    }
  });
})();