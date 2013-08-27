(function ($) {
  // remove the id_content required attribute
  $('#id_content').each(function () {
  	  $(this).removeAttr('required');
      if (!$('body').is('.is-template')) {
          $(this).ckeditor(function(){}, {
              customConfig: '/docs/ckeditor_config.js'
          });
      }
  });
})(jQuery);