(function($) {

  /*
    Create the settings and languages menu
  */
  (function() {
    var $menus = $('#settings-menu, #languages-menu');
    $menus.mozMenu();
    $menus.parent().find('.submenu').mozKeyboardNav();
  })();

  /*
    Set up the "from search" buttons if user came from search
  */
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
    // Set up the quick links for the toggler
    var $quickLinks = $('#quick-links');
    setupTogglers($quickLinks.find('> ul > li, > ol > li'));
    $quickLinks.find('.toggleable').mozTogglers();
    
    var side = $('#quick-links-toggle').closest('.wiki-column').attr('id');
    var $columnContainer = $('#wiki-column-container');
    var $quickLinksControl = $('#wiki-controls .quick-links');

    // Quick Link toggles
    $('#quick-links-toggle, #show-quick-links').on('click', function(e) {
      var $side = $('#' + side);

      e.preventDefault();
      $side.toggleClass('column-closed');
      $columnContainer.toggleClass(side + '-closed');
      $quickLinksControl.toggleClass('hidden');

      if($side.hasClass('column-closed')) {
        $(window).trigger('resize');
      }
    });
  })();
  
  /*
    Set up the zone subnav accordion
  */
  $('.zone-subnav-container').each(function() {
    var $subnavList = $(this).find('.subnav > ol');
    if(!$subnavList.length) return; // Exit if the subnav isn't set up properly
    
    // Set the list items as togglers where needed
    setupTogglers($subnavList.find('li'));
    
    // Make them toggleable!
    $subnavList.find('.toggleable').mozTogglers();
    
    // Try to find the current page in the list, if found, open it
    var $selected = $subnavList.find('a[href$="' + document.location.pathname + '"]');
    $selected.each(function() {
      $(this).parents('.toggleable').find('.toggler').trigger('click');
    }).parent().addClass('current');
    
    // Mark this is an accordion so the togglers open/close properly
    $subnavList.addClass('accordion');
  });

  /*
    Subscribe / unsubscribe to an article
  */
  $('.page-watch a').on('click', function(e) {
    e.preventDefault();
    $(this).closest('form').submit();
  });
  
  // Utility method for the togglers
  function setupTogglers($elements) {
    $elements.each(function() {
      var $li = $(this);
      var $sublist = $li.find('> ul, > ol');
      
      if($sublist.length) {
        $li.addClass('toggleable closed');
        $li.find('> a').addClass('toggler').prepend('<i class="icon-caret-up"></i>');
        $sublist.addClass('toggle-container');
      }
    });
  }
  
  /*
    Set up the scrolling TOC effect
  */
  (function() {
    var $toc = $('#toc');
    if($toc.length) {
      var tocOffset = $toc.offset().top;
      var $toggler = $toc.find('> .toggler');
      var fixedClass = 'fixed';
      var $wikiRight = $('#wiki-right');
      
      var resizeFn = debounce(function(e) {
        // Set forth the pinned or static positioning of the table of contents
        var scroll = window.scrollY;
        var maxHeight = window.innerHeight - parseInt($toc.css('padding-top'), 10) - parseInt($toc.css('padding-bottom'), 10);
        
        if(scroll > tocOffset && $toggler.css('pointer-events') == 'none') {
          $toc.css({
            width: $toc.css('width'),
            maxHeight: maxHeight
          });
          
          if(!$toc.hasClass(fixedClass)){
            $toc.addClass(fixedClass);
          }
        }
        else {
          $toc.css({
            width: 'auto',
            maxHeight: 'none'
          });
          $toc.removeClass(fixedClass);
        }
        
        // Should the TOC be one-column (auto-closed) or sidebar'd
        if(!e || e.type == 'resize') {
          if($toggler.css('pointer-events') == 'auto'  || $toggler.find('i').css('display') != 'none') { /* icon check is for old IEs that don't support pointer-events */
            if(!$toc.attr('data-closed')) {
              $toggler.trigger('click');
            }
          }
          else if($toc.attr('data-closed')) { // Changes width, should be opened (i.e. mobile to desktop width)
            $toggler.trigger('click');
          }
        }
      }, 10);
      
      // Set it forth!
      resizeFn();
      $(window).on('scroll resize', resizeFn);
    }
  })();
  
  function debounce(func, wait, immediate) {
    var timeout;
    return function() {
      var context = this, args = arguments;
      var later = function() {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
  };
  
})(jQuery);