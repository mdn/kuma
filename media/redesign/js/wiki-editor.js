(function($) {

  // CKEditor setup method
  var $body = $('body');
  var setup = function() {
      var $appBoxes = $('.approved .boxed');
      var $tools = $('div.cke_toolbox');
      var $wikiArt = $('#cke_wikiArticle');
      var $container = $('.ckeditor-container');
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
              width: $('#cke_id_content').width() - 11
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
    var $el = $(this);
    if (!$body.is('.is-template')) {
      $el.removeAttr('required').ckeditor(setup, {
        customConfig : '/docs/ckeditor_config.js'
      });
    }
  });

})(jQuery);