(function($) {

  // Settings menu
  (function() {
    var $settingsMenu = $('#settings-menu');
    $settingsMenu.mozMenu();
    $settingsMenu.parent().find('.submenu').mozKeyboardNav();
  })();

  // New tag placeholder
  // Has to be placed in ready call because the plugin is initialized in one
  $.ready(function() {
    $('.tagit-new input').attr('placeholder', gettext('New tag...'));
  });

  // "From Search" submenu click
  (function() {
    var $fromSearchNav = $('.from-search-navigate');
    if($fromSearchNav.length) {
      var $fromSearchList = $('.from-search-toc');
      $fromSearchNav.mozMenu({
        submenu: $fromSearchList,
        brickOnClick: true
      });
      $fromSearchList.find('ol').mozKeyboardNav();
    }
  })();

  /*
    Toggle for quick links show/hide
  */
  (function() {
    var side = $('#quick-links-toggle').closest('.wiki-column').attr('id');
    // Quick Link toggles
    $('#quick-links-toggle, #show-quick-links').on('click', function(e) {
      e.preventDefault();
      $('#' + side).toggleClass('column-closed');
      $('#wiki-column-container').toggleClass(side + '-closed');
      $('#wiki-controls .quick-links').toggleClass('hidden');
    });
  })();


})(jQuery);