(function($) {
  $('#id_content').each(function () {
      var $el = $(this);
      if (!$('body').is('.is-template')) {
        $el.ckeditor(function(){
            $el.removeAttr('required');
          }, {
                customConfig : '/docs/ckeditor_config.js'
        });
      }
  });
})(jQuery);