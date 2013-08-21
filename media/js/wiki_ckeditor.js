(function ($) {
  $('#id_content').each(function () {
      if (!$('body').is('.is-template')) {
          $(this).ckeditor(function(){}, {
              customConfig: '/docs/ckeditor_config.js'
          });
      }
  });
})(jQuery);