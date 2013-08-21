(function($) {

  // Callback functions after CKE is ready
  $('#id_content').each(function() {
    if (!$('body').is('.edit.is-template')) {
      $(this).ckeditor(function(){}, {
        customConfig: '/docs/ckeditor_config.js'
      });
    }
  });

})(jQuery);