(function($) {

  // Callback functions after CKE is ready
  var setup_ckeditor = function() {

    var $appBoxes = $('.approved .boxed'),
      $head = $('#article-head'),
      $transdesc = $('#trans-description'),
      $transcont = $('#content-fields'),
      $tools = $('div.cke_toolbox'),
      $wikiArt = $('#cke_wikiArticle'),
      contentTop = $('#content').offset(),
      transTop = $transcont.offset(),
      headHeight = $head.height(),
      toolHeight = $tools.height(),
      contentBottom = $('.page-meta').first().offset().top - 300,
      fixed = false;

    $('#content-fields .approved .boxed').css({
      paddingTop: toolHeight + 50
    });

    // Switch header and toolbar styles on scroll to keep them on screen
    $(document).scroll(function() {
      if ($(this).scrollTop() >= contentTop.top && $(this).scrollTop() < contentBottom) { // If top of the window is betwen top of #content and top of metadata (first .page-meta) blocks, the header is fixed
        if (!fixed) {
          fixed = true;
          $head.css({
            position: 'fixed',
            top: 19,
            width: '95%'
          });
          $tools.css({
            position: 'fixed',
            top: headHeight + 28,
            width: $('#cke_id_content').width() - 11
          });
          $('#cke_id_content').css({
            marginTop: headHeight
          });
          $('.approved header').hide();
          $('.localized header').hide();
          $('#content-fields .approved .boxed').css({
            paddingTop: toolHeight - 40
          });
        }
      } else { // If not, header is relative
        if (fixed) {
          fixed = false;
          $head.css({
            position: 'relative',
            top: 'auto',
            width: 'auto'
          });
          $tools.css({
            position: 'relative',
            top: 'auto',
            width: 'auto'
          });
          $('#cke_id_content').css({
            marginTop: 0
          });
          $('.approved header').show();
          $('.localized header').show();
          $('#content-fields .approved .boxed').css({
            paddingTop: toolHeight + 50
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

  $('#id_content').each(function() {
    if (!$('body').is('.edit.is-template')) {
      $(this).ckeditor(setup_ckeditor, {
        customConfig: '/docs/ckeditor_config.js'
      });
    }
  });

})(jQuery);