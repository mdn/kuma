/*
  INITIALIZE THAT WE HAVE JAVASCRIPT
*/
document.documentElement.className += ' js';

(function($) {

  var isOldIE = $('#oldIE').length;

  /*
    Main menu
  */
  (function() {
    var $mainItems = $('#main-nav > ul > li');
    $mainItems.find('> a').mozMenu();
    $mainItems.find('.submenu').mozKeyboardNav();
  })();

  /*
    Search animation

    TODO:  What happens on mobile?
  */
  !isOldIE && (function() {
    var $nav = $('#main-nav');
    var $navItems = $nav.find('ul > li:not(:last-child)');
    var $searchWrap = $nav.find('.search-wrap');
    var $input = $searchWrap.find('input');
    var placeholder = $input.attr('placeholder');

    var timeout;
    var createExpander = function(delay, isAdd) {
      return function(e) {
        e && e.preventDefault();
        timeout && clearTimeout(timeout);
        timeout = setTimeout(function() {
          if(isAdd) {
            $navItems.fadeOut(100, function() {
              $navItems.css('display', 'none');
              $searchWrap.addClass('expanded');
              $nav.addClass('expand');
            });
          }
          else {
            $nav.removeClass('expand');
            timeout = setTimeout(function() {
              $searchWrap.removeClass('expanded');
              $navItems.fadeIn(400);
            } , 500)
          }
        }, delay);
      }
    };

    $input.
      on('focus', createExpander(200, true)).
      on('blur', createExpander(600));

    $nav.find('.search-trigger').on('focus click mouseenter', function() {
      // Adding timeout so the element isn't too responsive
      setTimeout(function() {
        $input.css('display', ''); 
        createExpander(200, true)();
        $input.get(0).select();
      }, 100);
    });
  })();

  /*
    Togglers within articles (i.e.)
  */
  $('.toggleable').mozTogglers();

  /*
    Persona Login
  */
  $('.persona-login').click(function(e) {
    if(!$(this).hasClass('toggle')) {
      navigator.id.get(function(assertion) {
        if(!assertion) return;
        $('input[name="assertion"]').val(assertion.toString());
        $('form.browserid').first().submit();
      });
      return false;
    }
  });

})(jQuery);