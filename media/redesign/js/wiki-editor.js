(function($) {

  // CKEditor setup method
  var setup = function() {
      var $appBoxes = $('.approved .boxed');
      var $tools = $('div.cke_toolbox');
      var $wikiArt = $('#cke_wikiArticle');
      var $container = $('.ckeditor-container');
      var $content = $('#cke_id_content');
      var contentTop = $container.offset().top;
      var fixed = false;

      // Switch header and toolbar styles on scroll to keep them on screen
      $(document).scroll(function() {

        // If top of the window is betwen top of #content and top of metadata (first .page-meta) blocks, the header is fixed
        var scrollTop = $(this).scrollTop();
        if (scrollTop >= contentTop) {

          // Need to display or hide the toolbar depending on scroll position
           if(scrollTop > $container.height() + contentTop - 200 /* offset to ensure toolbar doesn't reach content bottom */) {
            $tools.css('display', 'none');
            return; // Cut off at some point
           }
           else {
            $tools.css('display', '');
           }

           // Fixed position toolbar if scrolled down to the editor
           // Wrapped in IF to cut down on processing
          if (!fixed) {
            fixed = true;
            $tools.css({
              position: 'fixed',
              top: 0,
              width: $content.width() - 11
            });
          }

        } else { // If not, header is relative, put it back
          if (fixed) {
            fixed = false;
            $tools.css({
              position: 'relative',
              top: 'auto',
              width: 'auto'
            });
          }
        }

        // remove the id_content required attribute
        $('#id_content').removeAttr('required');
      });

      $(window).resize(function() { // Recalculate box width on resize
        if (fixed) {
          $tools.css({
            width: $wikiArt.width() - 10
          }); // Readjust toolbox to fit
        }
      });
   };

  // Renders the WYSIWYG editor
  $('#id_content').each(function () {
    if (!$('body').is('.is-template')) {
      $(this).removeAttr('required').ckeditor(setup, {
        customConfig : '/en-US/docs/ckeditor_config.js'
      });
    }
  });

  /* 
    Plugin for prepopulating the slug fields
  */
  $.fn.prepopulate = function(dependencies, maxLength) {
      var _changed = '_changed';

      return this.each(function() {
          var $field = $(this);

          $field.data(_changed, false);
          $field.on(_changed, function() {
              $field.data(_changed, true);
          });

          var populate = function () {
              // Bail if the fields value has changed
              if ($field.data(_changed) == true) return;

              var values = [], field_val, field_val_raw, split;
              dependencies.each(function() {
                  if ($(this).val().length > 0) {
                      values.push($(this).val());
                  }
              });

              s = values.join(' ');
              
              s = $.slugifyString(s);

              // Trim to first num_chars chars
              s = s.substring(0, maxLength);

              // Only replace the last piece (don't replace slug heirarchy)
              split = $field.val().split('/');
              split[split.length - 1] = s;
              $field.val(split.join('/'));
          };
          
          dependencies.on('keyup change focus', populate);
      });
  };

})(jQuery);