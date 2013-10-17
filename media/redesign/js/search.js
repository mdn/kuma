(function($) {
  
  var parentSelector = '.search-pane';
    $(parentSelector + ' .close').on('click', function(e) {
      e.preventDefault();
      $('#search-results-close-container').addClass('closed');
    });

    var $more = $('.search-results-more');
    $more.find('.view-all').on('click', function(e) {
      e.preventDefault();
      var hiddenClass = 'closed';
      var $parent = $(this).closest(parentSelector);
      $parent.find('.' + hiddenClass).removeClass(hiddenClass);
      $parent.find('.pager').removeClass('hidden');
      $more.removeClass('with-view-all');
    });

})(jQuery);