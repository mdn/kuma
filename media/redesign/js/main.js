/*
  INITIALIZE THAT WE HAVE JAVASCRIPT
*/
document.documentElement.className += ' js';

(function($) {

  /*
    Some quick feature testing up front
  */
  var isOldIE = $('#feature-test-old-ie').length;
  (function() {
    // This DIV will have a different z-index based on device width
    // This is changed via media queries supported via MDN
    var $div = $('<div id="feature-test-element"></div>').appendTo(document.body);
    window.mdn.features.getDeviceState = function() {
      return $div.css('z-index');
    };
  })();

  /*
    Main menu
  */
  (function() {
    var $mainItems = $('#main-nav > ul > li');
    $mainItems.find('> a').mozMenu({
      brickOnClick: function(e) {
        return e.target.tagName == 'I';
      }
    });
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
              setTimeout(function() { 
                $input.attr('placeholder', $input.attr('data-placeholder'));
                $input.val($input.attr('data-value'));
              }, 100);
            });
          }
          else {
            $nav.removeClass('expand');
            $input.attr('placeholder', '');
            $input.attr('data-value', $input.val());
            $input.val('');
            timeout = setTimeout(function() {
              $searchWrap.removeClass('expanded');
              $navItems.fadeIn(400);
            } , 500);
          }
        }, delay);
      };
    };

    $input.
      on('focus', createExpander(200, true)).
      on('blur', createExpander(600));
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

  /* Skip to search is better done with JS because it's sometimes hidden and shown */
  $('#skip-search').on('click', function(e) {
    e.preventDefault();
    $('input[name=q]').last().get(0).focus();
  });

})(jQuery);